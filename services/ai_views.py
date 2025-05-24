from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from .models import ServiceRequest, Bid, Service, Review
from .serializers import ServiceSerializer

class AIRecommendationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def suggest_bid(self, request):
        """Suggest a bid amount for a service request"""
        service_request_id = request.query_params.get('service_request_id')
        if not service_request_id:
            return Response(
                {'error': 'service_request_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service_request = ServiceRequest.objects.get(id=service_request_id)
        except ServiceRequest.DoesNotExist:
            return Response(
                {'error': 'Service request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get average bid amount for similar service requests
        similar_bids = Bid.objects.filter(
            service_request__category=service_request.category,
            status='ACCEPTED'
        ).exclude(
            service_request=service_request
        )

        if service_request.estimated_hours:
            similar_bids = similar_bids.filter(
                estimated_hours__range=[
                    service_request.estimated_hours - 2,
                    service_request.estimated_hours + 2
                ]
            )

        avg_bid = similar_bids.aggregate(Avg('amount'))['amount__avg']

        # If no similar bids, use the budget as a reference
        if not avg_bid and service_request.budget:
            avg_bid = service_request.budget

        # If still no reference, use average hourly rate in the category
        if not avg_bid:
            avg_hourly = Service.objects.filter(
                category=service_request.category,
                is_active=True
            ).aggregate(Avg('hourly_rate'))['hourly_rate__avg']

            if avg_hourly and service_request.estimated_hours:
                avg_bid = avg_hourly * service_request.estimated_hours

        if not avg_bid:
            return Response(
                {'error': 'Not enough data to make a suggestion'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Adjust based on provider rating if available
        if request.user.received_reviews.exists():
            avg_rating = request.user.received_reviews.aggregate(
                Avg('rating')
            )['rating__avg']
            
            if avg_rating:
                # Adjust bid up to 20% based on rating (4.5+ gets full 20%)
                rating_factor = min((avg_rating - 3) / 1.5, 1.0)  # 3.0 is baseline
                avg_bid *= (1 + (0.2 * rating_factor))

        return Response({
            'suggested_amount': round(avg_bid, 2),
            'confidence': 'high' if similar_bids.count() > 5 else 'medium'
        })

    @action(detail=False, methods=['get'])
    def recommend_services(self, request):
        """Recommend services based on user's history and preferences"""
        user = request.user
        
        # Get categories from user's past bookings
        if user.user_type == 'customer':
            booked_categories = user.customer_bookings.values(
                'service__category'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
        else:
            # For providers, recommend based on their expertise
            return Response(
                {'error': 'Recommendations not available for providers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommended_services = []
        
        # First, get highly rated services in user's preferred categories
        if booked_categories:
            category_ids = [item['service__category'] for item in booked_categories]
            top_rated_services = Service.objects.filter(
                category_id__in=category_ids,
                is_active=True
            ).exclude(
                bookings__customer=user  # Exclude services user has already used
            ).annotate(
                avg_rating=Avg('provider__received_reviews__rating'),
                booking_count=Count('bookings')
            ).filter(
                avg_rating__gte=4.0,
                booking_count__gte=3
            ).order_by('-avg_rating')[:5]
            
            recommended_services.extend(top_rated_services)

        # If we need more recommendations, add trending services
        if len(recommended_services) < 5:
            trending_services = Service.objects.filter(
                is_active=True
            ).exclude(
                id__in=[s.id for s in recommended_services]
            ).exclude(
                bookings__customer=user
            ).annotate(
                booking_count=Count('bookings')
            ).order_by('-booking_count')[:5-len(recommended_services)]
            
            recommended_services.extend(trending_services)

        return Response(
            ServiceSerializer(recommended_services, many=True).data
        ) 