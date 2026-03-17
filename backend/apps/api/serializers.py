from decimal import Decimal

from rest_framework import serializers

from apps.catalog.models import Category, Product, ProductImage
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "order", "parent", "children_count"]

    def get_children_count(self, obj):
        return obj.children.count() if obj.id else 0


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "url", "order"]

    def get_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else ""


class ProductListSerializer(serializers.ModelSerializer):
    """Краткий список для каталога."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "category", "image_url"]

    def get_image_url(self, obj):
        first = obj.images.order_by("order").first()
        if not first or not first.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(first.image.url)
        return first.image.url


class ProductDetailSerializer(serializers.ModelSerializer):
    """Детали товара с изображениями."""
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "description", "price", "category", "image_urls"]

    def get_image_urls(self, obj):
        request = self.context.get("request")
        qs = obj.images.order_by("order")
        return [
            request.build_absolute_uri(img.image.url) if request and img.image else (img.image.url or "")
            for img in qs
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source="product")
    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, source="product.price", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "product_name", "price", "quantity", "subtotal"]

    def get_subtotal(self, obj):
        return (obj.product.price * obj.quantity) if obj.product else Decimal("0")


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    address = serializers.CharField()
    phone = serializers.CharField(max_length=32)


class OrderListSerializer(serializers.ModelSerializer):
    """Краткий список заказов пользователя для профиля."""

    class Meta:
        model = Order
        fields = ["id", "status", "total", "created_at"]

    total = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
