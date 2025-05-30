from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import Bid
from .serializers import (
    BidListSerializer,
    BidDetailSerializer,
    BidCreateSerializer,
    BidUpdateSerializer,
    BidStatusUpdateSerializer
)
from .permissions import IsProvider, IsBidOwner, IsBidParticipant, IsBidCustomer
from bookings.serializers import BookingCreateFromBidSerializer
from ai_suggestions.models import AISuggestion

class BidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for bids - allows listing, retrieving, creating, updating, and managing bids.
    Implements role-based filtering and permissions based on user type and ownership.
    """
    queryset = Bid.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service', 'provider', 'status']
    search_fields = ['description']
    ordering_fields = ['created_at', 'amount', 'estimated_delivery_time']
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Bid.objects.none()
            
        # Staff can see all bids
        if user.is_staff:
            return Bid.objects.all()
            
        # Providers see their own bids
        if user.user_type == 'provider':
            return Bid.objects.filter(provider=user)
            
        # Customers see bids on their services
        return Bid.objects.filter(service__provider=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BidCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BidUpdateSerializer
        elif self.action == 'retrieve':
            return BidDetailSerializer
        elif self.action in ['accept', 'reject']:
            return BidStatusUpdateSerializer
        return BidListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Only providers can create bids
            return [permissions.IsAuthenticated(), IsProvider()]
        elif self.action in ['update', 'partial_update']:
            # Only the owner can update a bid
            return [permissions.IsAuthenticated(), IsBidOwner()]
        elif self.action in ['accept', 'reject']:
            # Only the customer can accept/reject bids
            return [permissions.IsAuthenticated(), IsBidCustomer()]
        elif self.action == 'retrieve':
            # Only participants can see bid details
            return [permissions.IsAuthenticated(), IsBidParticipant()]
        # List view is filtered by user role in get_queryset
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        # Set the provider to the current user
        bid = serializer.save(provider=self.request.user, status='pending')
        
        # Log AI suggestion usage if this bid is based on an AI suggestion
        ai_suggestion_id = self.request.data.get('ai_suggestion_id')
        is_ai_suggested = self.request.data.get('is_ai_suggested', False)
        
        if ai_suggestion_id and is_ai_suggested:
            try:
                from ai_suggestions.models import AISuggestion, AIFeedbackLog
                suggestion = AISuggestion.objects.get(id=ai_suggestion_id, user=self.request.user)
                
                # Mark the suggestion as used
                suggestion.mark_as_used()
                
                # Update the bid to reference the AI suggestion
                bid.is_ai_suggested = True
                bid.save(update_fields=['is_ai_suggested'])
                
                # Log this interaction
                AIFeedbackLog.objects.create(
                    user=self.request.user,
                    suggestion=suggestion,
                    interaction_type='use',
                    bid=bid,
                    interaction_data={
                        'bid_id': str(bid.id),
                        'suggested_amount': float(suggestion.suggested_amount) if suggestion.suggested_amount else None,
                        'actual_amount': float(bid.amount)
                    }
                )
            except (AISuggestion.DoesNotExist, Exception) as e:
                # Don't fail the bid creation if there's an issue with the AI suggestion logging
                print(f"Error processing AI suggestion for bid: {e}")
                pass
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a bid and create a booking from it.
        This action is only available to the customer whose service received the bid.
        """
        bid = self.get_object()
        
        # Check if bid is already accepted or rejected
        if bid.status != 'pending':
            return Response(
                {"error": f"This bid is already {bid.status} and cannot be accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create serializer with the bid ID and request data
        data = request.data.copy()
        data['bid_id'] = str(bid.id)
        
        # If booking_date not provided, set it to a reasonable future date
        if 'booking_date' not in data:
            # Set to current time + estimated delivery days
            data['booking_date'] = timezone.now() + timezone.timedelta(days=1)
            
        serializer = BookingCreateFromBidSerializer(
            data=data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            booking = serializer.save()
            return Response(
                {
                    "message": "Bid accepted and booking created successfully.",
                    "booking_id": booking.id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a bid.
        This action is only available to the customer whose service received the bid.
        """
        bid = self.get_object()
        
        # Check if bid is already accepted or rejected
        if bid.status != 'pending':
            return Response(
                {"error": f"This bid is already {bid.status} and cannot be rejected."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update bid status to rejected
        bid.status = 'rejected'
        bid.save()
        
        return Response(
            {"message": "Bid rejected successfully."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def smart_price(self, request):
        """
        Get AI-suggested pricing for a service.
        Requires a service_id parameter.
        """
        service_id = request.query_params.get('service_id')
        if not service_id:
            return Response(
                {"error": "service_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This is a placeholder for actual AI pricing logic
        # In a real implementation, you would:  
        # 1. Check if there's a cached suggestion for this service
        # 2. If not, generate a new suggestion using your AI model
        # 3. Store the suggestion in AISuggestion model
        # 4. Return the suggested price
        
        # For this example, we'll generate a mock suggestion
        suggestion = {
            "min_price": 25.00,
            "max_price": 75.00,
            "optimal_price": 50.00,
            "rationale": "Based on market rates for similar services and estimated effort required."
        }
        
        # Save this suggestion in the AISuggestion model for future reference
        ai_suggestion = AISuggestion.objects.create(
            user=request.user,
            suggestion_type='pricing',
            title=f"Price suggestion for service {service_id}",
            content={
                "price_suggestion": suggestion
            }
        )
        
        return Response(suggestion, status=status.HTTP_200_OK)
