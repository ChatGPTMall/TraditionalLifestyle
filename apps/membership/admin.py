"""
Membership Admin Configuration
"""

from django.contrib import admin
from .models import MembershipPlan, Membership, Wallet, WalletTransaction


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'plan_type', 'price', 'credits', 'discount_percentage', 'is_active', 'is_featured']
    list_filter = ['brand', 'plan_type', 'is_active', 'is_featured']
    list_editable = ['is_active', 'is_featured', 'price']
    search_fields = ['name']
    ordering = ['brand', 'order', 'price']

    fieldsets = (
        (None, {
            'fields': ('name', 'brand', 'plan_type', 'price')
        }),
        ('Benefits', {
            'fields': ('credits', 'discount_percentage', 'priority_booking', 'features')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id',),
            'description': 'Add the Stripe Price ID to enable online subscriptions.'
        }),
        ('Display', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'plan__brand', 'plan', 'auto_renew']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'plan']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'auto_renew')
        }),
        ('Stripe', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'credits', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'credits_amount', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__email', 'description', 'reference_id']
    raw_id_fields = ['wallet']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    def has_change_permission(self, request, obj=None):
        return False  # Transactions should be immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Transactions should not be deleted
