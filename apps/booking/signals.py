"""
Booking Signals
Notification triggers for appointments
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.conf import settings

from .models import Appointment
from apps.core.email_utils import send_email_async

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Appointment)
def track_status_change(sender, instance, **kwargs):
    """Track status changes before save."""
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Appointment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Appointment)
def appointment_saved(sender, instance, created, **kwargs):
    """Handle appointment save - send notifications."""
    if created:
        # New appointment created
        send_appointment_confirmation(instance)
    else:
        # Check for status changes
        old_status = getattr(instance, '_old_status', None)

        if old_status != instance.status:
            if instance.status == 'confirmed':
                send_appointment_confirmed(instance)
            elif instance.status == 'cancelled':
                send_appointment_cancelled(instance)


def send_appointment_confirmation(appointment: Appointment):
    """Send appointment confirmation email to customer (async)."""
    if not appointment.customer.email:
        return

    subject = f'Appointment Confirmation - {appointment.service.name}'

    # Determine brand for template context
    brand = appointment.service.brand
    brand_name = 'Brooklyn Luxury Barbershop' if brand == 'men' else 'Vintage Salon'

    context = {
        'appointment': appointment,
        'customer': appointment.customer,
        'service': appointment.service,
        'staff': appointment.staff,
        'brand_name': brand_name,
        'brand': brand,
    }

    # Render email templates
    html_message = render_to_string('emails/appointment_confirmation.html', context)
    plain_message = render_to_string('emails/appointment_confirmation.txt', context)

    logger.info(f"Queuing confirmation email to {appointment.customer.email}")

    # Send async - don't block the request
    send_email_async(
        subject=subject,
        plain_message=plain_message,
        recipient_list=[appointment.customer.email],
        html_message=html_message,
    )

    # Mark as sent (optimistic - email is queued)
    Appointment.objects.filter(pk=appointment.pk).update(confirmation_sent=True)


def send_appointment_confirmed(appointment: Appointment):
    """Send email when appointment is confirmed by staff (async)."""
    if not appointment.customer.email:
        return

    subject = f'Appointment Confirmed - {appointment.service.name}'

    brand = appointment.service.brand
    brand_name = 'Brooklyn Luxury Barbershop' if brand == 'men' else 'Vintage Salon'

    context = {
        'appointment': appointment,
        'customer': appointment.customer,
        'service': appointment.service,
        'staff': appointment.staff,
        'brand_name': brand_name,
        'brand': brand,
    }

    html_message = render_to_string('emails/appointment_confirmed.html', context)
    plain_message = render_to_string('emails/appointment_confirmed.txt', context)

    logger.info(f"Queuing confirmed email to {appointment.customer.email}")

    send_email_async(
        subject=subject,
        plain_message=plain_message,
        recipient_list=[appointment.customer.email],
        html_message=html_message,
    )


def send_appointment_cancelled(appointment: Appointment):
    """Send email when appointment is cancelled (async)."""
    if not appointment.customer.email:
        return

    subject = f'Appointment Cancelled - {appointment.service.name}'

    brand = appointment.service.brand
    brand_name = 'Brooklyn Luxury Barbershop' if brand == 'men' else 'Vintage Salon'

    context = {
        'appointment': appointment,
        'customer': appointment.customer,
        'service': appointment.service,
        'staff': appointment.staff,
        'brand_name': brand_name,
        'brand': brand,
    }

    html_message = render_to_string('emails/appointment_cancelled.html', context)
    plain_message = render_to_string('emails/appointment_cancelled.txt', context)

    logger.info(f"Queuing cancellation email to {appointment.customer.email}")

    send_email_async(
        subject=subject,
        plain_message=plain_message,
        recipient_list=[appointment.customer.email],
        html_message=html_message,
    )


def send_appointment_reminder(appointment: Appointment):
    """
    Send appointment reminder email (async).
    Should be called by Celery task 24 hours before appointment.
    """
    if not appointment.customer.email:
        return

    if appointment.reminder_sent:
        return

    subject = f'Reminder: Your Appointment Tomorrow - {appointment.service.name}'

    brand = appointment.service.brand
    brand_name = 'Brooklyn Luxury Barbershop' if brand == 'men' else 'Vintage Salon'

    context = {
        'appointment': appointment,
        'customer': appointment.customer,
        'service': appointment.service,
        'staff': appointment.staff,
        'brand_name': brand_name,
        'brand': brand,
    }

    html_message = render_to_string('emails/appointment_reminder.html', context)
    plain_message = render_to_string('emails/appointment_reminder.txt', context)

    logger.info(f"Queuing reminder email to {appointment.customer.email}")

    send_email_async(
        subject=subject,
        plain_message=plain_message,
        recipient_list=[appointment.customer.email],
        html_message=html_message,
    )

    # Mark as sent (optimistic)
    Appointment.objects.filter(pk=appointment.pk).update(reminder_sent=True)
