from decimal import Decimal

from django.db.models import Q
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.users.models import TelegramUser

from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    CartItemSerializer,
    CartAddSerializer,
    CartUpdateSerializer,
    OrderCreateSerializer,
)


def _get_cart(user: TelegramUser) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user, defaults={})
    return cart


class CategoryListView(APIView):
    """Список корневых категорий или дочерних по query-параметру parent_id."""

    def get(self, request: Request):
        parent_id = request.query_params.get("parent_id")
        if parent_id is None or parent_id == "":
            qs = Category.objects.filter(parent__isnull=True)
        else:
            try:
                qs = Category.objects.filter(parent_id=int(parent_id))
            except ValueError:
                qs = Category.objects.none()
        qs = qs.order_by("order", "name")
        serializer = CategorySerializer(qs, many=True)
        return Response(serializer.data)


class ProductListView(APIView):
    """Товары по категории или поиск по имени/описанию."""

    def get(self, request: Request):
        category_id = request.query_params.get("category_id")
        search = (request.query_params.get("search") or "").strip()
        qs = Product.objects.filter(is_active=True).select_related("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        qs = qs.order_by("-created_at")[:100]
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class ProductDetailView(APIView):
    """Один товар по id."""

    def get(self, request: Request, pk: int):
        try:
            product = Product.objects.prefetch_related("images").get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductDetailSerializer(product, context={"request": request})
        return Response(serializer.data)


class CartView(APIView):
    """GET — содержимое корзины; DELETE — очистить."""

    def get(self, request: Request):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        cart = _get_cart(user)
        items = cart.items.select_related("product").all()
        total = sum(
            (item.product.price * item.quantity) for item in items
        )
        data = {
            "items": CartItemSerializer(items, many=True).data,
            "total": str(total),
        }
        return Response(data)

    def delete(self, request: Request):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        cart = _get_cart(user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartAddView(APIView):
    """Добавить товар в корзину (или увеличить количество)."""

    def post(self, request: Request):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = CartAddSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        product = ser.validated_data["product_id"]
        quantity = ser.validated_data.get("quantity", 1)
        cart = _get_cart(user)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        items = cart.items.select_related("product").all()
        total = sum((i.product.price * i.quantity) for i in items)
        return Response({
            "items": CartItemSerializer(items, many=True).data,
            "total": str(total),
        }, status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    """Изменить количество по product_id (или удалить при quantity=0)."""

    def patch(self, request: Request, product_id: int):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = CartUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        quantity = ser.validated_data["quantity"]
        cart = _get_cart(user)
        item = cart.items.filter(product_id=product_id).first()
        if not item:
            return Response({"detail": "Not in cart"}, status=status.HTTP_404_NOT_FOUND)
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save(update_fields=["quantity"])
        items = cart.items.select_related("product").all()
        total = sum((i.product.price * i.quantity) for i in items)
        return Response({
            "items": CartItemSerializer(items, many=True).data,
            "total": str(total),
        })


class CartRemoveView(APIView):
    """Удалить товар из корзины."""

    def delete(self, request: Request, product_id: int):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        cart = _get_cart(user)
        deleted, _ = cart.items.filter(product_id=product_id).delete()
        if not deleted:
            return Response({"detail": "Not in cart"}, status=status.HTTP_404_NOT_FOUND)
        items = cart.items.select_related("product").all()
        total = sum((i.product.price * i.quantity) for i in items)
        return Response({
            "items": CartItemSerializer(items, many=True).data,
            "total": str(total),
        })


class OrderCreateView(APIView):
    """Создать заказ из текущей корзины."""

    def post(self, request: Request):
        user = request.user
        if not user or not isinstance(user, TelegramUser):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = OrderCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        cart = _get_cart(user)
        items = list(cart.items.select_related("product").all())
        if not items:
            return Response(
                {"detail": "Корзина пуста"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total = sum((i.product.price * i.quantity) for i in items)
        order = Order.objects.create(
            user=user,
            status=Order.Status.PAYMENT_PENDING,
            full_name=ser.validated_data["full_name"],
            address=ser.validated_data["address"],
            phone=ser.validated_data["phone"],
            total=total,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
        cart.items.all().delete()
        return Response(
            {"id": order.id, "total": str(order.total), "status": order.status},
            status=status.HTTP_201_CREATED,
        )
