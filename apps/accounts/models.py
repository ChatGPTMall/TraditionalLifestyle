"""
Custom User Model for TraditionalLifestyle
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for TraditionalLifestyle.
    Uses email as the unique identifier instead of username.
    """

    BRAND_CHOICES = [
        ('men', 'Brooklyn Luxury Barbershop'),
        ('women', 'Vintage Salon'),
    ]

    username = None
    email = models.EmailField('email address', unique=True)

    # Profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    preferred_brand = models.CharField(
        max_length=10,
        choices=BRAND_CHOICES,
        default='men',
        help_text='Preferred salon brand'
    )
    date_of_birth = models.DateField(blank=True, null=True)

    # Address fields
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='United States')

    # Preferences
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    receive_whatsapp_notifications = models.BooleanField(default=False)

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f'{self.city}, {self.state} {self.postal_code}'.strip(', '),
            self.country
        ]
        return '\n'.join(filter(None, parts))
