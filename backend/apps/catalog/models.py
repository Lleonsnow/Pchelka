from django.db import models


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "catalog_category"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_product"
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]
        unique_together = [("category", "slug")]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/%Y/%m/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "catalog_productimage"
        verbose_name = "Фото товара"
        verbose_name_plural = "Фото товаров"
        ordering = ["order"]
