"""
Booking URL Configuration
"""

from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Public pages
    path('', views.ServicesListView.as_view(), name='services'),
    path('service/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('staff/', views.StaffListView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),

    # Booking flow
    path('book/', views.BookingCreateView.as_view(), name='create'),
    path('book/<int:service_id>/', views.BookingCreateView.as_view(), name='create_with_service'),

    # User appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointments'),
    path('appointment/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointment/<int:pk>/cancel/', views.AppointmentCancelView.as_view(), name='appointment_cancel'),

    # API endpoints for booking JavaScript
    path('api/available-dates/', views.AvailableDatesAPIView.as_view(), name='api_available_dates'),
    path('api/available-slots/', views.AvailableSlotsAPIView.as_view(), name='api_available_slots'),
    path('api/hold-slot/', views.HoldSlotAPIView.as_view(), name='api_hold_slot'),
    path('api/release-hold/', views.ReleaseHoldAPIView.as_view(), name='api_release_hold'),
]
