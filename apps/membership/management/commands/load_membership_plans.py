"""
Management command to load sample membership plans.
"""

from django.core.management.base import BaseCommand
from apps.membership.models import MembershipPlan


class Command(BaseCommand):
    help = 'Load sample membership plans for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing plans before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing membership plans...')
            MembershipPlan.objects.all().delete()

        self.stdout.write('Creating membership plans...')

        # Men's Plans (Brooklyn Luxury Barbershop)
        men_plans = [
            {
                'name': 'Classic',
                'brand': 'men',
                'plan_type': 'monthly',
                'price': 49.00,
                'credits': 1,
                'discount_percentage': 10,
                'priority_booking': False,
                'is_featured': False,
                'order': 1,
                'features': [
                    '1 monthly service credit',
                    '10% off all products',
                    'Birthday bonus credit',
                    'Early access to new services',
                ]
            },
            {
                'name': 'Executive',
                'brand': 'men',
                'plan_type': 'monthly',
                'price': 89.00,
                'credits': 2,
                'discount_percentage': 15,
                'priority_booking': True,
                'is_featured': True,
                'order': 2,
                'features': [
                    '2 monthly service credits',
                    '15% off all products',
                    'Priority booking access',
                    'Complimentary hot towel service',
                    'Birthday bonus credit',
                    'Exclusive member events',
                ]
            },
            {
                'name': 'Chairman',
                'brand': 'men',
                'plan_type': 'yearly',
                'price': 899.00,
                'credits': 3,
                'discount_percentage': 20,
                'priority_booking': True,
                'is_featured': False,
                'order': 3,
                'features': [
                    '3 monthly service credits',
                    '20% off all products',
                    'Priority booking access',
                    'VIP lounge access',
                    'Complimentary beverages',
                    'Personal grooming consultant',
                    'Birthday bonus credits (2)',
                    'Annual gift package',
                ]
            },
        ]

        # Women's Plans (Vintage Salon)
        women_plans = [
            {
                'name': 'Essentials',
                'brand': 'women',
                'plan_type': 'monthly',
                'price': 59.00,
                'credits': 1,
                'discount_percentage': 10,
                'priority_booking': False,
                'is_featured': False,
                'order': 1,
                'features': [
                    '1 monthly service credit',
                    '10% off all products',
                    'Birthday bonus credit',
                    'Styling tips newsletter',
                ]
            },
            {
                'name': 'Signature',
                'brand': 'women',
                'plan_type': 'monthly',
                'price': 119.00,
                'credits': 2,
                'discount_percentage': 15,
                'priority_booking': True,
                'is_featured': True,
                'order': 2,
                'features': [
                    '2 monthly service credits',
                    '15% off all products',
                    'Priority booking access',
                    'Complimentary scalp treatment',
                    'Birthday bonus credit',
                    'Exclusive member events',
                    'Free product samples',
                ]
            },
            {
                'name': 'Luxe',
                'brand': 'women',
                'plan_type': 'yearly',
                'price': 1199.00,
                'credits': 3,
                'discount_percentage': 20,
                'priority_booking': True,
                'is_featured': False,
                'order': 3,
                'features': [
                    '3 monthly service credits',
                    '20% off all products',
                    'Priority booking access',
                    'Private styling suite',
                    'Complimentary beverages & snacks',
                    'Personal style consultant',
                    'Birthday bonus credits (2)',
                    'Annual luxury gift package',
                    'Invite to fashion events',
                ]
            },
        ]

        for plan_data in men_plans + women_plans:
            plan, created = MembershipPlan.objects.get_or_create(
                name=plan_data['name'],
                brand=plan_data['brand'],
                defaults=plan_data
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {plan.name} ({plan.get_brand_display()}) - ${plan.price}')

        self.stdout.write(self.style.SUCCESS('Membership plans loaded successfully!'))
        self.stdout.write('')
        self.stdout.write('Summary:')
        self.stdout.write(f'  - Men\'s Plans: {MembershipPlan.objects.filter(brand="men").count()}')
        self.stdout.write(f'  - Women\'s Plans: {MembershipPlan.objects.filter(brand="women").count()}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'Note: To enable Stripe payments, add stripe_price_id to each plan in the admin.'
        ))
