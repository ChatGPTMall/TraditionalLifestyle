"""
Booking Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import ServiceCategory, Service, Staff, AvailabilitySlot, Appointment, SlotHold


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'order', 'service_count']
    list_filter = ['brand']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    def service_count(self, obj):
        return obj.services.count()
    service_count.short_description = 'Services'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price', 'duration_display', 'is_active', 'is_featured']
    list_filter = ['brand', 'category', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'brand', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'sale_price', 'duration')
        }),
        ('Display Options', {
            'fields': ('image', 'is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def duration_display(self, obj):
        return f"{obj.duration_minutes} min"
    duration_display.short_description = 'Duration'


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'title', 'brand', 'years_experience', 'is_active', 'appointment_count']
    list_filter = ['brand', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'title']
    filter_horizontal = ['specializations']
    list_editable = ['is_active']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'brand', 'title', 'bio')
        }),
        ('Details', {
            'fields': ('avatar', 'years_experience', 'specializations')
        }),
        ('Display', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_name(self, obj):
        return obj.user.full_name
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'user__first_name'

    def appointment_count(self, obj):
        return obj.appointments.filter(status__in=['pending', 'confirmed']).count()
    appointment_count.short_description = 'Upcoming'


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'start_time', 'end_time', 'is_available', 'has_appointment']
    list_filter = ['staff__brand', 'is_available', 'date', 'staff']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    date_hierarchy = 'date'
    ordering = ['date', 'start_time']
    list_editable = ['is_available']

    def has_appointment(self, obj):
        has_appt = obj.appointments.filter(status__in=['pending', 'confirmed']).exists()
        if has_appt:
            return format_html('<span style="color: #d4af37;">Booked</span>')
        return format_html('<span style="color: #87d762;">Available</span>')
    has_appointment.short_description = 'Status'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer_name', 'service', 'staff_name', 'date', 'start_time',
        'status_badge', 'total', 'is_paid'
    ]
    list_filter = ['status', 'is_paid', 'staff__brand', 'date', 'staff']
    search_fields = [
        'customer__email', 'customer__first_name', 'customer__last_name',
        'service__name', 'staff__user__first_name'
    ]
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'confirmation_sent', 'reminder_sent']
    ordering = ['-date', '-start_time']

    fieldsets = (
        ('Customer & Service', {
            'fields': ('customer', 'service', 'staff', 'slot')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Status & Payment', {
            'fields': ('status', 'is_paid', 'payment_method')
        }),
        ('Pricing', {
            'fields': ('price', 'discount', 'total')
        }),
        ('Notes', {
            'fields': ('notes', 'special_requests'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('confirmation_sent', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def customer_name(self, obj):
        return obj.customer.full_name
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__first_name'

    def staff_name(self, obj):
        return obj.staff.user.full_name
    staff_name.short_description = 'Staff'
    staff_name.admin_order_field = 'staff__user__first_name'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'in_progress': '#8b5cf6',
            'completed': '#22c55e',
            'cancelled': '#ef4444',
            'no_show': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    @admin.action(description='Mark selected as Confirmed')
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointments marked as confirmed.')

    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')

    @admin.action(description='Mark selected as Cancelled')
    def mark_cancelled(self, request, queryset):
        for appointment in queryset:
            appointment.status = 'cancelled'
            appointment.save()
            if appointment.slot:
                appointment.slot.is_available = True
                appointment.slot.save()
        self.message_user(request, f'{queryset.count()} appointments cancelled.')


@admin.register(SlotHold)
class SlotHoldAdmin(admin.ModelAdmin):
    list_display = ['slot', 'user', 'held_at', 'expires_at', 'is_expired_badge']
    list_filter = ['slot__staff__brand']
    search_fields = ['user__email', 'slot__staff__user__first_name']
    readonly_fields = ['held_at']

    def is_expired_badge(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: #ef4444;">Expired</span>')
        return format_html('<span style="color: #22c55e;">Active</span>')
    is_expired_badge.short_description = 'Status'

    actions = ['cleanup_expired']

    @admin.action(description='Clean up expired holds')
    def cleanup_expired(self, request, queryset):
        from .availability import BookingService
        count = BookingService.cleanup_expired_holds()
        self.message_user(request, f'{count} expired holds cleaned up.')
