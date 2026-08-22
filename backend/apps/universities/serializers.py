from rest_framework import serializers
from .models import Institution, Programme, ProgrammeOffering, ProgrammeRequirement, ClusterGroup, CutOffPoint, ProgrammeLevel

class ProgrammeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammeLevel
        fields = ['id', 'name']

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'code', 'institution_type', 'location', 'website']

class ClusterGroupSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    
    class Meta:
        model = ClusterGroup
        fields = ['id', 'level', 'level_name', 'code', 'name']

class ProgrammeRequirementSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = ProgrammeRequirement
        fields = ['subject', 'subject_name', 'subject_category', 'minimum_grade', 'is_category', 'description']

class CutOffPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutOffPoint
        fields = ['year', 'cutoff_type', 'weighted_cluster_points', 'mean_grade_cutoff', 'capacity', 'placed_students']

class ProgrammeOfferingSerializer(serializers.ModelSerializer):
    """
    Shows a generic programme offered at a specific institution
    """
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    location = serializers.CharField(source='institution.location', read_only=True)
    cutoffs = CutOffPointSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProgrammeOffering
        fields = ['id', 'institution', 'institution_name', 'location', 'cutoffs']

class ProgrammeSerializer(serializers.ModelSerializer):
    """
    Generic programme with all requirements + all offerings
    """
    level_name = serializers.CharField(source='level.name', read_only=True)
    cluster_info = ClusterGroupSerializer(source='cluster', read_only=True)
    requirements = ProgrammeRequirementSerializer(many=True, read_only=True)
    offerings = ProgrammeOfferingSerializer(many=True, read_only=True, source='programmeoffering_set')
    
    class Meta:
        model = Programme
        fields = ['id', 'kuccps_code', 'name', 'level', 'level_name', 'cluster', 'cluster_info', 
                  'description', 'job_market_demand', 'minimum_mean_grade', 'requirements', 'offerings']

# ============================================================================
# Eligibility API Serializers
# ============================================================================

class StudentGradesSerializer(serializers.Serializer):
    '''Serializer for student KCSE grades input.'''
    
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Student grades must be a dictionary of subject code: grade pairs")
        
        valid_grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']
        
        for code, grade in data.items():
            if not (isinstance(code, str) and code.isdigit() and len(code) == 3):
                raise serializers.ValidationError(
                    f"Invalid subject code '{code}'. Must be a 3-digit string (e.g., '101', '121')"
                )
            
            grade_upper = str(grade).strip().upper()
            if grade_upper not in valid_grades:
                raise serializers.ValidationError(
                    f"Invalid grade '{grade}' for subject {code}. Must be one of: {', '.join(valid_grades)}"
                )
        
        return data


class EligibilityRequestSerializer(serializers.Serializer):
    '''Request serializer for eligibility check.'''
    student_grades = StudentGradesSerializer()
    target_year = serializers.IntegerField(default=2024, min_value=2018, max_value=2030)
    level_name = serializers.ChoiceField(choices=['DEGREE', 'DIPLOMA', 'CERTIFICATE'], default='DEGREE')


class EligibleProgrammeSerializer(serializers.Serializer):
    '''Serializer for eligible programme details.'''
    programme_id = serializers.IntegerField(source='programme.id')
    programme_name = serializers.CharField(source='programme.name')
    programme_code = serializers.CharField(source='programme.kuccps_code')
    
    institution_id = serializers.IntegerField(source='institution.id')
    institution_name = serializers.CharField(source='institution.name')
    
    cluster_name = serializers.CharField(source='cluster.name')
    cluster_code = serializers.CharField(source='cluster.code')
    
    subcluster_code = serializers.CharField(source='subcluster.code')
    subcluster_name = serializers.CharField(source='subcluster.name')
    
    student_points = serializers.FloatField()
    cutoff_points = serializers.FloatField()
    cutoff_year = serializers.IntegerField()
    points_margin = serializers.FloatField()
    is_eligible = serializers.BooleanField()
    aggregate = serializers.IntegerField()
    
    cluster_subjects = serializers.SerializerMethodField()
    
    def get_cluster_subjects(self, obj):
        from .utils.requirement_parser import CODE_TO_NAME
        subjects_data = []
        for code, grade, points in obj['cluster_subjects']:
            subjects_data.append({
                'subject_code': code,
                'subject_name': CODE_TO_NAME.get(code, code),
                'grade': grade,
                'points': points
            })
        return subjects_data


class EligibilityResponseSerializer(serializers.Serializer):
    '''Response serializer for eligibility check.'''
    total_programmes_analyzed = serializers.IntegerField()
    eligible_programmes_count = serializers.IntegerField()
    ineligible_programmes_count = serializers.IntegerField()
    student_aggregate = serializers.IntegerField()
    target_year = serializers.IntegerField()
    level_name = serializers.CharField()
    programmes = EligibleProgrammeSerializer(many=True)
