"""
Accounts Forms
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Form for user registration."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """Form for updating user profile."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'avatar', 'preferred_brand')


class ProfileForm(forms.ModelForm):
    """Form for user profile updates."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'avatar',
            'date_of_birth', 'preferred_brand',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'receive_email_notifications', 'receive_sms_notifications', 'receive_whatsapp_notifications'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class NotificationPreferencesForm(forms.ModelForm):
    """Form for notification preferences."""

    class Meta:
        model = User
        fields = [
            'receive_email_notifications',
            'receive_sms_notifications',
            'receive_whatsapp_notifications'
        ]
