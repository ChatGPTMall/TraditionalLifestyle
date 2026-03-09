"""
Theme Context Processor
Injects theme-related variables into all template contexts.
"""

from django.conf import settings


def theme_context(request):
    """
    Add theme/brand variables to template context.

    Available in templates:
    - {{ brand }}: Current brand ('men' or 'women')
    - {{ brand_name }}: Display name ('Brooklyn Luxury Barbershop' or 'Vintage Salon')
    - {{ is_men_brand }}: Boolean for men brand
    - {{ is_women_brand }}: Boolean for women brand
    - {{ theme_template_prefix }}: Template prefix ('men/' or 'women/')
    - {{ opposite_brand }}: The other brand
    - {{ opposite_brand_name }}: Display name of other brand
    """
    brand = getattr(request, 'brand', settings.DEFAULT_BRAND)

    brand_names = {
        'men': 'Brooklyn Luxury Barbershop',
        'women': 'Vintage Salon',
    }

    brand_taglines = {
        'men': 'Where style meets tradition.',
        'women': 'Premium salon experiences for women.',
    }

    opposite_brand = 'women' if brand == 'men' else 'men'

    return {
        'brand': brand,
        'brand_name': brand_names.get(brand, 'TraditionalLifestyle'),
        'brand_tagline': brand_taglines.get(brand, ''),
        'is_men_brand': brand == 'men',
        'is_women_brand': brand == 'women',
        'theme_template_prefix': f'{brand}/',
        'opposite_brand': opposite_brand,
        'opposite_brand_name': brand_names.get(opposite_brand, ''),
        'brand_cookie_name': settings.BRAND_COOKIE_NAME,
    }
