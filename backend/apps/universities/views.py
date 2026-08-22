"""
API Views for Universities app
"""
from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Institution, Programme, ClusterGroup, ProgrammeLevel, ProgrammeOffering
from .serializers import (
    InstitutionSerializer, ProgrammeSerializer, ClusterGroupSerializer,
    ProgrammeLevelSerializer, ProgrammeOfferingSerializer,
    EligibilityRequestSerializer,
    EligibilityResponseSerializer
)
from drf_spectacular.utils import extend_schema
from .utils.eligibility_filter import get_eligible_programmes, filter_eligible_only
from .utils.points_calculator import calculate_aggregate_points

@extend_schema(tags=['Universities'])
class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Institutions to be viewed.
    WITH CACHING for list view
    """
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'location']

    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.conf import settings
        from utils.cache_utils import get_institution_cache_key
        
        # Check for search query
        search_query = request.query_params.get('search', '')
        
        # Generate cache key based on search query
        cache_key = get_institution_cache_key(search_query)
        
        # Try cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Cache miss - fetch from database
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Store in cache with appropriate TTL
        if search_query:
            cache_ttl = settings.CACHE_TTL.get('SEARCH_RESULTS', 60 * 5)
        else:
            cache_ttl = settings.CACHE_TTL.get('INSTITUTIONS', 60 * 60 * 12)
        
        cache.set(cache_key, serializer.data, cache_ttl)
        
        return Response(serializer.data)
@extend_schema(tags=['Universities'])
class ProgrammeLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProgrammeLevel.objects.all()
    serializer_class = ProgrammeLevelSerializer
@extend_schema(tags=['Universities'])
class ProgrammeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Generic Courses to be viewed and searched.
    WITH CACHING and QUERY OPTIMIZATION
    """
    queryset = Programme.objects.all()  # Required for router registration
    serializer_class = ProgrammeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'kuccps_code', 'level__name']
    
    def get_queryset(self):
        # Database query optimization
        return Programme.objects.select_related('level').prefetch_related('offerings').all()
    
    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.conf import settings
        import hashlib
        
        # Get search query
        search_query = request.query_params.get('search', '')
        
        # Generate cache key
        if search_query:
            query_hash = hashlib.md5(search_query.encode()).hexdigest()
            cache_key = f'programmes_search_{query_hash}'
            cache_ttl = settings.CACHE_TTL.get('SEARCH_RESULTS', 60 * 5)
        else:
            cache_key = 'programmes_list_all'
            cache_ttl = settings.CACHE_TTL.get('PROGRAMMES', 60 * 60 * 2)
        
        # Try cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Cache miss - fetch from database
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        cache.set(cache_key, serializer.data, cache_ttl)
        
        return Response(serializer.data)



@extend_schema(tags=['Universities'])
class ProgrammeOfferingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Specific offerings (e.g. CS at UoN).
    """
    queryset = ProgrammeOffering.objects.all()
    serializer_class = ProgrammeOfferingSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['programme__name', 'institution__name']

@extend_schema(tags=['Universities'])
class ClusterGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for cluster groups.
    WITH CACHING
    """
    queryset = ClusterGroup.objects.all()
    serializer_class = ClusterGroupSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'level__name']

    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.conf import settings
        from utils.cache_utils import get_cluster_cache_key
        
        # Try cache
        cache_key = get_cluster_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        # Cache miss
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        cache_ttl = settings.CACHE_TTL.get('CLUSTERS', 60 * 60 * 24)
        cache.set(cache_key, serializer.data, cache_ttl)
        
        return Response(serializer.data)


# ============================================================================
# Custom API Views for Eligibility Checking
# ============================================================================

class CheckEligibilityView(APIView):
    """
    API endpoint to check student eligibility for university programmes.
    
    Given a student's KCSE grades, calculates cluster points and returns
    all programmes the student is eligible for based on cutoff points.
    """
    
    def post(self, request):
        """
        Check student eligibility.
        
        Request body:
        {
            "student_grades": {
                "101": "B+",    # English
                "121": "A-",    # Mathematics
                "231": "A",     # Physics
                "232": "B+",    # Biology
                ...
            },
            "target_year": 2024,        # Optional, defaults to 2024
            "level_name": "DEGREE"      # Optional, defaults to DEGREE
        }
        """
        # Validate request
        serializer = EligibilityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        student_grades = validated_data['student_grades']
        target_year = validated_data.get('target_year', 2024)
        level_name = validated_data.get('level_name', 'DEGREE')
        
        try:
            # Calculate eligibility
            all_programmes = get_eligible_programmes(
                student_grades=student_grades,
                target_year=target_year,
                level_name=level_name
            )
            
            # Get only eligible programmes (optional - client can filter)
            eligible_only = filter_eligible_only(all_programmes)
            
            # Calculate aggregate
            aggregate = calculate_aggregate_points(student_grades)
            
            # Prepare response
            response_data = {
                'total_programmes_analyzed': len(all_programmes),
                'eligible_programmes_count': len(eligible_only),
                'ineligible_programmes_count': len(all_programmes) - len(eligible_only),
                'student_aggregate': aggregate,
                'target_year': target_year,
                'level_name': level_name,
                'programmes': eligible_only  # Return only eligible programmes
            }
            
            # Serialize response
            response_serializer = EligibilityResponseSerializer(response_data)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            # Log the error in production
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating eligibility: {str(e)}", exc_info=True)
            
            return Response(
                {
                    'error': 'Failed to calculate eligibility',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckEligibilityAllView(APIView):
    """
    API endpoint to check student eligibility and return ALL programmes (eligible and ineligible).
    
    Useful for showing students where they fell short.
    """
    
    def post(self, request):
        """
        Check student eligibility and return all programmes.
        """
        # Validate request
        serializer = EligibilityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        student_grades = validated_data['student_grades']
        target_year = validated_data.get('target_year', 2024)
        level_name = validated_data.get('level_name', 'DEGREE')
        
        try:
            # Calculate eligibility
            all_programmes = get_eligible_programmes(
                student_grades=student_grades,
                target_year=target_year,
                level_name=level_name
            )
            
            eligible_only = filter_eligible_only(all_programmes)
            aggregate = calculate_aggregate_points(student_grades)
            
            # Prepare response with ALL programmes
            response_data = {
                'total_programmes_analyzed': len(all_programmes),
                'eligible_programmes_count': len(eligible_only),
                'ineligible_programmes_count': len(all_programmes) - len(eligible_only),
                'student_aggregate': aggregate,
                'target_year': target_year,
                'level_name': level_name,
                'programmes': all_programmes  # Return ALL programmes
            }
            
            # Serialize response
            response_serializer = EligibilityResponseSerializer(response_data)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating eligibility: {str(e)}", exc_info=True)
            
            return Response(
                {
                    'error': 'Failed to calculate eligibility',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )