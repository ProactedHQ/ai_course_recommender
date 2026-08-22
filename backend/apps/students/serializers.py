from rest_framework import serializers
from django.utils import timezone
from .models import StudentProfile, Subject, AcademicResult, StudentAttribute, CareerGoal, PromptSubmission

GRADE_POINTS = {
    'A': 12, 'A-': 11,
    'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5,
    'D+': 4, 'D': 3, 'D-': 2,
    'E': 1
}

VALID_GRADES = list(GRADE_POINTS.keys())

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'category']

class AcademicResultSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    points = serializers.IntegerField(read_only=True) # Calculated automatically

    class Meta:
        model = AcademicResult
        fields = ['id', 'subject', 'subject_name', 'grade', 'points']

    def validate_grade(self, value):
        if value not in VALID_GRADES:
            raise serializers.ValidationError(f"Invalid grade. Choices are: {', '.join(VALID_GRADES)}")
        return value

    def validate(self, data):
        # 1. Check uniqueness: Student + Subject
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if this subject already exists for the student
            # We must handle UPDATE differently (exclude current instance)
            user_profile = getattr(request.user, 'student_profile', None)
            if user_profile:
                existing = AcademicResult.objects.filter(student=user_profile, subject=data['subject'])
                if self.instance:
                    existing = existing.exclude(pk=self.instance.pk)
                
                if existing.exists():
                    raise serializers.ValidationError({"subject": "You have already added a result for this subject."})

        return data

    def create(self, validated_data):
        # Auto-calculate points
        validated_data['points'] = GRADE_POINTS.get(validated_data['grade'], 0)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Recalculate points if grade changes
        if 'grade' in validated_data:
            validated_data['points'] = GRADE_POINTS.get(validated_data['grade'], 0)
        return super().update(instance, validated_data)

class StudentAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttribute
        fields = ['id', 'attribute_type', 'name', 'weight']

    def validate_weight(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError("Weight must be between 1 and 10.")
        return value


class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerGoal
        fields = ['id', 'title', 'description']

class StudentProfileSerializer(serializers.ModelSerializer):
    academic_results = AcademicResultSerializer(many=True, read_only=True)
    attributes = StudentAttributeSerializer(many=True, read_only=True)
    career_goals = CareerGoalSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'username', 'kcse_index_number', 'kcse_year', 
            'mean_grade', 'kcse_points',
            'self_description', 'short_term_goals', 'long_term_goals',
            'time_hours_per_week', 'budget_kes_estimate', 'preferred_location',
            'constraints_notes', 'exposure_notes',
            'academic_results', 'attributes', 'career_goals'
        ]
        read_only_fields = ['user']

    def validate_kcse_year(self, value):
        current_year = timezone.now().year
        if value < 1980 or value > current_year:
            raise serializers.ValidationError(f"KCSE Year must be between 1980 and {current_year}")
        return value

    def validate_self_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("Bio must be a maximum of 500 characters.")
        return value

    def validate_mean_grade(self, value):
        if value and value not in VALID_GRADES:
             raise serializers.ValidationError(f"Invalid mean grade. Choices are: {', '.join(VALID_GRADES)}")
        return value

class PromptSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptSubmission
        fields = ['id', 'user', 'payload', 'result', 'created_at']
        read_only_fields = ['user', 'result', 'created_at']