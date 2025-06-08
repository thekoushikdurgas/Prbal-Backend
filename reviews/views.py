from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, F
from django.db import transaction
from notifications.utils import send_notification

from .models import Review, ReviewImage
from .serializers import (
    ReviewListSerializer,
    ReviewDetailSerializer,
    ReviewCreateSerializer,
    ReviewProviderResponseSerializer,
    ReviewImageSerializer
)
from .permissions import IsReviewOwner, IsReviewProvider

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reviews - allows listing, retrieving, creating, and responding to reviews.
    Users can only create reviews for their own bookings.
    Providers can only respond to reviews of their services.
    """
    queryset = Review.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service', 'client', 'provider', 'booking', 'rating']
    search_fields = ['comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']  # Most recent first by default
    
    def get_queryset(self):
        user = self.request.user
        
        # If filtering for public display, only show public reviews
        if self.request.query_params.get('public') == 'true':
            return Review.objects.filter(is_public=True)
            
        # If user is not authenticated, only show public reviews
        if not user.is_authenticated:
            return Review.objects.filter(is_public=True)
            
        # Staff can see all reviews
        if user.is_staff:
            return Review.objects.all()
            
        # Users can see public reviews and all reviews they're involved in
        return Review.objects.filter(
            Q(is_public=True) | Q(client=user) | Q(provider=user)
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReviewDetailSerializer
        elif self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'respond':
            return ReviewProviderResponseSerializer
        return ReviewListSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only the reviewer can update or delete their review
            return [permissions.IsAuthenticated(), IsReviewOwner()]
        elif self.action == 'respond':
            # Only the provider can respond to the review
            return [permissions.IsAuthenticated(), IsReviewProvider()]
        elif self.action == 'create':
            # Any authenticated user can create a review (validation happens in serializer)
            return [permissions.IsAuthenticated()]
        # For list and retrieve, we filter in get_queryset
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """Create a review and update the provider's average rating"""
        with transaction.atomic():
            # Save the review
            review = serializer.save()
            
            # Update the provider's average rating
            provider = review.provider
            self.update_provider_rating(provider)
            
            # Increment the provider's total bookings count if needed
            # This might be redundant if already done in booking completion
            if hasattr(provider, 'profile') and hasattr(provider.profile, 'total_bookings'):
                if not provider.profile.total_bookings:
                    provider.profile.total_bookings = 1
                provider.profile.save(update_fields=['total_bookings'])
            
            # Send notification to the provider about the new review
            send_notification(
                recipient=provider,
                notification_type='review_received',
                title='New Review Received',
                message=f'You received a {review.rating}-star review from {review.client.get_full_name() or review.client.username}.',
                content_object=review,
                action_url=f'/provider/reviews/{review.id}/'
            )
    
    @action(detail=True, methods=['post'], url_path='response')
    def respond(self, request, pk=None):
        """
        Add or update a provider's response to a review.
        Only the provider who received the review can respond.
        """
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                updated_review = serializer.save()
                
                # Send notification to the reviewer about the provider's response
                send_notification(
                    recipient=review.client,
                    notification_type='review_response',
                    title='Provider Responded to Your Review',
                    message=f'{review.provider.get_full_name() or review.provider.username} responded to your review for {review.service.title}.',
                    content_object=review,
                    action_url=f'/bookings/{review.booking.id}/review/'
                )
            
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def provider_summary(self, request):
        """
        Get summary of reviews for a specific provider.
        Includes average rating and count by rating value.
        """
        provider_id = request.query_params.get('provider_id')
        if not provider_id:
            return Response({
                'detail': "provider_id query parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get public reviews for this provider
        reviews = Review.objects.filter(provider_id=provider_id, is_public=True)
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Count reviews by rating
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[str(i)] = reviews.filter(rating=i).count()
        
        return Response({
            'provider_id': provider_id,
            'total_reviews': reviews.count(),
            'average_rating': round(avg_rating, 1),
            'rating_counts': rating_counts
        }, status=status.HTTP_200_OK)
    
    def update_provider_rating(self, provider):
        """
        Calculate and update the provider's average rating based on all reviews.
        This should be called whenever a review is created, updated, or deleted.
        
        Args:
            provider: The User instance for the service provider
        """
        # Get all public reviews for this provider
        reviews = Review.objects.filter(provider=provider, is_public=True)
        
        # Calculate average rating
        avg = reviews.aggregate(avg_rating=Avg('rating'))
        avg_rating = avg['avg_rating'] or 0
        
        # Update the provider's rating (assumes User model has a rating field)
        provider.rating = round(avg_rating, 2)
        provider.save(update_fields=['rating'])
        
        return provider.rating
    
    @action(detail=False, methods=['get'])
    def service_summary(self, request):
        """
        Get summary of reviews for a specific service.
        Includes average rating and count by rating value.
        """
        service_id = request.query_params.get('service_id')
        if not service_id:
            return Response({
                'detail': "service_id query parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get public reviews for this service
        reviews = Review.objects.filter(service_id=service_id, is_public=True)
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Count reviews by rating
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[str(i)] = reviews.filter(rating=i).count()
        
        return Response({
            'service_id': service_id,
            'total_reviews': reviews.count(),
            'average_rating': round(avg_rating, 1),
            'rating_counts': rating_counts
        }, status=status.HTTP_200_OK)
