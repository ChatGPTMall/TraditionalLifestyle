"""
Shop Views
Products, Cart, and Checkout
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse

from .models import Product, Category, Cart, CartItem, Order, Coupon


class BrandFilterMixin:
    """Filter querysets by current brand."""

    def get_brand(self):
        return getattr(self.request, 'brand', 'men')


class ProductListView(BrandFilterMixin, ListView):
    """List all products."""
    model = Product
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        brand = self.get_brand()
        queryset = Product.objects.filter(brand=brand, is_active=True)

        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Sort
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['price', '-price', 'name', '-name', '-created_at']:
            queryset = queryset.order_by(sort)

        return queryset.select_related('category')

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/shop/products.html', 'common/shop/products.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_brand()
        context['categories'] = Category.objects.filter(brand=brand, is_active=True)
        context['featured_products'] = Product.objects.filter(
            brand=brand, is_active=True, is_featured=True
        )[:4]
        return context


class CategoryProductsView(BrandFilterMixin, ListView):
    """List products in a category."""
    model = Product
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        brand = self.get_brand()
        category_slug = self.kwargs.get('slug')
        return Product.objects.filter(
            brand=brand,
            is_active=True,
            category__slug=category_slug
        )

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/shop/category.html', 'common/shop/category.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, slug=self.kwargs.get('slug'))
        return context


class ProductDetailView(BrandFilterMixin, DetailView):
    """Product detail page."""
    model = Product
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        brand = self.get_brand()
        return Product.objects.filter(brand=brand, is_active=True)

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/shop/product_detail.html', 'common/shop/product_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            brand=self.get_brand(),
            category=self.object.category,
            is_active=True
        ).exclude(pk=self.object.pk)[:4]
        return context


class CartView(TemplateView):
    """Shopping cart page."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/shop/cart.html', 'common/shop/cart.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.get_cart()
        return context

    def get_cart(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
        return cart


class AddToCartView(View):
    """Add product to cart."""

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))

        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart.item_count,
                'message': f'{product.name} added to cart'
            })

        messages.success(request, f'{product.name} added to cart')
        return redirect('shop:cart')


class RemoveFromCartView(View):
    """Remove item from cart."""

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, pk=item_id)

        # Verify ownership
        if request.user.is_authenticated:
            if cart_item.cart.user != request.user:
                messages.error(request, 'Item not found in your cart.')
                return redirect('shop:cart')
        else:
            if cart_item.cart.session_key != request.session.session_key:
                messages.error(request, 'Item not found in your cart.')
                return redirect('shop:cart')

        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
        return redirect('shop:cart')


class UpdateCartItemView(View):
    """Update cart item quantity."""

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, pk=item_id)
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return redirect('shop:cart')


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout page."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/shop/checkout.html', 'common/shop/checkout.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.filter(user=self.request.user).first()
        context['cart'] = cart
        return context

    def post(self, request):
        """Handle checkout submission."""
        # TODO: Implement Stripe payment and order creation
        messages.info(request, 'Stripe checkout coming soon.')
        return redirect('shop:cart')


class CheckoutSuccessView(LoginRequiredMixin, TemplateView):
    """Checkout success page."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/shop/checkout_success.html', 'common/shop/checkout_success.html']


class OrderListView(LoginRequiredMixin, ListView):
    """List user's orders."""
    model = Order
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/shop/orders.html', 'common/shop/orders.html']


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail page."""
    model = Order
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/shop/order_detail.html', 'common/shop/order_detail.html']


class ApplyCouponView(View):
    """Apply coupon to cart."""

    def post(self, request):
        code = request.POST.get('code', '').strip().upper()

        if not code:
            messages.error(request, 'Please enter a coupon code.')
            return redirect('shop:cart')

        try:
            coupon = Coupon.objects.get(code=code)
            if not coupon.is_valid:
                messages.error(request, 'This coupon is no longer valid.')
                return redirect('shop:cart')

            # Apply to cart
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.coupon = coupon
                cart.save()
                messages.success(request, f'Coupon {code} applied!')
            else:
                messages.error(request, 'No cart found.')

        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')

        return redirect('shop:cart')
