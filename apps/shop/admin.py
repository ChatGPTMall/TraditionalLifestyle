"""
Shop Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Coupon, Cart, CartItem, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'parent', 'product_count', 'order', 'is_active']
    list_filter = ['brand', 'is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    ordering = ['brand', 'order', 'name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price_display', 'stock_display',
        'is_active', 'is_featured'
    ]
    list_filter = ['brand', 'category', 'is_active', 'is_featured']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'brand')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price', 'sku')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold')
        }),
        ('Display', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        if obj.is_on_sale:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">₹{}</span> '
                '<span style="color: #22c55e; font-weight: bold;">₹{}</span>',
                obj.price, obj.sale_price
            )
        return f'₹{obj.price}'
    price_display.short_description = 'Price'

    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: #ef4444;">Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: #f59e0b;">{} (Low)</span>', obj.stock)
        return format_html('<span style="color: #22c55e;">{}</span>', obj.stock)
    stock_display.short_description = 'Stock'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_display', 'valid_from', 'valid_until',
        'usage_display', 'is_active', 'validity_badge'
    ]
    list_filter = ['is_active', 'discount_type', 'brand']
    search_fields = ['code']
    list_editable = ['is_active']
    ordering = ['-valid_from']

    fieldsets = (
        (None, {
            'fields': ('code', 'brand', 'is_active')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value', 'max_discount')
        }),
        ('Conditions', {
            'fields': ('min_purchase', 'usage_limit', 'times_used')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
    )

    def discount_display(self, obj):
        if obj.discount_type == 'percent':
            return f'{obj.discount_value}%'
        return f'₹{obj.discount_value}'
    discount_display.short_description = 'Discount'

    def usage_display(self, obj):
        if obj.usage_limit:
            return f'{obj.times_used}/{obj.usage_limit}'
        return f'{obj.times_used}/∞'
    usage_display.short_description = 'Usage'

    def validity_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: #22c55e;">Valid</span>')
        return format_html('<span style="color: #ef4444;">Invalid</span>')
    validity_badge.short_description = 'Status'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['price', 'total']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'item_count', 'subtotal', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__email', 'session_key']
    raw_id_fields = ['user', 'coupon']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_sku', 'price', 'quantity', 'total']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status_badge', 'total_display',
        'is_paid', 'created_at'
    ]
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__first_name']
    raw_id_fields = ['user', 'coupon']
    readonly_fields = [
        'order_number', 'subtotal', 'discount', 'shipping', 'tax', 'total',
        'coupon_code', 'created_at', 'updated_at', 'paid_at'
    ]
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount', 'shipping', 'tax', 'total', 'coupon', 'coupon_code')
        }),
        ('Payment', {
            'fields': ('is_paid', 'paid_at', 'payment_method', 'stripe_payment_intent')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'processing': '#3b82f6',
            'shipped': '#8b5cf6',
            'delivered': '#22c55e',
            'cancelled': '#ef4444',
            'refunded': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def total_display(self, obj):
        return f'₹{obj.total}'
    total_display.short_description = 'Total'

    actions = ['mark_processing', 'mark_shipped', 'mark_delivered']

    @admin.action(description='Mark as Processing')
    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, f'{queryset.count()} orders marked as processing.')

    @admin.action(description='Mark as Shipped')
    def mark_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f'{queryset.count()} orders marked as shipped.')

    @admin.action(description='Mark as Delivered')
    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, f'{queryset.count()} orders marked as delivered.')
