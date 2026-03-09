"""
Core URL Configuration
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('set-brand/<str:brand>/', views.SetBrandView.as_view(), name='set_brand'),
    path('health/', views.health_check, name='health'),
]
