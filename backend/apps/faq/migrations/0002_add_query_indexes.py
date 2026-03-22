from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("faq", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="faq",
            index=models.Index(
                fields=["is_active", "order", "id"],
                name="faq_faq_active_ord_id",
            ),
        ),
    ]
