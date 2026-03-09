"""
Core Views
Landing page and brand selection.
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import HttpResponse


class LandingPageView(TemplateView):
    """
    Brand selection landing page.
    Shows split-screen design for Men/Women brand choice.
    Always displays as the homepage.
    """
    template_name = 'common/landing.html'


class HomeView(TemplateView):
    """
    Brand-specific home page.
    Template is selected based on current brand.
    """

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/home.html']


class SetBrandView(TemplateView):
    """
    Explicitly set brand and redirect.
    """

    def get(self, request, brand, *args, **kwargs):
        if brand not in ['men', 'women']:
            brand = 'men'

        response = redirect('core:home')
        response.set_cookie(
            'luxury_brand',
            brand,
            max_age=60 * 60 * 24 * 365,
            httponly=False,
            samesite='Lax'
        )
        return response


def health_check(request):
    """Simple health check endpoint."""
    return HttpResponse('OK', content_type='text/plain')
