"""
Booking Signals
Notification triggers for appointments
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Appointment


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
    """Send appointment confirmation email to customer."""
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

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer.email],
            html_message=html_message,
            fail_silently=True,
        )
        appointment.confirmation_sent = True
        appointment.save(update_fields=['confirmation_sent'])
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")


def send_appointment_confirmed(appointment: Appointment):
    """Send email when appointment is confirmed by staff."""
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

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send confirmed email: {e}")


def send_appointment_cancelled(appointment: Appointment):
    """Send email when appointment is cancelled."""
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

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send cancellation email: {e}")


def send_appointment_reminder(appointment: Appointment):
    """
    Send appointment reminder email.
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

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer.email],
            html_message=html_message,
            fail_silently=True,
        )
        appointment.reminder_sent = True
        appointment.save(update_fields=['reminder_sent'])
    except Exception as e:
        print(f"Failed to send reminder email: {e}")
