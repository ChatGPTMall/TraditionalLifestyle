"""
Shop Models
Products, Cart, Orders, and Coupons
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


BRAND_CHOICES = [
    ('men', 'Brooklyn Luxury Barbershop'),
    ('women', 'Vintage Salon'),
]


class Category(models.Model):
    """Product category."""
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product for sale."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        """Return sale price if available."""
        return self.sale_price if self.sale_price else self.price

    @property
    def is_on_sale(self):
        """Check if product is on sale."""
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        return self.stock > 0

    @property
    def is_low_stock(self):
        """Check if stock is low."""
        return 0 < self.stock <= self.low_stock_threshold


class ProductImage(models.Model):
    """Product images."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class Coupon(models.Model):
    """Discount coupon."""

    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_purchase = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    max_discount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.IntegerField(null=True, blank=True)
    times_used = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES, blank=True)

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percent' else '$'}"

    @property
    def is_valid(self):
        """Check if coupon is valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, subtotal):
        """Calculate discount amount."""
        if subtotal < self.min_purchase:
            return Decimal('0.00')

        if self.discount_type == 'percent':
            discount = subtotal * (self.discount_value / 100)
        else:
            discount = self.discount_value

        if self.max_discount:
            discount = min(discount, self.max_discount)

        return discount


class Cart(models.Model):
    """Shopping cart."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=100, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} - {self.user or self.session_key}"

    @property
    def subtotal(self):
        """Calculate cart subtotal."""
        return sum(item.total for item in self.items.all())

    @property
    def discount(self):
        """Calculate coupon discount."""
        if self.coupon and self.coupon.is_valid:
            return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def total(self):
        """Calculate cart total."""
        return self.subtotal - self.discount

    @property
    def item_count(self):
        """Total items in cart."""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Item in shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def price(self):
        """Get current product price."""
        return self.product.current_price

    @property
    def total(self):
        """Calculate item total."""
        return self.price * self.quantity


class Order(models.Model):
    """Customer order."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Coupon
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    coupon_code = models.CharField(max_length=50, blank=True)

    # Shipping
    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)

    # Payment
    stripe_payment_intent = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"LL-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Item in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)
