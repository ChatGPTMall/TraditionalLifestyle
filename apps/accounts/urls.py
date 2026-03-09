"""
Accounts URL Configuration
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('notifications/', views.NotificationPreferencesView.as_view(), name='notifications'),
]
