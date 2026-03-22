"""
Сидер тестовых данных: категории, товары, FAQ, шаблоны рассылок, настройки бота (если нет).
Запуск: python manage.py seed
Шаблоны рассылок: отправка из админки или командой /broadcasts в админ-чате.
"""
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import Category, Product, ProductImage
from apps.faq.models import FAQ
from apps.bot_settings.models import BotSettings
from apps.broadcasts.models import Broadcast, BroadcastTemplate
from apps.orders.models import Order


CATEGORIES = [
    {"name": "Мёд", "slug": "med", "order": 0},
    {"name": "Продукты пасеки", "slug": "produkty-paseki", "order": 1},
    {"name": "Подарочные наборы", "slug": "podarochnye-nabory", "order": 2},
    {"name": "Свечи и косметика", "slug": "svechi-kosmetika", "order": 3},
]

PRODUCTS = [
    ("med", "Мёд липовый 500 г", "med-lipovyi-500", "Натуральный липовый мёд с пасеки. 500 г.", Decimal("450.00")),
    ("med", "Мёд гречишный 350 г", "med-grechishnyi-350", "Тёмный гречишный мёд. 350 г.", Decimal("380.00")),
    ("med", "Мёд разнотравье 1 кг", "med-raznotravie-1kg", "Мёд из разнотравья. 1 кг.", Decimal("750.00")),
    ("produkty-paseki", "Перга 100 г", "perga-100", "Перга натуральная. 100 г.", Decimal("520.00")),
    ("produkty-paseki", "Прополис настойка 30 мл", "propolis-nastoyka-30", "Настойка прополиса. 30 мл.", Decimal("290.00")),
    ("produkty-paseki", "Забрус 200 г", "zabrus-200", "Забрус пчелиный. 200 г.", Decimal("350.00")),
    ("podarochnye-nabory", "Набор «Подарок пасечника»", "nabor-podarok-pasechnika", "Мёд, перга, свеча, подарочная упаковка.", Decimal("1200.00")),
    ("podarochnye-nabory", "Набор «Медовый букет»", "nabor-medovyi-buket", "Три вида мёда в подарочной коробке.", Decimal("980.00")),
    ("svechi-kosmetika", "Свеча восковая малая", "svecha-voskovaya-malaya", "Восковая свеча ручной работы. Малая.", Decimal("150.00")),
    ("svechi-kosmetika", "Свеча восковая большая", "svecha-voskovaya-bolshaya", "Восковая свеча ручной работы. Большая.", Decimal("280.00")),
    ("svechi-kosmetika", "Крем с прополисом", "krem-s-propolisom", "Крем для кожи с прополисом. 50 мл.", Decimal("420.00")),
]

FAQ_ITEMS = [
    ("Как хранить мёд?", "Храните в тёмном прохладном месте, плотно закрытым. Не нагревайте выше 40 °C."),
    ("Как оформить доставку?", "Выберите товары в корзине, нажмите «Оформить заказ», укажите адрес и контакты. Мы согласуем время доставки."),
    ("У вас есть сертификаты?", "Да, на всю продукцию есть документы. По запросу можем выслать."),
    ("Можно ли забрать заказ самовывозом?", "Да, укажите при оформлении «самовывоз» — согласуем место и время."),
    ("Какой срок годности у мёда?", "Натуральный мёд при правильном хранении годен не менее 2 лет."),
]

# Шаблоны рассылок (имя уникально для get_or_create).
BROADCAST_TEMPLATE_SEEDS = [
    ("Тест (сидер)", "<b>Тестовая рассылка</b>\n\nПроверка админки и бота."),
    ("Акция выходного дня", "<b>Акция выходного дня</b>\n\n−10% на мёд до воскресенья. <i>Тест.</i>"),
    ("Доставка", "Напоминание: доставка по городу в день заказа при заказе до 14:00."),
]

# Фоны для тестовых фото (мёд / пасека / подарки / косметика — тёплые оттенки).
_SEED_IMAGE_PALETTE = [
    (255, 243, 205),
    (252, 211, 77),
    (254, 215, 170),
    (253, 224, 200),
    (250, 204, 133),
    (245, 230, 200),
    (255, 237, 213),
    (254, 240, 220),
    (243, 212, 160),
    (238, 200, 140),
    (255, 248, 220),
]


def _seed_placeholder_jpeg_bytes(title: str, accent: tuple[int, int, int]) -> bytes:
    w, h = 900, 600
    img = Image.new("RGB", (w, h), color=accent)
    draw = ImageDraw.Draw(img)
    stripe = (
        min(255, accent[0] + 25),
        min(255, accent[1] + 20),
        min(255, accent[2] + 15),
    )
    for x in range(0, w, 48):
        draw.line([(x, 0), (x, h)], fill=stripe, width=1)
    rim = (120, 75, 30)
    draw.rounded_rectangle([24, 24, w - 24, h - 24], radius=28, outline=rim, width=6)
    draw.rounded_rectangle([48, 48, w - 48, h - 48], radius=20, outline=rim, width=2)
    font = ImageFont.load_default()
    label = (title or "Товар")[:48]
    draw.text((w // 2, h // 2 - 6), label, fill=rim, font=font, anchor="mm")
    draw.text((w // 2, h // 2 + 14), "tg-shop seed", fill=rim, font=font, anchor="mm")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _ensure_seed_product_images(stdout, style) -> None:
    """Один JPEG на товар, если фото ещё нет (удобно и при повторном seed без --clear)."""
    products = list(Product.objects.all().order_by("id"))
    added = 0
    for i, product in enumerate(products):
        if product.images.exists():
            continue
        color = _SEED_IMAGE_PALETTE[i % len(_SEED_IMAGE_PALETTE)]
        raw = _seed_placeholder_jpeg_bytes(product.name, color)
        fname = f"seed_{product.slug}.jpg"
        img = ProductImage(product=product, order=0)
        img.image.save(fname, ContentFile(raw), save=True)
        added += 1
        stdout.write(f"  Фото (сидер): {product.name[:40]}")
    if added:
        stdout.write(style.SUCCESS(f"  Добавлено тестовых изображений: {added}"))
    elif products:
        stdout.write("  У всех товаров уже есть фото — пропуск.")


class Command(BaseCommand):
    help = (
        "Загружает тестовые данные: категории, товары, FAQ, шаблоны рассылок, "
        "настройки бота (если нет)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help=(
                "Перед загрузкой удалить заказы, категории, товары, FAQ, шаблоны и журнал рассылок "
                "(настройки бота не трогаем)."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Удаление старых данных…")
            # OrderItem ссылается на Product с PROTECT — сначала заказы.
            Order.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            FAQ.objects.all().delete()
            Broadcast.objects.all().delete()
            BroadcastTemplate.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    "Заказы, категории, товары, FAQ, шаблоны и журнал рассылок удалены."
                )
            )

        # Категории
        slug_to_category = {}
        for c in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=c["slug"],
                defaults={"name": c["name"], "order": c["order"]},
            )
            slug_to_category[c["slug"]] = cat
            if created:
                self.stdout.write(f"  Категория: {cat.name}")

        # Товары
        for cat_slug, name, slug, description, price in PRODUCTS:
            category = slug_to_category[cat_slug]
            _, created = Product.objects.get_or_create(
                category=category,
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "price": price,
                },
            )
            if created:
                self.stdout.write(f"  Товар: {name}")

        _ensure_seed_product_images(self.stdout, self.style)

        # FAQ
        for order, (question, answer) in enumerate(FAQ_ITEMS, 1):
            _, created = FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "order": order},
            )
            if created:
                self.stdout.write(f"  FAQ: {question[:50]}…")

        # Шаблоны рассылок (отправка: кнопка в админке или /broadcasts в админ-чате)
        for order, (name, text) in enumerate(BROADCAST_TEMPLATE_SEEDS, start=1):
            _, created = BroadcastTemplate.objects.get_or_create(
                name=name,
                defaults={"text": text, "order": order, "is_active": True},
            )
            if created:
                self.stdout.write(f"  Шаблон рассылки: {name}")

        # Настройки бота — один раз создать, если нет
        if not BotSettings.objects.exists():
            BotSettings.objects.create(admin_chat_id=None, admin_telegram_ids=[])
            self.stdout.write("  Настройки бота созданы (admin_chat_id и admin_telegram_ids задайте в админке).")

        self.stdout.write(self.style.SUCCESS("Сидер выполнен."))
