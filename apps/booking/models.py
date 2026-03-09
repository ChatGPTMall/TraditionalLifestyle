"""
Booking Models
Services, Staff, Availability, and Appointments
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


BRAND_CHOICES = [
    ('men', 'Brooklyn Luxury Barbershop'),
    ('women', 'Vintage Salon'),
]


class ServiceCategory(models.Model):
    """Category for grouping services."""
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_brand_display()})"


class Service(models.Model):
    """Salon service offering."""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services'
    )
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    description = models.TextField()
    duration = models.DurationField(help_text='Service duration (e.g., 00:30:00 for 30 minutes)')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - ${self.price}"

    @property
    def duration_minutes(self):
        """Return duration in minutes."""
        return int(self.duration.total_seconds() / 60)

    @property
    def current_price(self):
        """Return sale price if available, otherwise regular price."""
        return self.sale_price if self.sale_price else self.price


class Staff(models.Model):
    """Staff member who provides services."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    brand = models.CharField(max_length=10, choices=BRAND_CHOICES)
    title = models.CharField(max_length=100, help_text='e.g., Master Barber, Senior Stylist')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='staff/', blank=True, null=True)
    specializations = models.ManyToManyField(Service, blank=True, related_name='specialists')
    years_experience = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Staff'
        ordering = ['order', 'user__first_name']

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"


class AvailabilitySlot(models.Model):
    """Available time slots for staff members."""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']

    def __str__(self):
        return f"{self.staff} - {self.date} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """Customer appointment booking."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    # Metadata
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.customer} - {self.service} on {self.date} at {self.start_time}"

    def save(self, *args, **kwargs):
        # Calculate total
        self.total = self.price - self.discount
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        """Check if appointment is in the future."""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return appointment_datetime > now

    @property
    def can_cancel(self):
        """Check if appointment can be cancelled (24 hours before)."""
        if not self.is_upcoming:
            return False
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return (appointment_datetime - now) > timedelta(hours=24)


class SlotHold(models.Model):
    """Temporary hold on a slot during booking process."""
    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.CASCADE, related_name='holds')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    held_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ['slot', 'user']

    def __str__(self):
        return f"Hold on {self.slot} by {self.user}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
