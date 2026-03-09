"""
Booking Availability Service
Redis-based slot locking and availability management
"""

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta, time, date as date_type
from typing import Optional, List, Dict, Union
import hashlib
import calendar

from .models import Staff, Service, AvailabilitySlot, Appointment, SlotHold


# Constants
SLOT_HOLD_DURATION = 5 * 60  # 5 minutes in seconds
SLOT_LOCK_PREFIX = 'slot_lock:'
SLOT_HOLD_PREFIX = 'slot_hold:'

# Default working hours
DEFAULT_START_HOUR = 9
DEFAULT_END_HOUR = 20
DEFAULT_INTERVAL = 30  # minutes


class BookingService:
    """
    Service class for managing booking availability and slot reservations.
    Uses Redis for distributed locking when available, falls back to database.
    """

    @staticmethod
    def get_lock_key(staff_id: int, date: str, start_time: str) -> str:
        """Generate a unique lock key for a slot."""
        key = f"{SLOT_LOCK_PREFIX}{staff_id}:{date}:{start_time}"
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def get_hold_key(user_id: int, staff_id: int, date: str, start_time: str) -> str:
        """Generate a unique hold key for a user's slot hold."""
        key = f"{SLOT_HOLD_PREFIX}{user_id}:{staff_id}:{date}:{start_time}"
        return hashlib.md5(key.encode()).hexdigest()

    def get_available_dates(
        self,
        service_id: int,
        staff_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[str]:
        """
        Get list of dates with available slots for booking.

        Args:
            service_id: Service ID
            staff_id: Optional staff ID (None = any available staff)
            month: Month number (1-12)
            year: Year

        Returns:
            List of date strings (YYYY-MM-DD format)
        """
        today = timezone.now().date()

        if month is None:
            month = today.month
        if year is None:
            year = today.year

        # Get first and last day of month
        _, last_day = calendar.monthrange(year, month)
        month_start = date_type(year, month, 1)
        month_end = date_type(year, month, last_day)

        # Adjust start date if it's in the past
        if month_start < today:
            month_start = today

        # Get staff members who can perform this service
        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return []

        if staff_id:
            staff_members = Staff.objects.filter(pk=staff_id, is_active=True)
        else:
            staff_members = service.specialists.filter(is_active=True)

        if not staff_members.exists():
            # If no specialists assigned, get all active staff for the brand
            staff_members = Staff.objects.filter(brand=service.brand, is_active=True)

        if not staff_members.exists():
            return []

        # Generate available dates
        # For simplicity, we'll mark all weekdays as available
        # In production, this would check actual staff schedules
        available_dates = []
        current_date = month_start

        while current_date <= month_end:
            # Skip Sundays (weekday() == 6)
            if current_date.weekday() != 6:
                # Check if any staff is available on this date
                # For now, assume all staff work Mon-Sat
                available_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        return available_dates

    def get_available_slots(
        self,
        service_id: int,
        date: str,
        staff_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get available time slots for a specific date.

        Args:
            service_id: Service ID
            date: Date string (YYYY-MM-DD)
            staff_id: Optional staff ID (None = any available staff)

        Returns:
            List of slot dictionaries with id, time, staff info
        """
        try:
            service = Service.objects.get(pk=service_id)
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except (Service.DoesNotExist, ValueError):
            return []

        # Don't allow booking in the past
        if target_date < timezone.now().date():
            return []

        # Get staff members
        if staff_id:
            staff_members = Staff.objects.filter(pk=staff_id, is_active=True)
        else:
            staff_members = service.specialists.filter(is_active=True)

        if not staff_members.exists():
            staff_members = Staff.objects.filter(brand=service.brand, is_active=True)

        if not staff_members.exists():
            return []

        # Get booked appointments for this date
        booked = Appointment.objects.filter(
            date=target_date,
            status__in=['pending', 'confirmed', 'in_progress']
        ).values_list('staff_id', 'start_time')

        booked_slots = {}
        for staff_pk, start_time in booked:
            if staff_pk not in booked_slots:
                booked_slots[staff_pk] = set()
            booked_slots[staff_pk].add(start_time)

        # Generate time slots
        slots = []
        time_slots = generate_time_slots(DEFAULT_START_HOUR, DEFAULT_END_HOUR, DEFAULT_INTERVAL)

        # Adjust for Saturday (shorter hours)
        if target_date.weekday() == 5:  # Saturday
            time_slots = generate_time_slots(10, 18, DEFAULT_INTERVAL)

        # Current time check for today
        now = timezone.now()
        is_today = target_date == now.date()
        current_time = now.time() if is_today else None

        for i, start_time in enumerate(time_slots[:-1]):
            end_time = time_slots[i + 1]

            # Skip past times for today
            if current_time and start_time <= current_time:
                continue

            # Skip lunch break (1pm - 2pm)
            if time(13, 0) <= start_time < time(14, 0):
                continue

            # Check each staff member for availability
            for staff in staff_members:
                staff_booked = booked_slots.get(staff.pk, set())

                if start_time not in staff_booked:
                    # Check Redis lock
                    lock_key = self.get_lock_key(staff.pk, date, str(start_time))
                    if not cache.get(lock_key):
                        # Create a unique slot ID
                        slot_id = f"{staff.pk}_{date}_{start_time.strftime('%H%M')}"

                        slots.append({
                            'id': slot_id,
                            'time': start_time.strftime('%H:%M'),
                            'staff_id': str(staff.pk),
                            'staff_name': staff.user.full_name if not staff_id else None,
                            'available': True
                        })

                        # If specific staff requested, only show their slots
                        if staff_id:
                            break

        return slots

    def hold_slot(
        self,
        slot_id: str,
        user_id: Union[int, str],
        duration_minutes: int = 5
    ) -> Dict:
        """
        Place a temporary hold on a slot.

        Args:
            slot_id: Slot identifier (staff_id_date_time format)
            user_id: User ID or session key
            duration_minutes: Hold duration

        Returns:
            Dict with success status and hold info
        """
        try:
            # Parse slot_id (format: staffid_YYYY-MM-DD_HHMM)
            parts = slot_id.split('_')
            if len(parts) != 3:
                return {'success': False, 'error': 'Invalid slot ID format'}

            staff_id = int(parts[0])
            date_str = parts[1]
            time_str = parts[2]

            # Format time for lock key
            formatted_time = f"{time_str[:2]}:{time_str[2:]}:00"

            lock_key = self.get_lock_key(staff_id, date_str, formatted_time)
            duration_seconds = duration_minutes * 60

            # Try to acquire lock
            if cache.add(lock_key, str(user_id), timeout=duration_seconds):
                expires_at = timezone.now() + timedelta(minutes=duration_minutes)

                # Generate hold ID
                hold_id = hashlib.md5(f"{slot_id}:{user_id}".encode()).hexdigest()[:16]

                # Store hold info in cache
                hold_key = f"hold:{hold_id}"
                cache.set(hold_key, {
                    'slot_id': slot_id,
                    'user_id': str(user_id),
                    'lock_key': lock_key
                }, timeout=duration_seconds)

                return {
                    'success': True,
                    'hold_id': hold_id,
                    'expires_at': expires_at
                }
            else:
                return {'success': False, 'error': 'Slot is no longer available'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def release_hold(self, hold_id: str) -> bool:
        """
        Release a hold on a slot.

        Args:
            hold_id: Hold identifier

        Returns:
            True if successful
        """
        try:
            hold_key = f"hold:{hold_id}"
            hold_info = cache.get(hold_key)

            if hold_info:
                # Release the lock
                cache.delete(hold_info.get('lock_key', ''))
                cache.delete(hold_key)

            return True
        except Exception:
            return False

    @classmethod
    def book_appointment(
        cls,
        user,
        staff: Staff,
        service: Service,
        date: date_type,
        start_time: time,
        notes: str = '',
        special_requests: str = ''
    ) -> Optional[Appointment]:
        """
        Book an appointment atomically.
        """
        from django.db import transaction

        lock_key = cls.get_lock_key(staff.id, str(date), str(start_time))

        try:
            with transaction.atomic():
                # Check for existing appointments
                existing = Appointment.objects.filter(
                    staff=staff,
                    date=date,
                    start_time=start_time,
                    status__in=['pending', 'confirmed']
                ).exists()

                if existing:
                    return None

                # Calculate end time based on service duration
                start_datetime = datetime.combine(date, start_time)
                end_datetime = start_datetime + service.duration
                end_time = end_datetime.time()

                # Create appointment
                appointment = Appointment.objects.create(
                    customer=user,
                    staff=staff,
                    service=service,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    price=service.current_price,
                    discount=0,
                    total=service.current_price,
                    notes=notes,
                    special_requests=special_requests,
                    status='pending'
                )

                # Clear the Redis lock
                cache.delete(lock_key)

                return appointment

        except Exception as e:
            cache.delete(lock_key)
            raise e

    @classmethod
    def cancel_appointment(cls, appointment: Appointment) -> bool:
        """Cancel an appointment."""
        from django.db import transaction

        try:
            with transaction.atomic():
                appointment.status = 'cancelled'
                appointment.save()
                return True
        except Exception:
            return False

    @classmethod
    def cleanup_expired_holds(cls) -> int:
        """Clean up expired slot holds from database."""
        expired = SlotHold.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()

        for hold in expired:
            lock_key = cls.get_lock_key(
                hold.slot.staff_id,
                str(hold.slot.date),
                str(hold.slot.start_time)
            )
            cache.delete(lock_key)

        expired.delete()
        return count


def generate_time_slots(
    start_hour: int = 9,
    end_hour: int = 20,
    interval_minutes: int = 30
) -> List[time]:
    """Generate a list of time slots for a day."""
    slots = []
    current = datetime(2000, 1, 1, start_hour, 0)
    end = datetime(2000, 1, 1, end_hour, 0)

    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=interval_minutes)

    return slots


def create_staff_availability(
    staff: Staff,
    target_date: date_type,
    start_hour: int = 9,
    end_hour: int = 20,
    interval_minutes: int = 30,
    break_start: Optional[time] = None,
    break_end: Optional[time] = None
) -> List[AvailabilitySlot]:
    """Create availability slots for a staff member on a given date."""
    slots = []
    time_slots = generate_time_slots(start_hour, end_hour, interval_minutes)

    for i, start_time in enumerate(time_slots[:-1]):
        end_time = time_slots[i + 1]

        if break_start and break_end:
            if break_start <= start_time < break_end:
                continue

        slot, created = AvailabilitySlot.objects.get_or_create(
            staff=staff,
            date=target_date,
            start_time=start_time,
            defaults={'end_time': end_time, 'is_available': True}
        )

        if created:
            slots.append(slot)

    return slots
