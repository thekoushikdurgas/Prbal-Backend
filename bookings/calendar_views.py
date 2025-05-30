"""
Views for calendar integration functionality.
"""
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from .calendar_serializers import CalendarSyncSerializer, CalendarEventResponseSerializer
from .calendar_sync import CalendarSyncManager, CalendarSyncError

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
