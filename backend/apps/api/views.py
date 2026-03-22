from typing import Union

from django.conf import settings
from django.db.models import Count, Prefetch, Q
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product, ProductImage
from apps.faq.models import FAQ
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.orders.signals import notify_bot_admin_new_order
from apps.users.models import TelegramUser

from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    CartItemSerializer,
    CartAddSerializer,
    CartUpdateSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    FAQSerializer,
)


def _get_cart(user: TelegramUser) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user, defaults={})
    return cart


def _require_telegram_user(request: Request) -> Union[TelegramUser, Response]:
    user = request.user
    if not user or not isinstance(user, TelegramUser):
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    return user


def _cart_response_payload(cart: Cart) -> dict:
    items = cart.items.select_related("product").all()
    total = sum((item.product.price * item.quantity) for item in items)
    return {
        "items": CartItemSerializer(items, many=True).data,
        "total": str(total),
    }


class WebAppConfigView(APIView):
    """Публичный конфиг: username бота и short name Mini App (из BotFather)."""

    permission_classes = [AllowAny]

    def get(self, request: Request):
        u = (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").strip().lstrip("@")
        short = (getattr(settings, "TELEGRAM_MINIAPP_SHORT_NAME", "") or "").strip()
        return Response(
            {
                "telegram_bot_username": u,
                "miniapp_short_name": short,
            }
        )


class MeView(APIView):
    """Профиль текущего пользователя (телефон из бота после «Поделиться контактом»)."""

    def get(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
        return Response(
            {
                "phone": user.phone or "",
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
            }
        )


class FAQListView(APIView):
    """Публичный список FAQ для главной WebApp (без обязательной авторизации)."""

    permission_classes = [AllowAny]

    def get(self, request: Request):
        qs = FAQ.objects.filter(is_active=True).order_by("order", "id")
        return Response(FAQSerializer(qs, many=True).data)


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
        qs = qs.annotate(children_count=Count("children")).order_by("order", "name")
        serializer = CategorySerializer(qs, many=True)
        return Response(serializer.data)


class ProductListView(APIView):
    """Товары по категории или поиск по имени/описанию."""

    def get(self, request: Request):
        category_id = request.query_params.get("category_id")
        search = (request.query_params.get("search") or "").strip()
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("images", queryset=ProductImage.objects.order_by("order"))
            )
        )
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
    """Один товар по id (публичный GET — превью ссылок и generateMetadata в Next)."""

    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int):
        try:
            product = (
                Product.objects.filter(is_active=True)
                .prefetch_related(
                    Prefetch("images", queryset=ProductImage.objects.order_by("order"))
                )
                .get(pk=pk)
            )
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductDetailSerializer(product, context={"request": request})
        return Response(serializer.data)


class CartView(APIView):
    """GET — содержимое корзины; DELETE — очистить."""

    def get(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
        cart = _get_cart(user)
        return Response(_cart_response_payload(cart))

    def delete(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
        cart = _get_cart(user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartAddView(APIView):
    """Добавить товар в корзину (или увеличить количество)."""

    def post(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
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
        return Response(
            _cart_response_payload(cart),
            status=status.HTTP_201_CREATED,
        )


class CartUpdateView(APIView):
    """Изменить количество по product_id (или удалить при quantity=0)."""

    def patch(self, request: Request, product_id: int):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
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
        return Response(_cart_response_payload(cart))


class CartRemoveView(APIView):
    """Удалить товар из корзины."""

    def delete(self, request: Request, product_id: int):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
        cart = _get_cart(user)
        deleted, _ = cart.items.filter(product_id=product_id).delete()
        if not deleted:
            return Response({"detail": "Not in cart"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_cart_response_payload(cart))


class OrderListView(APIView):
    """Список заказов текущего пользователя."""

    def get(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
        orders = Order.objects.filter(user=user).order_by("-created_at")[:50]
        return Response(OrderListSerializer(orders, many=True).data)


class OrderCreateView(APIView):
    """Создать заказ из текущей корзины."""

    def post(self, request: Request):
        user = _require_telegram_user(request)
        if isinstance(user, Response):
            return user
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
        oid = order.id
        transaction.on_commit(lambda: notify_bot_admin_new_order(oid))
        return Response(
            {"id": order.id, "total": str(order.total), "status": order.status},
            status=status.HTTP_201_CREATED,
        )
