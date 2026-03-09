"""
Booking Views
Services, Staff, and Appointment management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Service, ServiceCategory, Staff, AvailabilitySlot, Appointment


class BrandFilterMixin:
    """Filter querysets by current brand."""

    def get_brand(self):
        return getattr(self.request, 'brand', 'men')

    def get_template_names(self):
        brand = self.get_brand()
        base_name = self.template_name_suffix or 'list'
        return [f'{brand}/booking/{self.model.__name__.lower()}_{base_name}.html',
                f'common/booking/{self.model.__name__.lower()}_{base_name}.html']


class ServicesListView(BrandFilterMixin, ListView):
    """List all services for current brand."""
    model = Service
    context_object_name = 'services'
    template_name_suffix = 'list'

    def get_queryset(self):
        brand = self.get_brand()
        queryset = Service.objects.filter(brand=brand, is_active=True)

        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_brand()
        context['categories'] = ServiceCategory.objects.filter(brand=brand)
        context['featured_services'] = Service.objects.filter(
            brand=brand, is_active=True, is_featured=True
        )[:3]
        return context

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/booking/services.html', 'common/booking/services.html']


class ServiceDetailView(BrandFilterMixin, DetailView):
    """Service detail page."""
    model = Service
    context_object_name = 'service'
    template_name_suffix = 'detail'

    def get_queryset(self):
        brand = self.get_brand()
        return Service.objects.filter(brand=brand, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specialists'] = self.object.specialists.filter(is_active=True)
        context['related_services'] = Service.objects.filter(
            brand=self.get_brand(),
            category=self.object.category,
            is_active=True
        ).exclude(pk=self.object.pk)[:3]
        return context

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/booking/service_detail.html', 'common/booking/service_detail.html']


class StaffListView(BrandFilterMixin, ListView):
    """List all staff for current brand."""
    model = Staff
    context_object_name = 'staff_members'
    template_name_suffix = 'list'

    def get_queryset(self):
        brand = self.get_brand()
        return Staff.objects.filter(brand=brand, is_active=True).select_related('user')

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/booking/staff.html', 'common/booking/staff.html']


class StaffDetailView(BrandFilterMixin, DetailView):
    """Staff detail page."""
    model = Staff
    context_object_name = 'staff_member'
    template_name_suffix = 'detail'

    def get_queryset(self):
        brand = self.get_brand()
        return Staff.objects.filter(brand=brand, is_active=True).select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = self.object.specializations.filter(is_active=True)
        return context

    def get_template_names(self):
        brand = self.get_brand()
        return [f'{brand}/booking/staff_detail.html', 'common/booking/staff_detail.html']


class BookingCreateView(LoginRequiredMixin, TemplateView):
    """Multi-step booking creation."""

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/booking/create.html', 'common/booking/create.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = getattr(self.request, 'brand', 'men')

        context['services'] = Service.objects.filter(brand=brand, is_active=True)
        context['staff_members'] = Staff.objects.filter(brand=brand, is_active=True)

        # Pre-select service if provided
        service_id = self.kwargs.get('service_id')
        if service_id:
            context['selected_service'] = get_object_or_404(Service, pk=service_id, brand=brand)

        return context

    def post(self, request, *args, **kwargs):
        """Handle booking submission."""
        from datetime import datetime, timedelta

        service_id = request.POST.get('service')
        staff_id = request.POST.get('staff')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes', '')

        try:
            service = Service.objects.get(pk=service_id)
            staff = Staff.objects.get(pk=staff_id)

            # Parse date and time
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_str, '%H:%M').time()

            # Calculate end time based on service duration
            start_datetime = datetime.combine(booking_date, start_time)
            end_datetime = start_datetime + service.duration
            end_time = end_datetime.time()

            # Create appointment
            appointment = Appointment.objects.create(
                customer=request.user,
                staff=staff,
                service=service,
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                price=service.current_price,
                total=service.current_price,
                notes=notes,
                status='pending'
            )

            messages.success(request, 'Your appointment has been booked successfully!')
            return redirect('booking:appointment_detail', pk=appointment.pk)

        except (Service.DoesNotExist, Staff.DoesNotExist) as e:
            messages.error(request, 'Invalid service or staff selected.')
            return self.get(request, *args, **kwargs)
        except (ValueError, TypeError) as e:
            messages.error(request, 'Invalid date or time format.')
            return self.get(request, *args, **kwargs)


class AppointmentListView(LoginRequiredMixin, ListView):
    """List user's appointments."""
    model = Appointment
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        return Appointment.objects.filter(customer=self.request.user).select_related(
            'service', 'staff', 'staff__user'
        )

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/booking/appointments.html', 'common/booking/appointments.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['upcoming'] = self.get_queryset().filter(date__gte=today, status__in=['pending', 'confirmed'])
        context['past'] = self.get_queryset().filter(date__lt=today)
        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Appointment detail page."""
    model = Appointment
    context_object_name = 'appointment'

    def get_queryset(self):
        return Appointment.objects.filter(customer=self.request.user)

    def get_template_names(self):
        brand = getattr(self.request, 'brand', 'men')
        return [f'{brand}/booking/appointment_detail.html', 'common/booking/appointment_detail.html']


class AppointmentCancelView(LoginRequiredMixin, View):
    """Cancel an appointment."""

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment,
            pk=pk,
            customer=request.user
        )

        if not appointment.can_cancel:
            messages.error(request, 'This appointment cannot be cancelled.')
            return redirect('booking:appointment_detail', pk=pk)

        appointment.status = 'cancelled'
        appointment.save()

        # Release the slot
        if appointment.slot:
            appointment.slot.is_available = True
            appointment.slot.save()

        messages.success(request, 'Your appointment has been cancelled.')
        return redirect('booking:appointments')


class AvailableDatesAPIView(APIView):
    """API endpoint to get available dates for a month."""

    def get(self, request):
        from .availability import BookingService

        service_id = request.query_params.get('service')
        staff_id = request.query_params.get('staff')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not service_id:
            return Response({'success': False, 'error': 'Service ID required'}, status=400)

        try:
            month = int(month) if month else timezone.now().month
            year = int(year) if year else timezone.now().year
        except ValueError:
            return Response({'success': False, 'error': 'Invalid month or year'}, status=400)

        booking_service = BookingService()
        dates = booking_service.get_available_dates(
            service_id=service_id,
            staff_id=staff_id,
            month=month,
            year=year
        )

        return Response({
            'success': True,
            'dates': dates,
            'month': month,
            'year': year
        })


class AvailableSlotsAPIView(APIView):
    """API endpoint to get available time slots for a date."""

    def get(self, request):
        from .availability import BookingService

        service_id = request.query_params.get('service')
        staff_id = request.query_params.get('staff')
        date = request.query_params.get('date')

        if not all([service_id, date]):
            return Response({'success': False, 'error': 'Service and date required'}, status=400)

        booking_service = BookingService()
        slots = booking_service.get_available_slots(
            service_id=service_id,
            staff_id=staff_id,
            date=date
        )

        return Response({
            'success': True,
            'slots': slots,
            'date': date
        })


class HoldSlotAPIView(APIView):
    """API endpoint to hold a slot temporarily."""

    def post(self, request):
        from .availability import BookingService

        slot_id = request.data.get('slot_id')
        service_id = request.data.get('service_id')

        if not slot_id:
            return Response({'success': False, 'error': 'Slot ID required'}, status=400)

        # Get user ID or session ID for anonymous users
        user_id = request.user.id if request.user.is_authenticated else None
        session_id = request.session.session_key if not user_id else None

        if not user_id and not session_id:
            request.session.create()
            session_id = request.session.session_key

        booking_service = BookingService()
        result = booking_service.hold_slot(
            slot_id=slot_id,
            user_id=user_id or session_id,
            duration_minutes=5
        )

        if result['success']:
            return Response({
                'success': True,
                'hold_id': result['hold_id'],
                'expires_at': result['expires_at'].isoformat()
            })
        else:
            return Response({
                'success': False,
                'message': result.get('error', 'Failed to hold slot')
            }, status=400)


class ReleaseHoldAPIView(APIView):
    """API endpoint to release a held slot."""

    def post(self, request):
        from .availability import BookingService

        hold_id = request.data.get('hold_id')

        if not hold_id:
            return Response({'success': False, 'error': 'Hold ID required'}, status=400)

        booking_service = BookingService()
        result = booking_service.release_hold(hold_id)

        return Response({'success': result})
