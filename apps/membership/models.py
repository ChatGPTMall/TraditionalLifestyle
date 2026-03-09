"""
Membership Models
Plans, Subscriptions, Wallet, and Credits
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


BRAND_CHOICES = [
    ('men', 'Brooklyn Luxury Barbershop'),
    ('women', 'Vintage Salon'),
]


class MembershipPlan(models.Model):
    """Membership plan configuration."""

    PLAN_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    credits = models.IntegerField(default=0, help_text='Monthly credits included')
    discount_percentage = models.IntegerField(default=0, help_text='Shop discount %')
    priority_booking = models.BooleanField(default=False)
    features = models.JSONField(default=list, help_text='List of feature descriptions')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.get_plan_type_display()}"

    @property
    def monthly_price(self):
        """Return equivalent monthly price."""
        if self.plan_type == 'yearly':
            return self.price / 12
        return self.price


class Membership(models.Model):
    """User's active membership."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.plan.name}"

    @property
    def is_active(self):
        """Check if membership is currently active."""
        today = timezone.now().date()
        return self.status == 'active' and self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        """Days until membership expires."""
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days


class Wallet(models.Model):
    """User wallet for credits and balance."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    credits = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s Wallet - ${self.balance}, {self.credits} credits"

    def add_balance(self, amount, description=''):
        """Add balance to wallet."""
        self.balance += Decimal(str(amount))
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            description=description
        )

    def deduct_balance(self, amount, description=''):
        """Deduct balance from wallet."""
        if self.balance >= Decimal(str(amount)):
            self.balance -= Decimal(str(amount))
            self.save()
            WalletTransaction.objects.create(
                wallet=self,
                amount=-amount,
                transaction_type='debit',
                description=description
            )
            return True
        return False

    def add_credits(self, amount, description=''):
        """Add credits to wallet."""
        self.credits += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            credits_amount=amount,
            transaction_type='credit',
            description=description
        )

    def use_credits(self, amount, description=''):
        """Use credits from wallet."""
        if self.credits >= amount:
            self.credits -= amount
            self.save()
            WalletTransaction.objects.create(
                wallet=self,
                credits_amount=-amount,
                transaction_type='debit',
                description=description
            )
            return True
        return False


class WalletTransaction(models.Model):
    """Wallet transaction history."""

    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('refund', 'Refund'),
        ('membership_credit', 'Membership Credit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    credits_amount = models.IntegerField(default=0)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True, help_text='Payment/Order reference')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user} - {self.transaction_type} - ${self.amount}"
