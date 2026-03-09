"""
Async Email Utilities
Send emails in background threads to avoid blocking user requests
"""

import threading
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email_async(subject, plain_message, recipient_list, html_message=None, from_email=None):
    """
    Send email asynchronously in a background thread.

    Args:
        subject: Email subject
        plain_message: Plain text message
        recipient_list: List of recipient emails
        html_message: Optional HTML message
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    def send():
        try:
            logger.info(f"Sending async email to {recipient_list}")
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {e}")

    thread = threading.Thread(target=send, daemon=True)
    thread.start()


def send_templated_email_async(subject, template_name, context, recipient_list, from_email=None):
    """
    Send a templated email asynchronously.

    Args:
        subject: Email subject
        template_name: Base template name (without extension)
                      Will look for {template_name}.html and {template_name}.txt
        context: Template context dictionary
        recipient_list: List of recipient emails
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    def send():
        try:
            logger.info(f"Sending async templated email to {recipient_list}")

            # Render templates
            html_message = render_to_string(f'{template_name}.html', context)
            plain_message = render_to_string(f'{template_name}.txt', context)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Templated email sent successfully to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send templated email to {recipient_list}: {e}")

    thread = threading.Thread(target=send, daemon=True)
    thread.start()
