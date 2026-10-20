from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Brand, Category, Phone


class Command(BaseCommand):
    help = 'Populate TechMarket with realistic demo categories, brands, and products.'

    def handle(self, *args, **options):
        categories = {
            'Smartphones': ('Flagship and everyday smartphones.', 'Phones', 'shop/img/phone.svg'),
            'Tablets': ('Portable screens for work, study, and streaming.', 'Tablets', 'shop/img/tablet.svg'),
            'Smart Watches': ('Wearables for health, fitness, and notifications.', 'Watches', 'shop/img/watch.svg'),
            'Earbuds': ('Wireless audio for calls, music, and travel.', 'Audio', 'shop/img/earbuds.svg'),
            'Accessories': ('Chargers, cases, keyboards, and useful add-ons.', 'Gear', 'shop/img/accessory.svg'),
        }
        category_objs = {
            name: Category.objects.update_or_create(
                name=name,
                defaults={'description': description, 'icon': icon},
            )[0]
            for name, (description, icon, image) in categories.items()
        }

        brand_countries = {
            'Apple': 'USA', 'Samsung': 'South Korea', 'Google': 'USA', 'Nothing': 'United Kingdom',
            'Xiaomi': 'China', 'OnePlus': 'China', 'Sony': 'Japan', 'Huawei': 'China',
            'Realme': 'China', 'Honor': 'China',
        }
        brand_objs = {
            name: Brand.objects.update_or_create(name=name, defaults={'country': country})[0]
            for name, country in brand_countries.items()
        }

        products = [
            ('Apple', 'Smartphones', 'iPhone 15 Pro', 999, 1099, 256, 4.9, 16, 124),
            ('Apple', 'Smartphones', 'iPhone 15', 799, 899, 128, 4.8, 22, 152),
            ('Samsung', 'Smartphones', 'Galaxy S24 Ultra', 1199, 1299, 256, 4.9, 18, 141),
            ('Samsung', 'Smartphones', 'Galaxy S24', 859, 949, 128, 4.7, 24, 118),
            ('Google', 'Smartphones', 'Pixel 8 Pro', 999, 1099, 256, 4.8, 13, 83),
            ('Google', 'Smartphones', 'Pixel 8a', 499, 549, 128, 4.6, 21, 96),
            ('Nothing', 'Smartphones', 'Phone (2)', 599, 699, 256, 4.6, 10, 77),
            ('Xiaomi', 'Smartphones', '14 Ultra', 999, 1099, 512, 4.8, 9, 68),
            ('OnePlus', 'Smartphones', '12', 799, 899, 256, 4.7, 15, 89),
            ('Sony', 'Smartphones', 'Xperia 1 VI', 1299, 1399, 256, 4.5, 7, 38),
            ('Huawei', 'Smartphones', 'Pura 70 Pro', 999, 1099, 512, 4.6, 8, 42),
            ('Realme', 'Smartphones', 'GT 6', 649, 729, 256, 4.5, 17, 61),
            ('Honor', 'Smartphones', 'Magic6 Pro', 1099, 1199, 512, 4.7, 12, 58),
            ('Apple', 'Tablets', 'iPad Pro 11-inch M4', 999, 1099, 256, 4.9, 11, 78),
            ('Apple', 'Tablets', 'iPad Air 13-inch M2', 799, 899, 128, 4.8, 14, 64),
            ('Samsung', 'Tablets', 'Galaxy Tab S9 Ultra', 1199, 1299, 256, 4.7, 8, 53),
            ('Samsung', 'Tablets', 'Galaxy Tab S9 FE', 449, 529, 128, 4.5, 19, 72),
            ('Xiaomi', 'Tablets', 'Pad 6S Pro', 699, 799, 256, 4.6, 10, 47),
            ('Huawei', 'Tablets', 'MatePad Pro 13.2', 899, 999, 256, 4.5, 6, 35),
            ('Honor', 'Tablets', 'Pad 9', 329, 399, 128, 4.4, 18, 46),
            ('Apple', 'Smart Watches', 'Apple Watch Series 9', 399, 449, 64, 4.8, 25, 166),
            ('Apple', 'Smart Watches', 'Apple Watch Ultra 2', 799, 849, 64, 4.9, 12, 94),
            ('Samsung', 'Smart Watches', 'Galaxy Watch6 Classic', 399, 449, 32, 4.6, 18, 88),
            ('Google', 'Smart Watches', 'Pixel Watch 2', 349, 399, 32, 4.5, 13, 51),
            ('Huawei', 'Smart Watches', 'Watch GT 4', 249, 299, 32, 4.5, 20, 69),
            ('Xiaomi', 'Smart Watches', 'Watch 2 Pro', 269, 329, 32, 4.4, 15, 43),
            ('Apple', 'Earbuds', 'AirPods Pro 2', 249, 279, 8, 4.9, 36, 210),
            ('Apple', 'Earbuds', 'AirPods 3', 169, 199, 8, 4.6, 34, 174),
            ('Samsung', 'Earbuds', 'Galaxy Buds3 Pro', 249, 279, 8, 4.7, 28, 116),
            ('Google', 'Earbuds', 'Pixel Buds Pro', 199, 229, 8, 4.5, 24, 75),
            ('Sony', 'Earbuds', 'WF-1000XM5', 299, 329, 8, 4.8, 17, 103),
            ('Nothing', 'Earbuds', 'Ear (2)', 149, 179, 8, 4.4, 21, 67),
            ('Apple', 'Accessories', 'MagSafe Charger', 39, 49, 0, 4.7, 40, 230),
            ('Apple', 'Accessories', 'Magic Keyboard for iPad Pro', 299, 349, 0, 4.6, 11, 48),
            ('Samsung', 'Accessories', '45W USB-C Charger', 49, 59, 0, 4.5, 38, 127),
            ('Samsung', 'Accessories', 'SmartTag2', 29, 39, 0, 4.4, 45, 96),
            ('Google', 'Accessories', 'Pixel Stand 2', 79, 89, 0, 4.3, 14, 39),
            ('Xiaomi', 'Accessories', '120W HyperCharge Adapter', 59, 69, 0, 4.5, 31, 74),
            ('OnePlus', 'Accessories', 'SUPERVOOC 100W Charger', 69, 79, 0, 4.6, 23, 58),
            ('Sony', 'Accessories', 'WH-1000XM5 Headphones', 399, 449, 0, 4.9, 15, 122),
        ]

        image_by_category = {name: image for name, (_, _, image) in categories.items()}
        for brand, category, name, price, old_price, memory, rating, stock, sold in products:
            Phone.objects.update_or_create(
                brand=brand_objs[brand],
                category=category_objs[category],
                name=name,
                defaults={
                    'price': Decimal(str(price)),
                    'old_price': Decimal(str(old_price)),
                    'memory_gb': memory,
                    'description': f'{name} combines premium hardware, refined design, and dependable everyday performance.',
                    'short_description': f'Premium {category.lower()} option from {brand} with polished performance.',
                    'specifications': f'Brand: {brand}\nCategory: {category}\nMemory: {memory} GB\nWarranty: 12 months\nConnectivity: USB-C / wireless',
                    'image': image_by_category[category],
                    'rating': Decimal(str(rating)),
                    'stock': stock,
                    'sold_count': sold,
                    'in_stock': stock > 0,
                },
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(products)} products across {len(categories)} categories.'))
