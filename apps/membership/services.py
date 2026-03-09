"""
Membership Services
Stripe integration for subscriptions and payments
"""

import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from .models import MembershipPlan, Membership, Wallet, WalletTransaction

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for Stripe operations."""

    @staticmethod
    def create_customer(user):
        """Create a Stripe customer for a user."""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    'user_id': str(user.id),
                }
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise

    @staticmethod
    def get_or_create_customer(user):
        """Get existing Stripe customer or create new one."""
        # Check if user has existing membership with customer ID
        membership = Membership.objects.filter(
            user=user,
            stripe_customer_id__isnull=False
        ).exclude(stripe_customer_id='').first()

        if membership and membership.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(membership.stripe_customer_id)
                return customer
            except stripe.error.InvalidRequestError:
                pass  # Customer doesn't exist, create new one

        return StripeService.create_customer(user)

    @staticmethod
    def create_checkout_session(user, plan, success_url, cancel_url):
        """
        Create a Stripe Checkout session for subscription.

        Args:
            user: User object
            plan: MembershipPlan object
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Stripe Checkout Session object
        """
        if not plan.stripe_price_id:
            raise ValueError("Plan does not have a Stripe price ID configured")

        customer = StripeService.get_or_create_customer(user)

        try:
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user.id),
                        'plan_id': str(plan.id),
                    }
                }
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            raise

    @staticmethod
    def create_payment_intent(user, amount, description='Wallet top-up'):
        """
        Create a payment intent for one-time payment (wallet top-up).

        Args:
            user: User object
            amount: Amount in dollars (will be converted to cents)
            description: Payment description

        Returns:
            Stripe PaymentIntent object
        """
        customer = StripeService.get_or_create_customer(user)
        amount_cents = int(Decimal(str(amount)) * 100)

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=customer.id,
                description=description,
                metadata={
                    'user_id': str(user.id),
                    'type': 'wallet_topup',
                }
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id):
        """Cancel a Stripe subscription."""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {e}")
            raise

    @staticmethod
    def reactivate_subscription(subscription_id):
        """Reactivate a cancelled subscription."""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription reactivation failed: {e}")
            raise

    @staticmethod
    def get_subscription(subscription_id):
        """Get a Stripe subscription."""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription retrieval failed: {e}")
            raise


class MembershipService:
    """Service class for membership operations."""

    @staticmethod
    def activate_membership(user, plan, stripe_subscription_id, stripe_customer_id):
        """
        Activate a membership for a user.

        Args:
            user: User object
            plan: MembershipPlan object
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID

        Returns:
            Membership object
        """
        # Calculate dates
        start_date = timezone.now().date()
        if plan.plan_type == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:  # yearly
            end_date = start_date + timedelta(days=365)

        # Deactivate any existing active memberships
        Membership.objects.filter(user=user, status='active').update(status='expired')

        # Create new membership
        membership = Membership.objects.create(
            user=user,
            plan=plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            auto_renew=True,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
        )

        # Add initial credits to wallet
        if plan.credits > 0:
            MembershipService.add_membership_credits(user, plan.credits)

        return membership

    @staticmethod
    def add_membership_credits(user, credits):
        """Add membership credits to user's wallet."""
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.add_credits(credits, f'Monthly membership credits')
        return wallet

    @staticmethod
    def handle_subscription_renewed(subscription_id):
        """Handle subscription renewal - add monthly credits."""
        membership = Membership.objects.filter(
            stripe_subscription_id=subscription_id,
            status='active'
        ).first()

        if membership and membership.plan.credits > 0:
            MembershipService.add_membership_credits(
                membership.user,
                membership.plan.credits
            )

            # Update end date
            if membership.plan.plan_type == 'monthly':
                membership.end_date = timezone.now().date() + timedelta(days=30)
            else:
                membership.end_date = timezone.now().date() + timedelta(days=365)
            membership.save()

        return membership

    @staticmethod
    def handle_subscription_cancelled(subscription_id):
        """Handle subscription cancellation."""
        membership = Membership.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()

        if membership:
            membership.status = 'cancelled'
            membership.auto_renew = False
            membership.save()

        return membership

    @staticmethod
    def handle_subscription_expired(subscription_id):
        """Handle subscription expiration."""
        membership = Membership.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()

        if membership:
            membership.status = 'expired'
            membership.save()

        return membership

    @staticmethod
    def handle_payment_failed(subscription_id):
        """Handle failed subscription payment."""
        membership = Membership.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()

        if membership:
            membership.status = 'past_due'
            membership.save()

        return membership

    @staticmethod
    def get_user_discount(user):
        """Get the discount percentage for a user based on their membership."""
        membership = Membership.objects.filter(
            user=user,
            status='active'
        ).first()

        if membership and membership.is_active:
            return membership.plan.discount_percentage
        return 0

    @staticmethod
    def has_priority_booking(user):
        """Check if user has priority booking benefit."""
        membership = Membership.objects.filter(
            user=user,
            status='active'
        ).first()

        if membership and membership.is_active:
            return membership.plan.priority_booking
        return False


class WalletService:
    """Service class for wallet operations."""

    @staticmethod
    def get_or_create_wallet(user):
        """Get or create wallet for user."""
        wallet, created = Wallet.objects.get_or_create(user=user)
        return wallet

    @staticmethod
    def add_funds(user, amount, payment_intent_id):
        """
        Add funds to user's wallet after successful payment.

        Args:
            user: User object
            amount: Amount in dollars
            payment_intent_id: Stripe payment intent ID
        """
        wallet = WalletService.get_or_create_wallet(user)
        wallet.add_balance(amount, f'Wallet top-up')

        # Update the transaction with reference ID
        transaction = wallet.transactions.latest('created_at')
        transaction.reference_id = payment_intent_id
        transaction.save()

        return wallet

    @staticmethod
    def use_for_booking(user, amount, booking_id):
        """
        Use wallet balance for booking payment.

        Args:
            user: User object
            amount: Amount to deduct
            booking_id: Appointment/booking ID for reference

        Returns:
            True if successful, False if insufficient balance
        """
        wallet = WalletService.get_or_create_wallet(user)
        success = wallet.deduct_balance(amount, f'Booking payment #{booking_id}')

        if success:
            transaction = wallet.transactions.latest('created_at')
            transaction.reference_id = str(booking_id)
            transaction.save()

        return success

    @staticmethod
    def use_credits_for_booking(user, credits, booking_id):
        """
        Use wallet credits for booking.

        Args:
            user: User object
            credits: Number of credits to use
            booking_id: Appointment/booking ID for reference

        Returns:
            True if successful, False if insufficient credits
        """
        wallet = WalletService.get_or_create_wallet(user)
        success = wallet.use_credits(credits, f'Booking #{booking_id}')

        if success:
            transaction = wallet.transactions.latest('created_at')
            transaction.reference_id = str(booking_id)
            transaction.save()

        return success

    @staticmethod
    def refund_to_wallet(user, amount, reason='Refund'):
        """Refund amount to user's wallet."""
        wallet = WalletService.get_or_create_wallet(user)
        wallet.balance += Decimal(str(amount))
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='refund',
            description=reason
        )

        return wallet


def handle_stripe_webhook(payload, sig_header):
    """
    Handle incoming Stripe webhook events.

    Args:
        payload: Raw request body
        sig_header: Stripe signature header

    Returns:
        Tuple of (success: bool, message: str)
    """
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return False, 'Invalid payload'
    except stripe.error.SignatureVerificationError:
        return False, 'Invalid signature'

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == 'checkout.session.completed':
            # Subscription checkout completed
            session = data
            if session.get('mode') == 'subscription':
                user_id = session['metadata'].get('user_id')
                plan_id = session['metadata'].get('plan_id')
                subscription_id = session.get('subscription')
                customer_id = session.get('customer')

                if user_id and plan_id and subscription_id:
                    from apps.accounts.models import User
                    user = User.objects.get(pk=user_id)
                    plan = MembershipPlan.objects.get(pk=plan_id)
                    MembershipService.activate_membership(
                        user, plan, subscription_id, customer_id
                    )

        elif event_type == 'invoice.paid':
            # Subscription renewed
            subscription_id = data.get('subscription')
            if subscription_id:
                MembershipService.handle_subscription_renewed(subscription_id)

        elif event_type == 'invoice.payment_failed':
            # Payment failed
            subscription_id = data.get('subscription')
            if subscription_id:
                MembershipService.handle_payment_failed(subscription_id)

        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled/expired
            subscription_id = data.get('id')
            if subscription_id:
                MembershipService.handle_subscription_expired(subscription_id)

        elif event_type == 'customer.subscription.updated':
            # Subscription updated (could be cancellation pending)
            subscription_id = data.get('id')
            cancel_at_period_end = data.get('cancel_at_period_end', False)

            if subscription_id and cancel_at_period_end:
                MembershipService.handle_subscription_cancelled(subscription_id)

        elif event_type == 'payment_intent.succeeded':
            # One-time payment succeeded (wallet top-up)
            if data['metadata'].get('type') == 'wallet_topup':
                user_id = data['metadata'].get('user_id')
                amount = Decimal(data['amount']) / 100  # Convert from cents

                if user_id:
                    from apps.accounts.models import User
                    user = User.objects.get(pk=user_id)
                    WalletService.add_funds(user, amount, data['id'])

        return True, 'Webhook processed successfully'

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return False, str(e)
