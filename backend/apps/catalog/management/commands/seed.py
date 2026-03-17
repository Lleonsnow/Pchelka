"""
Сидер тестовых данных: категории, товары, FAQ, настройки бота (если нет).
Запуск: python manage.py seed
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product
from apps.faq.models import FAQ
from apps.bot_settings.models import BotSettings


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


class Command(BaseCommand):
    help = "Загружает тестовые данные: категории, товары, FAQ, настройки бота (если нет)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Перед загрузкой удалить существующие категории, товары и FAQ (настройки бота не трогаем).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Удаление старых данных…")
            Product.objects.all().delete()
            Category.objects.all().delete()
            FAQ.objects.all().delete()
            self.stdout.write(self.style.WARNING("Категории, товары и FAQ удалены."))

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

        # FAQ
        for order, (question, answer) in enumerate(FAQ_ITEMS, 1):
            _, created = FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "order": order},
            )
            if created:
                self.stdout.write(f"  FAQ: {question[:50]}…")

        # Настройки бота — один раз создать, если нет
        if not BotSettings.objects.exists():
            BotSettings.objects.create(admin_chat_id=None, admin_telegram_ids=[])
            self.stdout.write("  Настройки бота созданы (admin_chat_id и admin_telegram_ids задайте в админке).")

        self.stdout.write(self.style.SUCCESS("Сидер выполнен."))
