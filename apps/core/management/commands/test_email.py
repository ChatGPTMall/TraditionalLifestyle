"""
Test Email Command
Use this to verify email configuration is working correctly.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']

        self.stdout.write(f"\nEmail Configuration:")
        self.stdout.write(f"  Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"  Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"  User: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write("")

        self.stdout.write(f"Sending test email to {recipient}...")

        try:
            send_mail(
                subject='Test Email from Traditional Lifestyle',
                message='This is a test email to verify your email configuration is working correctly.\n\nIf you received this, your SMTP settings are configured properly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'\nSUCCESS: Test email sent to {recipient}'))
            self.stdout.write('Check your inbox (and spam folder) for the test email.')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nFAILED: {e}'))
            self.stdout.write('\nTroubleshooting tips:')
            self.stdout.write('  1. Make sure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set in .env')
            self.stdout.write('  2. For Gmail, use an App Password (not your regular password)')
            self.stdout.write('  3. Enable "Less secure app access" or use App Passwords in Google Account settings')
