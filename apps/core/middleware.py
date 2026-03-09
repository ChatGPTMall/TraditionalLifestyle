"""
Theme Brand Middleware
Detects and sets the current brand (men/women) from cookie or URL parameter.
"""

from django.conf import settings


class ThemeBrandMiddleware:
    """
    Middleware to detect and persist brand selection across requests.

    Brand can be set via:
    1. URL parameter: ?brand=men or ?brand=women
    2. Cookie: luxury_brand
    3. Default: settings.DEFAULT_BRAND
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cookie_name = getattr(settings, 'BRAND_COOKIE_NAME', 'luxury_brand')
        self.cookie_age = getattr(settings, 'BRAND_COOKIE_AGE', 60 * 60 * 24 * 365)
        self.default_brand = getattr(settings, 'DEFAULT_BRAND', 'men')
        self.valid_brands = ['men', 'women']

    def __call__(self, request):
        # Try to get brand from URL parameter first
        brand = request.GET.get('brand')

        # If not in URL, try cookie
        if not brand or brand not in self.valid_brands:
            brand = request.COOKIES.get(self.cookie_name)

        # Validate brand
        if brand not in self.valid_brands:
            brand = self.default_brand

        # Set brand on request object for easy access
        request.brand = brand
        request.is_men_brand = brand == 'men'
        request.is_women_brand = brand == 'women'

        # Get response
        response = self.get_response(request)

        # Set/update cookie if brand was explicitly set in URL
        url_brand = request.GET.get('brand')
        if url_brand and url_brand in self.valid_brands:
            response.set_cookie(
                self.cookie_name,
                url_brand,
                max_age=self.cookie_age,
                httponly=False,  # Allow JS access for theme switching
                samesite='Lax'
            )
        # Set cookie if not already set
        elif self.cookie_name not in request.COOKIES:
            response.set_cookie(
                self.cookie_name,
                brand,
                max_age=self.cookie_age,
                httponly=False,
                samesite='Lax'
            )

        return response
