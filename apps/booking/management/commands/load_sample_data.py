"""
Management command to load sample booking data.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.booking.models import ServiceCategory, Service, Staff

User = get_user_model()


class Command(BaseCommand):
    help = 'Load sample services and staff for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Staff.objects.all().delete()
            Service.objects.all().delete()
            ServiceCategory.objects.all().delete()
            User.objects.filter(email__endswith='@traditionallifestyle.com').delete()

        self.stdout.write('Creating service categories...')
        self.create_categories()

        self.stdout.write('Creating services...')
        self.create_services()

        self.stdout.write('Creating staff members...')
        self.create_staff()

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
        self.stdout.write('')
        self.stdout.write('Summary:')
        self.stdout.write(f'  - Categories: {ServiceCategory.objects.count()}')
        self.stdout.write(f'  - Services: {Service.objects.count()}')
        self.stdout.write(f'  - Staff: {Staff.objects.count()}')

    def create_categories(self):
        categories = [
            {'name': 'Haircuts', 'slug': 'haircuts', 'brand': 'men', 'description': 'Classic and modern haircut styles', 'order': 1},
            {'name': 'Beard & Shave', 'slug': 'beard-shave', 'brand': 'men', 'description': 'Beard grooming and traditional shaves', 'order': 2},
            {'name': 'Hair Styling', 'slug': 'hair-styling', 'brand': 'women', 'description': 'Professional hair styling services', 'order': 1},
            {'name': 'Hair Color', 'slug': 'hair-color', 'brand': 'women', 'description': 'Coloring, highlights, and treatments', 'order': 2},
        ]

        for cat_data in categories:
            obj, created = ServiceCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {obj.name}')

    def create_services(self):
        # Men's Services
        haircuts = ServiceCategory.objects.get(slug='haircuts')
        beard = ServiceCategory.objects.get(slug='beard-shave')

        men_services = [
            {
                'name': 'Classic Haircut',
                'category': haircuts,
                'brand': 'men',
                'description': 'Traditional gentleman\'s haircut with precision scissors and clippers. Includes consultation, shampoo, and styling.',
                'duration': timedelta(minutes=30),
                'price': 45.00,
                'is_featured': True,
            },
            {
                'name': 'Executive Cut & Style',
                'category': haircuts,
                'brand': 'men',
                'description': 'Premium haircut experience with hot towel treatment, scalp massage, and precision styling for the modern professional.',
                'duration': timedelta(minutes=45),
                'price': 65.00,
                'is_featured': True,
            },
            {
                'name': 'Fade & Design',
                'category': haircuts,
                'brand': 'men',
                'description': 'Sharp fade with optional hair design. Perfect for a bold, modern look.',
                'duration': timedelta(minutes=40),
                'price': 55.00,
                'is_featured': False,
            },
            {
                'name': 'Beard Trim',
                'category': beard,
                'brand': 'men',
                'description': 'Professional beard shaping and trimming with hot towel finish.',
                'duration': timedelta(minutes=20),
                'price': 25.00,
                'is_featured': False,
            },
            {
                'name': 'Traditional Hot Shave',
                'category': beard,
                'brand': 'men',
                'description': 'Luxurious straight razor shave with hot towels, pre-shave oil, and soothing aftershave balm.',
                'duration': timedelta(minutes=35),
                'price': 40.00,
                'is_featured': True,
            },
            {
                'name': 'Haircut & Beard Combo',
                'category': haircuts,
                'brand': 'men',
                'description': 'Complete grooming package: precision haircut plus full beard trim and shape.',
                'duration': timedelta(minutes=50),
                'price': 75.00,
                'sale_price': 65.00,
                'is_featured': True,
            },
        ]

        # Women's Services
        styling = ServiceCategory.objects.get(slug='hair-styling')
        color = ServiceCategory.objects.get(slug='hair-color')

        women_services = [
            {
                'name': 'Women\'s Haircut',
                'category': styling,
                'brand': 'women',
                'description': 'Personalized haircut tailored to your face shape and lifestyle. Includes consultation, shampoo, and blowdry.',
                'duration': timedelta(minutes=45),
                'price': 75.00,
                'is_featured': True,
            },
            {
                'name': 'Blowout & Style',
                'category': styling,
                'brand': 'women',
                'description': 'Professional blowdry and styling for any occasion. Long-lasting volume and shine.',
                'duration': timedelta(minutes=40),
                'price': 55.00,
                'is_featured': True,
            },
            {
                'name': 'Updo & Special Occasion',
                'category': styling,
                'brand': 'women',
                'description': 'Elegant updo styling perfect for weddings, proms, and special events.',
                'duration': timedelta(minutes=60),
                'price': 95.00,
                'is_featured': False,
            },
            {
                'name': 'Full Color',
                'category': color,
                'brand': 'women',
                'description': 'Complete single-process color application for vibrant, all-over color.',
                'duration': timedelta(minutes=90),
                'price': 120.00,
                'is_featured': True,
            },
            {
                'name': 'Highlights',
                'category': color,
                'brand': 'women',
                'description': 'Partial or full highlights using foil technique for natural, sun-kissed dimension.',
                'duration': timedelta(minutes=120),
                'price': 150.00,
                'is_featured': True,
            },
            {
                'name': 'Balayage',
                'category': color,
                'brand': 'women',
                'description': 'Hand-painted highlighting technique for a natural, graduated color effect.',
                'duration': timedelta(minutes=150),
                'price': 200.00,
                'sale_price': 180.00,
                'is_featured': True,
            },
        ]

        for service_data in men_services + women_services:
            obj, created = Service.objects.get_or_create(
                name=service_data['name'],
                brand=service_data['brand'],
                defaults=service_data
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {obj.name} (${obj.price})')

    def create_staff(self):
        # Men's Staff
        men_staff_data = [
            {
                'email': 'marcus.johnson@traditionallifestyle.com',
                'first_name': 'Marcus',
                'last_name': 'Johnson',
                'title': 'Master Barber',
                'bio': 'With over 15 years of experience, Marcus is our lead master barber specializing in classic cuts and hot towel shaves.',
                'years_experience': 15,
            },
            {
                'email': 'james.williams@traditionallifestyle.com',
                'first_name': 'James',
                'last_name': 'Williams',
                'title': 'Senior Barber',
                'bio': 'James brings creativity and precision to every cut. Known for his modern fades and beard artistry.',
                'years_experience': 8,
            },
            {
                'email': 'david.chen@traditionallifestyle.com',
                'first_name': 'David',
                'last_name': 'Chen',
                'title': 'Barber & Stylist',
                'bio': 'David combines Eastern and Western styling techniques for a unique approach to men\'s grooming.',
                'years_experience': 5,
            },
        ]

        # Women's Staff
        women_staff_data = [
            {
                'email': 'sophia.martinez@traditionallifestyle.com',
                'first_name': 'Sophia',
                'last_name': 'Martinez',
                'title': 'Creative Director',
                'bio': 'Sophia is our salon\'s creative director with 12 years of experience in high-end styling and color work.',
                'years_experience': 12,
            },
            {
                'email': 'emma.thompson@traditionallifestyle.com',
                'first_name': 'Emma',
                'last_name': 'Thompson',
                'title': 'Senior Colorist',
                'bio': 'Emma is a color specialist known for her stunning balayage and dimensional highlights.',
                'years_experience': 9,
            },
            {
                'email': 'olivia.davis@traditionallifestyle.com',
                'first_name': 'Olivia',
                'last_name': 'Davis',
                'title': 'Stylist',
                'bio': 'Olivia excels in special occasion styling and updos. She creates looks that make clients feel their best.',
                'years_experience': 6,
            },
        ]

        men_services = Service.objects.filter(brand='men')
        women_services = Service.objects.filter(brand='women')

        for staff_data in men_staff_data:
            user, user_created = User.objects.get_or_create(
                email=staff_data['email'],
                defaults={
                    'first_name': staff_data['first_name'],
                    'last_name': staff_data['last_name'],
                }
            )
            staff, staff_created = Staff.objects.get_or_create(
                user=user,
                defaults={
                    'brand': 'men',
                    'title': staff_data['title'],
                    'bio': staff_data['bio'],
                    'years_experience': staff_data['years_experience'],
                    'is_active': True,
                }
            )
            if staff_created:
                staff.specializations.set(men_services)
            status = 'Created' if staff_created else 'Exists'
            self.stdout.write(f'  {status}: {user.full_name} ({staff.title})')

        for staff_data in women_staff_data:
            user, user_created = User.objects.get_or_create(
                email=staff_data['email'],
                defaults={
                    'first_name': staff_data['first_name'],
                    'last_name': staff_data['last_name'],
                }
            )
            staff, staff_created = Staff.objects.get_or_create(
                user=user,
                defaults={
                    'brand': 'women',
                    'title': staff_data['title'],
                    'bio': staff_data['bio'],
                    'years_experience': staff_data['years_experience'],
                    'is_active': True,
                }
            )
            if staff_created:
                staff.specializations.set(women_services)
            status = 'Created' if staff_created else 'Exists'
            self.stdout.write(f'  {status}: {user.full_name} ({staff.title})')
