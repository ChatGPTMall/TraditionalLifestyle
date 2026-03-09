"""
Membership Views
Plans, Subscriptions, and Wallet management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.conf import settings
import json

from .models import MembershipPlan, Membership, Wallet, WalletTransaction
from .services import StripeService, MembershipService, WalletService, handle_stripe_webhook


class MembershipPlansView(ListView):
    """Display available membership plans."""
    model = MembershipPlan
    context_object_name = 'plans'

    def get_queryset(self):
        brand = getattr(self.request, 'brand', 'men')
        return MembershipPlan.objects.filter(brand=brand, is_active=True)

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/plans.html', 'common/membership/plans.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_plan'] = self.get_queryset().filter(is_featured=True).first()

        # Check if user has active membership
        if self.request.user.is_authenticated:
            context['current_membership'] = Membership.objects.filter(
                user=self.request.user,
                status='active'
            ).first()

        return context


class SubscribeView(LoginRequiredMixin, TemplateView):
    """Subscribe to a membership plan."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/subscribe.html', 'common/membership/subscribe.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)
        context['plan'] = plan
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def post(self, request, plan_id):
        """Handle subscription creation via Stripe Checkout."""
        plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)

        # Check if Stripe is configured
        if not settings.STRIPE_SECRET_KEY or not plan.stripe_price_id:
            messages.warning(
                request,
                'Payment system not fully configured. Please contact support.'
            )
            return redirect('membership:plans')

        try:
            # Create Stripe Checkout session
            success_url = request.build_absolute_uri(
                reverse('membership:subscription_success')
            ) + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = request.build_absolute_uri(
                reverse('membership:subscribe', kwargs={'plan_id': plan_id})
            )

            session = StripeService.create_checkout_session(
                user=request.user,
                plan=plan,
                success_url=success_url,
                cancel_url=cancel_url
            )

            # Redirect to Stripe Checkout
            return redirect(session.url)

        except Exception as e:
            messages.error(request, f'Unable to process subscription: {str(e)}')
            return redirect('membership:plans')


class SubscriptionSuccessView(LoginRequiredMixin, TemplateView):
    """Handle successful subscription."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/success.html', 'common/membership/success.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the latest active membership
        context['membership'] = Membership.objects.filter(
            user=self.request.user,
            status='active'
        ).first()

        return context


class MyMembershipView(LoginRequiredMixin, TemplateView):
    """View current membership status."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/my_membership.html', 'common/membership/my_membership.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membership'] = Membership.objects.filter(
            user=self.request.user,
            status='active'
        ).first()

        # Get wallet info
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet

        # Get available plans for upgrade
        brand = getattr(self.request, 'brand', 'men')
        context['plans'] = MembershipPlan.objects.filter(brand=brand, is_active=True)

        return context


class WalletView(LoginRequiredMixin, TemplateView):
    """View wallet balance and transactions."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/wallet.html', 'common/membership/wallet.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        context['transactions'] = wallet.transactions.all()[:20]
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context


class AddFundsView(LoginRequiredMixin, TemplateView):
    """Add funds to wallet."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/membership/add_funds.html', 'common/membership/add_funds.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY

        # Predefined amounts
        context['amounts'] = [25, 50, 100, 200]

        return context

    def post(self, request):
        """Create payment intent for adding funds."""
        amount = request.POST.get('amount')

        try:
            amount = float(amount)
            if amount < 500:
                messages.error(request, 'Minimum amount is ₹500.')
                return redirect('membership:add_funds')
            if amount > 50000:
                messages.error(request, 'Maximum amount is ₹50,000.')
                return redirect('membership:add_funds')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
            return redirect('membership:add_funds')

        # Check if Stripe is configured
        if not settings.STRIPE_SECRET_KEY:
            messages.warning(
                request,
                'Payment system not configured. Please contact support.'
            )
            return redirect('membership:wallet')

        try:
            intent = StripeService.create_payment_intent(
                user=request.user,
                amount=amount,
                description=f'Wallet top-up - ${amount}'
            )

            return JsonResponse({
                'client_secret': intent.client_secret
            })

        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)


class CancelMembershipView(LoginRequiredMixin, View):
    """Cancel membership subscription."""

    def post(self, request):
        membership = Membership.objects.filter(
            user=request.user,
            status='active'
        ).first()

        if not membership:
            messages.error(request, 'No active membership found.')
            return redirect('membership:my_membership')

        try:
            # Cancel on Stripe if subscription exists
            if membership.stripe_subscription_id:
                StripeService.cancel_subscription(membership.stripe_subscription_id)
                messages.success(
                    request,
                    'Your membership will be cancelled at the end of the billing period.'
                )
            else:
                # No Stripe subscription, cancel immediately
                membership.status = 'cancelled'
                membership.auto_renew = False
                membership.save()
                messages.success(request, 'Your membership has been cancelled.')

        except Exception as e:
            messages.error(request, f'Unable to cancel membership: {str(e)}')

        return redirect('membership:my_membership')


class ReactivateMembershipView(LoginRequiredMixin, View):
    """Reactivate a cancelled membership."""

    def post(self, request):
        membership = Membership.objects.filter(
            user=request.user,
            status__in=['cancelled', 'active']
        ).first()

        if not membership:
            messages.error(request, 'No membership found to reactivate.')
            return redirect('membership:my_membership')

        if not membership.stripe_subscription_id:
            messages.error(request, 'Cannot reactivate membership without subscription.')
            return redirect('membership:my_membership')

        try:
            StripeService.reactivate_subscription(membership.stripe_subscription_id)
            membership.auto_renew = True
            membership.status = 'active'
            membership.save()
            messages.success(request, 'Your membership has been reactivated.')
        except Exception as e:
            messages.error(request, f'Unable to reactivate membership: {str(e)}')

        return redirect('membership:my_membership')


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Handle Stripe webhooks."""

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        success, message = handle_stripe_webhook(payload, sig_header)

        if success:
            return HttpResponse(status=200)
        else:
            return HttpResponse(message, status=400)


class CreateCheckoutSessionAPIView(LoginRequiredMixin, View):
    """API endpoint to create Stripe Checkout session."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)

        if not plan.stripe_price_id:
            return JsonResponse({
                'error': 'This plan is not available for online subscription.'
            }, status=400)

        try:
            success_url = request.build_absolute_uri(
                reverse('membership:subscription_success')
            ) + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = request.build_absolute_uri(reverse('membership:plans'))

            session = StripeService.create_checkout_session(
                user=request.user,
                plan=plan,
                success_url=success_url,
                cancel_url=cancel_url
            )

            return JsonResponse({'url': session.url})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
