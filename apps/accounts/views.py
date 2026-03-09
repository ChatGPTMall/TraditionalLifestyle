"""
Accounts Views
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import ProfileForm, NotificationPreferencesForm
from apps.booking.models import Appointment
from apps.membership.models import Membership, Wallet


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display user profile."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/accounts/profile.html', 'common/accounts/profile.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user

        # Get booking stats
        appointments = Appointment.objects.filter(customer=user)
        context['total_bookings'] = appointments.count()

        # Get upcoming appointments
        today = timezone.now().date()
        upcoming = appointments.filter(
            date__gte=today,
            status__in=['pending', 'confirmed']
        ).order_by('date', 'start_time')[:5]
        context['upcoming_bookings'] = upcoming
        context['upcoming_count'] = upcoming.count()

        # Get recent bookings (past appointments)
        recent = appointments.filter(
            date__lt=today
        ).order_by('-date', '-start_time')[:5]
        context['recent_bookings'] = recent

        # Get wallet/credits
        try:
            wallet = Wallet.objects.get(user=user)
            context['credits'] = wallet.credits
            context['wallet_balance'] = wallet.balance
        except Wallet.DoesNotExist:
            context['credits'] = 0
            context['wallet_balance'] = 0

        # Get active membership
        try:
            membership = Membership.objects.filter(
                user=user,
                status='active',
                start_date__lte=today,
                end_date__gte=today
            ).select_related('plan').first()
            context['membership'] = membership
        except Membership.DoesNotExist:
            context['membership'] = None

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile."""
    form_class = ProfileForm
    success_url = reverse_lazy('accounts:profile')

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/accounts/profile_edit.html', 'common/accounts/profile_edit.html']

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    """Update notification preferences."""
    form_class = NotificationPreferencesForm
    success_url = reverse_lazy('accounts:profile')

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/accounts/notifications.html', 'common/accounts/notifications.html']

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Notification preferences updated!')
        return super().form_valid(form)
