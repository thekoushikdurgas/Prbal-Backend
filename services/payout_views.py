from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Payout, Payment, Booking
from .serializers import PayoutSerializer

class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payout.objects.filter(provider=self.request.user)

    @action(detail=False, methods=['get'])
    def available_balance(self, request):
        """Get the available balance for payout"""
        # Get total amount from completed bookings with released payments
        total_released = Payment.objects.filter(
            booking__provider=request.user,
            status='released_to_provider'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Subtract amounts already paid out or pending payout
        total_paid_or_pending = Payout.objects.filter(
            provider=request.user,
            status__in=['PENDING', 'IN_TRANSIT', 'PAID']
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        available_balance = total_released - total_paid_or_pending

        return Response({
            'available_balance': available_balance,
            'currency': 'USD'  # You might want to make this configurable
        })

    @action(detail=False, methods=['get'])
    def earnings_summary(self, request):
        """Get a summary of earnings and payouts"""
        # Get earnings for different time periods
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timezone.timedelta(days=1)).replace(day=1)

        # This month's earnings
        this_month_earnings = Payment.objects.filter(
            booking__provider=request.user,
            status='released_to_provider',
            updated_at__gte=this_month_start
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Last month's earnings
        last_month_earnings = Payment.objects.filter(
            booking__provider=request.user,
            status='released_to_provider',
            updated_at__gte=last_month_start,
            updated_at__lt=this_month_start
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # All time earnings
        all_time_earnings = Payment.objects.filter(
            booking__provider=request.user,
            status='released_to_provider'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Recent payouts
        recent_payouts = self.get_queryset().order_by('-initiated_at')[:5]

        # Pending earnings (completed but not yet released)
        pending_earnings = Payment.objects.filter(
            booking__provider=request.user,
            status='held_in_escrow'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        return Response({
            'this_month_earnings': this_month_earnings,
            'last_month_earnings': last_month_earnings,
            'all_time_earnings': all_time_earnings,
            'pending_earnings': pending_earnings,
            'recent_payouts': PayoutSerializer(recent_payouts, many=True).data,
            'currency': 'USD'
        })

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a new payout"""
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify amount is available
        available_response = self.available_balance(request)
        if float(amount) > available_response.data['available_balance']:
            return Response(
                {'error': 'Requested amount exceeds available balance'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payout record
        payout = Payout.objects.create(
            provider=request.user,
            amount=amount,
            status='PENDING'
        )

        # Here you would typically initiate the actual payout through your payment provider
        # For now, we'll just return the created payout record
        return Response(
            PayoutSerializer(payout).data,
            status=status.HTTP_201_CREATED
        ) 