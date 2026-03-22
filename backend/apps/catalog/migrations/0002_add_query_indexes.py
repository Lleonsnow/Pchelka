from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["parent", "order", "name"],
                name="catalog_cat_parent_ord_nm",
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_active", "category", "-created_at"],
                name="catalog_prod_act_cat_crt",
            ),
        ),
        migrations.AddIndex(
            model_name="productimage",
            index=models.Index(
                fields=["product", "order"],
                name="catalog_pimg_prod_ord",
            ),
        ),
    ]
