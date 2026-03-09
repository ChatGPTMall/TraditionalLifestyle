"""
Membership URL Configuration
"""

from django.urls import path
from . import views

app_name = 'membership'

urlpatterns = [
    # Public pages
    path('', views.MembershipPlansView.as_view(), name='plans'),
    path('subscribe/<int:plan_id>/', views.SubscribeView.as_view(), name='subscribe'),
    path('subscription-success/', views.SubscriptionSuccessView.as_view(), name='subscription_success'),

    # User membership management
    path('my-membership/', views.MyMembershipView.as_view(), name='my_membership'),
    path('cancel/', views.CancelMembershipView.as_view(), name='cancel'),
    path('reactivate/', views.ReactivateMembershipView.as_view(), name='reactivate'),

    # Wallet
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('wallet/add-funds/', views.AddFundsView.as_view(), name='add_funds'),

    # API endpoints
    path('api/create-checkout-session/', views.CreateCheckoutSessionAPIView.as_view(), name='api_create_checkout'),

    # Webhooks
    path('webhook/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
]
