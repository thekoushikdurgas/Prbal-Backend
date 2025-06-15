from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from django.utils import timezone
from django.conf import settings

from .models import AISuggestion, AIFeedbackLog
from .serializers import (
    AISuggestionListSerializer,
    AISuggestionDetailSerializer,
    AISuggestionFeedbackSerializer,
    AIFeedbackLogSerializer,
    BidAmountSuggestionSerializer,
    BidMessageSuggestionSerializer
)
from .services import OpenRouterAIService
from services.models import Service
from bids.models import Bid
from decimal import Decimal
import statistics
import random


class AISuggestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AI suggestions - allows listing, retrieving, and interacting with suggestions.
    Users can only see their own suggestions.
    """
    queryset = AISuggestion.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['suggestion_type', 'status', 'is_used', 'service', 'category']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']  # Most recent first by default
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return AISuggestion.objects.none()
            
        # Staff can see all suggestions (for debugging/monitoring)
        if user.is_staff and self.request.query_params.get('all'):
            return AISuggestion.objects.all()
            
        # Users see only their own suggestions
        return AISuggestion.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AISuggestionDetailSerializer
        elif self.action == 'provide_feedback':
            return AISuggestionFeedbackSerializer
        elif self.action == 'suggest_bid_amount':
            return BidAmountSuggestionSerializer
        elif self.action == 'suggest_bid_message':
            return BidMessageSuggestionSerializer
        return AISuggestionListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Mark suggestion as viewed if it's new
        if instance.status == 'new':
            instance.mark_as_viewed()
            
            # Log this interaction
            AIFeedbackLog.objects.create(
                user=request.user,
                suggestion=instance,
                interaction_type='view'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """
        Provide feedback on an AI suggestion.
        This can include whether it was used and any comments.
        """
        suggestion = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'suggestion': suggestion}
        )
        
        if serializer.is_valid():
            feedback = serializer.validated_data['feedback']
            is_used = serializer.validated_data.get('is_used', False)
            status = serializer.validated_data.get('status', 'implemented' if is_used else 'rejected')
            
            # Update the suggestion with feedback
            suggestion.add_feedback(feedback, status=status)
            
            if is_used and not suggestion.is_used:
                suggestion.mark_as_used()
                
                # Log this interaction
                AIFeedbackLog.objects.create(
                    user=request.user,
                    suggestion=suggestion,
                    interaction_type='use',
                    interaction_data={'feedback': feedback}
                )
            else:
                # Log feedback interaction
                AIFeedbackLog.objects.create(
                    user=request.user,
                    suggestion=suggestion,
                    interaction_type='feedback',
                    interaction_data={'feedback': feedback, 'status': status}
                )
            
            return Response({
                'message': 'Feedback provided successfully.',
                'suggestion_id': suggestion.id,
                'status': suggestion.status
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_service_suggestions(self, request):
        """
        Generate AI-powered service suggestions based on user preferences and history.
        """
        # Check if AI suggestions are enabled
        if not settings.AI_SUGGESTIONS_ENABLED:
            return Response(
                {"error": "AI suggestions are currently disabled."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Get parameters from request
        user_preferences = request.data.get('preferences', {})
        category_id = request.data.get('category_id')
        max_suggestions = int(request.data.get('max_suggestions', 5))
        
        # Get user history from logs
        user_history = []
        recent_logs = AIFeedbackLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        for log in recent_logs:
            if hasattr(log, 'suggestion') and log.suggestion:
                if hasattr(log.suggestion, 'service') and log.suggestion.service:
                    item = {
                        'type': log.interaction_type,
                        'service_name': log.suggestion.service.title,
                        'timestamp': log.created_at.isoformat()
                    }
                    user_history.append(item)
        
        try:
            # Initialize the OpenRouter AI service
            ai_service = OpenRouterAIService()
            
            # Generate suggestions
            suggestions = ai_service.generate_service_suggestions(
                user_preferences=user_preferences,
                user_history=user_history,
                category_id=category_id,
                max_suggestions=max_suggestions
            )
            
            # Store suggestions in database
            saved_suggestions = []
            for suggestion in suggestions:
                ai_suggestion = AISuggestion.objects.create(
                    user=request.user,
                    suggestion_type='service_recommendation',
                    title=suggestion['title'],
                    content=suggestion,
                    category_id=category_id,
                    confidence_score=0.8  # Default confidence score
                )
                saved_suggestions.append({
                    'id': ai_suggestion.id,
                    **suggestion
                })
                
                # Log this suggestion
                AIFeedbackLog.objects.create(
                    user=request.user,
                    suggestion=ai_suggestion,
                    interaction_type='generation',
                    interaction_data={'source': 'openrouter'}
                )
            
            return Response({
                'count': len(saved_suggestions),
                'suggestions': saved_suggestions
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger('ai_suggestions')
            logger.error(f"Error generating service suggestions: {str(e)}")
            
            return Response(
                {"error": f"Failed to generate suggestions: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def suggest_bid_amount(self, request):
        """
        Get an AI-suggested bid amount for a service.
        """
        service_id = request.data.get('service_id')
        
        if not service_id:
            return Response(
                {"error": "service_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Get the service
            service = Service.objects.get(id=service_id)
            
            # Find similar bids in this category for price analysis
            similar_bids = Bid.objects.filter(
                service__category=service.category,
                status='accepted'
            ).order_by('-created_at')[:20]
            
            # Calculate suggested amount based on similar accepted bids
            if similar_bids.exists():
                # Use statistical analysis to suggest an amount
                bid_amounts = [bid.amount for bid in similar_bids]
                suggested_amount = statistics.median(bid_amounts)
            else:
                # If no similar bids, use service price as a baseline
                suggested_amount = Decimal(service.price * Decimal('0.8'))  # 80% of the service price as a starting point
            
            # Create and save the suggestion
            suggestion = AISuggestion.objects.create(
                user=request.user,
                suggestion_type='bid_amount',
                title=f"Suggested bid for {service.title}",
                content={
                    "service_id": str(service.id),
                    "service_title": service.title,
                    "suggested_amount": float(suggested_amount),
                    "rationale": "Based on analysis of similar accepted bids in this category."
                },
                suggested_amount=suggested_amount
            )
            
            # Return the suggestion
            return Response({
                "suggestion_id": suggestion.id,
                "suggested_amount": suggested_amount,
                "rationale": "Based on analysis of similar accepted bids in this category.",
                "service": {
                    "id": service.id,
                    "title": service.title
                }
            }, status=status.HTTP_200_OK)
            
        except Service.DoesNotExist:
            return Response(
                {"error": "Service not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def suggest_message(self, request):
        """Generate an AI suggested message for a bid based on service details and user preferences"""
        service_id = request.data.get('service_id')
        message_type = request.data.get('message_type', 'bid_proposal')  # Default to bid proposal
        user_preferences = request.data.get('preferences', {})  # Optional user preferences
        
        if not service_id:
            return Response(
                {"error": "service_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Get the service details
            service = Service.objects.get(pk=service_id)
            
            # Generate message based on type
            message = ""
            title = ""
            
            if message_type == 'bid_proposal':
                # Create a professional bid proposal message
                title = f"Bid proposal for {service.title}"
                tone = user_preferences.get('tone', 'professional')
                include_experience = user_preferences.get('include_experience', True)
                
                # Start with greeting
                message = "Hello! I'm interested in providing this service for you. "
                
                # Add service-specific content
                message += f"Your project '{service.title}' caught my attention because I have relevant expertise in this area. "
                
                # Add experience if requested
                if include_experience:
                    message += "I have successfully completed similar projects in the past with high client satisfaction. "
                
                # Add customization based on tone
                if tone == 'friendly':
                    message += "I'd love to discuss your specific needs in more detail and see how I can help bring your vision to life! "
                elif tone == 'professional':
                    message += "I can deliver high-quality results within your specified timeframe and would be pleased to discuss any specific requirements you may have. "
                elif tone == 'formal':
                    message += "I am confident in my ability to meet your requirements with the utmost professionalism and attention to detail. "
                
                # Closing
                message += "Looking forward to the possibility of working together."
                
            elif message_type == 'follow_up':
                # Create a follow-up message
                title = f"Follow-up message for {service.title}"
                message = "I wanted to follow up on my previous bid. I'm still very interested in working on your project and am available to answer any questions you might have. Looking forward to hearing from you!"
                
            elif message_type == 'negotiation':
                # Create a negotiation message
                title = f"Negotiation message for {service.title}"
                message = "Thank you for considering my bid. I believe we can find a solution that works for both of us. I'm flexible on the pricing and timeline and would be happy to discuss options that better fit your budget and needs."
            
            # Create and save the suggestion
            suggestion = AISuggestion.objects.create(
                user=request.user,
                suggestion_type='message',
                title=title,
                content={
                    "service_id": str(service.id),
                    "service_title": service.title,
                    "message_type": message_type,
                    "suggested_message": message,
                    "user_preferences": user_preferences
                },
                suggested_text=message
            )
            
            # Return the suggestion
            return Response({
                "suggestion_id": suggestion.id,
                "message_type": message_type,
                "suggested_message": message,
                "service": {
                    "id": service.id,
                    "title": service.title
                }
            }, status=status.HTTP_200_OK)
            
        except Service.DoesNotExist:
            return Response(
                {"error": "Service not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def suggest_bid_message(self, request):
        """
        Get an AI-suggested message template for a bid.
        This is a mock implementation for demonstration purposes.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            service_id = serializer.validated_data['service_id']
            bid_amount = serializer.validated_data['bid_amount']
            message_tone = serializer.validated_data.get('message_tone', 'professional')
            
            try:
                service = Service.objects.get(id=service_id)
                
                # Generate a template message based on the service and tone
                # In a real implementation, this would use an LLM or template system
                if message_tone == 'professional':
                    message = f"I'm pleased to offer my professional services for your {service.title} project. Based on your requirements, I can complete this work for ${bid_amount}. I have extensive experience in this field and would ensure high-quality results delivered on time."
                elif message_tone == 'friendly':
                    message = f"Hi there! I'd love to help with your {service.title} project. I can do this for ${bid_amount}, and I'm confident you'll be happy with the results. I've done similar work before and really enjoy these kinds of projects!"
                elif message_tone == 'formal':
                    message = f"I would like to formally submit my bid of ${bid_amount} for the {service.title} project. My qualifications and experience make me well-suited for this task, and I can guarantee timely delivery and professional quality."
                else:  # casual
                    message = f"Hey! I checked out your {service.title} project and I'd be up for doing it for ${bid_amount}. I've got good experience with this kind of work and would make sure it's done right."
                
                # Create an AI suggestion record
                suggestion = AISuggestion.objects.create(
                    user=request.user,
                    service=service,
                    suggestion_type='bid_message',
                    title=f"{message_tone.capitalize()} bid message for {service.title}",
                    content=message,
                    confidence_score=0.9,  # Mock confidence score
                )
                
                return Response({
                    'suggestion_id': suggestion.id,
                    'message': message,
                    'tone': message_tone,
                    'confidence_score': suggestion.confidence_score
                }, status=status.HTTP_200_OK)
                
            except Service.DoesNotExist:
                return Response({
                    'error': 'Service not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIFeedbackLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for logging AI feedback. 
    This is primarily used internally and by the frontend to log user interactions.
    """
    queryset = AIFeedbackLog.objects.all()
    serializer_class = AIFeedbackLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post', 'get']  # Only allow POST and GET
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff can see all feedback logs
        if user.is_staff:
            return AIFeedbackLog.objects.all()
            
        # Regular users only see their own logs
        return AIFeedbackLog.objects.filter(user=user)
    
    @action(detail=False, methods=['post'], url_path='log')
    def log_interaction(self, request):
        """
        Log an interaction with an AI suggestion or bid.
        This is used to track how users interact with AI features.
        """
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            interaction = serializer.save()
            
            # If this is a 'use' interaction, mark the suggestion as used
            if interaction.interaction_type == 'use' and interaction.suggestion:
                interaction.suggestion.mark_as_used()
            
            return Response({
                'message': 'Interaction logged successfully.',
                'interaction_id': interaction.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
