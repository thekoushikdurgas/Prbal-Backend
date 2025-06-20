from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from .models import Booking
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateDirectSerializer,
    BookingStatusUpdateSerializer,
    BookingRescheduleSerializer
)
from .permissions import IsBookingParticipant, CanChangeBookingStatus
from notifications.utils import send_notification
"""
Views for calendar integration functionality.
"""
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from .serializers import CalendarSyncSerializer, CalendarEventResponseSerializer
from .sync import CalendarSyncManager, CalendarSyncError

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for bookings - allows listing, retrieving, creating, and managing bookings.
    Implements role-based filtering and permissions based on user type and participation.
    """
    queryset = Booking.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service', 'customer', 'provider', 'status']
    search_fields = ['requirements', 'notes']
    ordering_fields = ['created_at', 'booking_date', 'amount']
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Booking.objects.none()
            
        # Staff can see all bookings
        if user.is_staff:
            return Booking.objects.all()
            
        # Filter by role parameter if provided
        role = self.request.query_params.get('role')
        if role == 'provider':
            return Booking.objects.filter(provider=user)
        elif role == 'customer':
            return Booking.objects.filter(customer=user)
            
        # Default: users see bookings they're part of
        return Booking.objects.filter(Q(provider=user) | Q(customer=user))
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateDirectSerializer
        elif self.action == 'retrieve':
            return BookingDetailSerializer
        elif self.action in ['update_status', 'cancel']:
            return BookingStatusUpdateSerializer
        elif self.action == 'reschedule':
            return BookingRescheduleSerializer
        return BookingListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Anyone authenticated can create a booking
            return [permissions.IsAuthenticated()]
        elif self.action in ['retrieve', 'destroy']:
            # Only participants can view or cancel their bookings
            return [permissions.IsAuthenticated(), IsBookingParticipant()]
        elif self.action == 'update_status':
            # Status updates are controlled by the CanChangeBookingStatus permission
            return [permissions.IsAuthenticated(), IsBookingParticipant(), CanChangeBookingStatus()]
        # List view is filtered by user role in get_queryset
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        # Set the customer to the current user
        serializer.save(customer=self.request.user)
    
    # Override to disable PUT/PATCH on the main endpoint
    def update(self, request, *args, **kwargs):
        return Response(
            {"error": "Use /status/ endpoint to update booking status or /cancel/ to cancel a booking."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
        
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update the status of a booking.
        This action is available to participants based on their role and the current status.
        """
        return self._update_booking_status(request, pk)
        
    @action(detail=True, methods=['put', 'patch'], url_path='status')
    def status(self, request, pk=None):
        """
        Update the status of a booking (alias for update_status).
        This endpoint provides the standard /api/v1/bookings/{id}/status/ pattern.
        """
        return self._update_booking_status(request, pk)
        
    def _update_booking_status(self, request, pk=None):
        """
        Internal method for updating booking status to avoid code duplication.
        Used by both update_status and status action methods.
        """
        booking = self.get_object()
        old_status = booking.status
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        
        if serializer.is_valid():
            with transaction.atomic():
                # The permission class CanChangeBookingStatus will validate the transition
                booking = serializer.save()
                
                # Send notifications to both parties
                new_status = booking.status
                user_role = 'provider' if request.user == booking.provider else 'customer'
                other_user = booking.customer if user_role == 'provider' else booking.provider
                
                # Status-specific notification handling
                if new_status == 'in_progress':
                    # Notify customer that service has started
                    send_notification(
                        recipient=booking.customer,
                        notification_type='booking_status_updated',
                        title='Service In Progress',
                        message=f'Your booking for {booking.service.title} is now in progress.',
                        content_object=booking,
                        action_url=f'/bookings/{booking.id}/'
                    )
                elif new_status == 'completed':
                    # Notify customer about completion and prompt for review
                    send_notification(
                        recipient=booking.customer,
                        notification_type='booking_status_updated',
                        title='Service Completed',
                        message=f'Your booking for {booking.service.title} has been marked as completed. Please leave a review!',
                        content_object=booking,
                        action_url=f'/bookings/{booking.id}/review/'
                    )
                    
                    # Update provider's booking count
                    provider = booking.provider
                    if hasattr(provider, 'profile'):
                        if not hasattr(provider.profile, 'total_bookings'):
                            provider.profile.total_bookings = 1
                        else:
                            provider.profile.total_bookings += 1
                        provider.profile.save(update_fields=['total_bookings'])
                elif new_status == 'disputed':
                    # Notify admin about dispute
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    for admin in User.objects.filter(is_staff=True, is_active=True):
                        send_notification(
                            recipient=admin,
                            notification_type='booking_status_updated',
                            title='Booking Disputed',
                            message=f'A booking ({booking.id}) has been marked as disputed by {request.user.get_full_name() or request.user.username}.',
                            content_object=booking,
                            action_url=f'/admin/bookings/booking/{booking.id}/change/'
                        )
                
                # General notification to the other party
                send_notification(
                    recipient=other_user,
                    notification_type='booking_status_updated',
                    title=f'Booking Status Updated',
                    message=f'Booking for {booking.service.title} has been updated from {old_status} to {new_status}.',
                    content_object=booking,
                    action_url=f'/bookings/{booking.id}/'
                )
            
            return Response(
                {
                    "message": f"Booking status updated to {booking.status}.",
                    "booking_id": booking.id,
                    "status": booking.status
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        This action is available to both the customer and provider.
        """
        booking = self.get_object()
        
        # Check if booking can be cancelled
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {"error": f"This booking is already {booking.status} and cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get cancellation reason and reason type
            notes = request.data.get('notes', '')
            reason_type = request.data.get('cancellation_reason', 'other')
            
            # Update booking fields
            booking.status = 'cancelled'
            booking.cancellation_reason = reason_type
            booking.cancelled_by = request.user
            booking.cancellation_date = timezone.now()
            
            if notes:
                # Append the cancellation reason to existing notes
                booking.notes = f"{booking.notes}\n\nCancellation reason: {notes}" if booking.notes else f"Cancellation reason: {notes}"
            
            booking.save()
            
            # Determine the other party to notify
            other_user = booking.provider if request.user == booking.customer else booking.customer
            
            # Send notification to the other party
            canceller_name = request.user.get_full_name() or request.user.username
            send_notification(
                recipient=other_user,
                notification_type='booking_status_updated',
                title='Booking Cancelled',
                message=f'Booking for {booking.service.title} has been cancelled by {canceller_name}.',
                content_object=booking,
                action_url=f'/bookings/{booking.id}/'
            )
        
        return Response(
            {"message": "Booking cancelled successfully."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=True, methods=['patch'])
    def reschedule(self, request, pk=None):
        """
        Reschedule a booking to a new date.
        This action is available to both the customer and provider.
        """
        booking = self.get_object()
        old_date = booking.booking_date
        serializer = self.get_serializer(booking, data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                # Save the rescheduled booking
                booking = serializer.save()
                
                # Determine the other party to notify
                other_user = booking.provider if request.user == booking.customer else booking.customer
                rescheduler_name = request.user.get_full_name() or request.user.username
                
                # Notification message details
                old_date_str = old_date.strftime('%b %d, %Y at %H:%M')
                new_date_str = booking.booking_date.strftime('%b %d, %Y at %H:%M')
                
                # Send notification to the other party
                send_notification(
                    recipient=other_user,
                    notification_type='booking_status_updated',
                    title='Booking Rescheduled',
                    message=f'Booking for {booking.service.title} has been rescheduled by {rescheduler_name} from {old_date_str} to {new_date_str}. Reason: {booking.rescheduled_reason}',
                    content_object=booking,
                    action_url=f'/bookings/{booking.id}/'
                )
                
                # Optional: Sync with calendar if integrated
                # self.sync_with_calendar(booking)
            
            return Response({
                "message": "Booking rescheduled successfully.",
                "booking_id": booking.id,
                "new_date": booking.booking_date,
                "is_rescheduled": booking.is_rescheduled,
                "rescheduled_count": booking.rescheduled_count
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def sync_with_calendar(self, booking):
        """
        Sync booking with external calendar (e.g., Google Calendar).
        This is a placeholder for calendar integration.
        """
        # If booking already has a calendar event ID, update that event
        if booking.calendar_event_id:
            # Update existing calendar event
            # In a real implementation, you would call the calendar API
            # Example pseudocode:
            # calendar_service.events().update(
            #     calendarId='primary',
            #     eventId=booking.calendar_event_id,
            #     body={
            #         'summary': f'Booking: {booking.service.title}',
            #         'start': {'dateTime': booking.booking_date.isoformat()},
            #         'end': {'dateTime': (booking.booking_date + timedelta(hours=1)).isoformat()},
            #         'description': booking.requirements
            #     }
            # ).execute()
            pass
        else:
            # Create new calendar event
            # Example pseudocode:
            # event = calendar_service.events().insert(
            #     calendarId='primary',
            #     body={
            #         'summary': f'Booking: {booking.service.title}',
            #         'start': {'dateTime': booking.booking_date.isoformat()},
            #         'end': {'dateTime': (booking.booking_date + timedelta(hours=1)).isoformat()},
            #         'description': booking.requirements,
            #         'attendees': [
            #             {'email': booking.customer.email},
            #             {'email': booking.provider.email}
            #         ]
            #     }
            # ).execute()
            # booking.calendar_event_id = event.get('id')
            # booking.save(update_fields=['calendar_event_id'])
            pass

class CalendarSyncView(views.APIView):
    """
    API endpoint for synchronizing bookings with external calendar services.
    
    Accepts POST requests with booking details and calendar provider information,
    then attempts to create or update events in the external calendar service.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = CalendarSyncSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract validated data
            booking_id = serializer.validated_data['booking_id']
            provider = serializer.validated_data['provider']
            auth_token = serializer.validated_data['auth_token']
            calendar_id = serializer.validated_data.get('calendar_id')
            
            # Prepare credentials
            credentials = {
                'auth_token': auth_token,
                'calendar_id': calendar_id,
                'create_reminder': serializer.validated_data.get('create_reminder', True),
                'reminder_minutes': serializer.validated_data.get('reminder_minutes', 30),
            }
            
            # Sync booking to calendar
            sync_manager = CalendarSyncManager(user_id=request.user.id)
            result = sync_manager.sync_booking_to_calendar(booking_id, provider, credentials)
            
            # Serialize and return the response
            response_serializer = CalendarEventResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except CalendarSyncError as e:
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f"An unexpected error occurred: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
