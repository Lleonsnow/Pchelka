from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "order")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
