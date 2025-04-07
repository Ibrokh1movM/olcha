import os
import django
from faker import Faker
import random
from django.utils.text import slugify

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from shop.models import Category, Product, ProductImage

fake = Faker()


def create_categories():
    categories = [
        "Smartfonlar", "Noutbuklar", "Televizorlar", "Aksessuarlar", "Maishiy Texnika",
        "Kiyim", "Poyabzal", "Sport Anjomlari", "Kitoblar", "O'yinchoqlar"
    ]
    for category_name in categories:
        base_slug = slugify(category_name)
        slug = base_slug
        counter = 1
        # Agar slug allaqachon mavjud bo‘lsa, noyob slug yaratamiz
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slug}
        )


def create_products(num_products=2000):
    categories = Category.objects.all()
    for _ in range(num_products):
        category = random.choice(categories)
        name = fake.word().capitalize() + " " + fake.word().capitalize()
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        # Mahsulotlar uchun ham noyob slug yaratamiz
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        product = Product.objects.create(
            name=name,
            slug=slug,
            category=category,
            description=fake.text(max_nb_chars=200),
            price=random.uniform(10, 1000),
            discount=random.uniform(0, 50),
            is_available=True
        )
        # Har bir mahsulot uchun tasodifiy rasm qo‘shish (agar rasm bo‘lmasa, o‘tkazib yuboring)
        ProductImage.objects.create(
            product=product,
            image='product_images/default.jpg',  # Bu joyda haqiqiy rasm yo‘lini qo‘yishingiz mumkin
            is_primary=True
        )


if __name__ == "__main__":
    print("Kategoriyalarni yaratish...")
    create_categories()
    print("Mahsulotlarni yaratish...")
    create_products(2000)
    print("2000 ta mahsulot muvaffaqiyatli qo‘shildi!")
