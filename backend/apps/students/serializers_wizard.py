from rest_framework import serializers

# -----------------------------------------------------------------------------
# STEP 1: KCSE Grades Validation
# -----------------------------------------------------------------------------

VALID_GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']

class KCSESubjectGradeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, allow_blank=True, required=False)
    grade = serializers.CharField(allow_blank=True, required=False) # More permissive to handle empty rows

class KCSESummarySerializer(serializers.Serializer):
    mean_grade = serializers.ChoiceField(choices=VALID_GRADES, allow_null=True, required=False)
    total_subjects = serializers.IntegerField(required=False)

class KCSEProfileSerializer(serializers.Serializer):
    subjects = KCSESubjectGradeSerializer(many=True)
    custom_subjects = serializers.ListField(child=serializers.DictField(), required=False)
    summary = KCSESummarySerializer(required=False)

    def to_internal_value(self, data):
        # Filter out empty subject rows before validation
        if 'subjects' in data and isinstance(data['subjects'], list):
            data['subjects'] = [
                s for s in data['subjects']
                if s.get('name') and str(s.get('name')).strip() and s.get('grade') and str(s.get('grade')).strip()
            ]
        return super().to_internal_value(data)

    def validate_subjects(self, value):
        """
        Enforce logical constraints:
        1. Cannot have both Math Alt A and Alt B
        """
        # Extra safety check for name existence since we made it allow_blank=True in the child
        subject_names = [str(s.get('name', '')).strip() for s in value if s.get('name')]
        
        has_math_a = any('Mathematics Alternative A' in name for name in subject_names)
        has_math_b = any('Mathematics Alternative B' in name for name in subject_names)

        if has_math_a and has_math_b:
            raise serializers.ValidationError("Invalid Subject Combination: You cannot take both Mathematics Alternative A and B.")
        
        return value

# -----------------------------------------------------------------------------
# STEP 2: Personal & Cognitive
# -----------------------------------------------------------------------------
class FlexibleStringListField(serializers.ListField):
    """
    Accepts lists of either plain strings OR objects/dicts.
    When an item is a dict, it extracts a string representation
    using 'style', 'value', 'label', or 'id' key (in that order).
    This handles cases like preferred_learning_styles sending
    {style: 'Visual', label: 'Visual Learner', description: '...'}
    """
    def to_internal_value(self, data):
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Pick the most descriptive string key available
                value = (item.get('style') or item.get('value') or
                         item.get('label') or item.get('id') or str(item))
                result.append(str(value))
            else:
                result.append(str(item))
        return result

class PersonalCognitiveSerializer(serializers.Serializer):
    self_description = serializers.CharField(max_length=5000, allow_blank=True)
    strengths = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    weaknesses = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    short_term_goals_1_3_years = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    long_term_goals_career = serializers.CharField(max_length=5000, allow_blank=True)
    current_skills = serializers.DictField(required=False)
    preferred_learning_styles = FlexibleStringListField(required=False)
    career_aspirations = FlexibleStringListField(required=False)

# -----------------------------------------------------------------------------
# STEP 3: Practical Factors
# -----------------------------------------------------------------------------
class PracticalFactorsSerializer(serializers.Serializer):
    time_hours_per_week = serializers.IntegerField(min_value=0, max_value=168, required=False)
    budget_kes_estimate = serializers.IntegerField(min_value=0, required=False)
    preferred_location = serializers.CharField(max_length=200, allow_blank=True, required=False)
    constraints_notes = serializers.CharField(max_length=1000, allow_blank=True, required=False)

# -----------------------------------------------------------------------------
# STEP 4: Interests & Exposure
# -----------------------------------------------------------------------------
class InterestsExposureSerializer(serializers.Serializer):
    interests_hobbies = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    extracurriculars = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    exposure_notes = serializers.CharField(max_length=1000, allow_blank=True, required=False)

# -----------------------------------------------------------------------------
# STEP 5: Influences
# -----------------------------------------------------------------------------
# Influences data structure in frontend (WizardManager l.54) is just an array if simple, 
# or complex object if fully implemented. Adapting to current frontend state.
class InfluenceItemSerializer(serializers.Serializer):
    # Depending on what frontend sends. Based on NewPrompt.jsx logs, it seems to be an array.
    # Allowing flexible structure for now, but validating type if possible.
    pass

# -----------------------------------------------------------------------------
# STEP 6: Decision Priorities
# -----------------------------------------------------------------------------
class PriorityItemSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=100)
    label = serializers.CharField(max_length=200)
    weight = serializers.IntegerField(min_value=0, max_value=100)

class DecisionPrioritiesSerializer(serializers.Serializer):
    mode = serializers.CharField(required=False)
    items = PriorityItemSerializer(many=True)
    total_weight = serializers.IntegerField(required=False)

    def validate(self, data):
        if data.get('mode') == 'weights':
            items = data.get('items', [])
            total = sum(item['weight'] for item in items)
            # Allow small float error margin or strict 100? Strict 100 per UI.
            if total != 100:
                raise serializers.ValidationError(f"Priorities must sum to 100%. Current sum: {total}%")
        return data

# -----------------------------------------------------------------------------
# TOP LEVEL: Student Profile Payload
# -----------------------------------------------------------------------------
class StudentProfilePayloadSerializer(serializers.Serializer):
    kcse = KCSEProfileSerializer()
    personal_cognitive = PersonalCognitiveSerializer()
    practical_factors = PracticalFactorsSerializer()
    interests_exposure = InterestsExposureSerializer()
    # Influences might be a list or dict depending on implementation
    influences = serializers.ListField(required=False) 
    decision_priorities = DecisionPrioritiesSerializer()

class WizardPayloadSerializer(serializers.Serializer):
    version = serializers.CharField(required=False)
    student_profile = StudentProfilePayloadSerializer()
    client_meta = serializers.DictField(required=False)
