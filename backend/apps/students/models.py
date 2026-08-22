from django.db import models
from django.conf import settings

class StudentProfile(models.Model): 
    """
    Extends the User model with KCSE-specific details.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    kcse_index_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    kcse_year = models.IntegerField(help_text="Year the student sat for KCSE", blank=True, null=True)
    
    # We will calculate mean grade automatically later, but good to store
    mean_grade = models.CharField(max_length=2, blank=True, null=True) # e.g., 'A', 'B+'
    kcse_points = models.FloatField(blank=True, null=True, help_text="Total cluster points")
    
    # Wizard Persistence Fields
    self_description = models.TextField(null=True, blank=True)
    short_term_goals = models.JSONField(null=True, blank=True, help_text="List of short term goals")
    long_term_goals = models.TextField(null=True, blank=True)
    time_hours_per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    budget_kes_estimate = models.PositiveIntegerField(null=True, blank=True)
    preferred_location = models.CharField(max_length=120, null=True, blank=True)
    constraints_notes = models.TextField(null=True, blank=True)
    exposure_notes = models.TextField(null=True, blank=True)
    
    updated_from_prompt_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.kcse_index_number}"

class Subject(models.Model):
    """
    Lookup table for KCSE Subjects (e.g., Math, English, Biology).
    """
    CATEGORY_CHOICES = [
        ('GP1', 'Group 1 (Compulsory)'),
        ('GP2', 'Group 2 (Sciences)'),
        ('GP3', 'Group 3 (Humanities)'),
        ('GP4', 'Group 4 (Technicals)'),
        ('GP5', 'Group 5 (Foreign Languages/Business)'),
        ('GPX', 'Other / Custom'),
    ]
    
    name = models.CharField(max_length=50) # e.g., "Mathematics Alt A"
    code = models.CharField(max_length=20, unique=True) # e.g., "101" or "CUST-..."
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.code} - {self.name}"

class AcademicResult(models.Model):
    """
    Stores the grade for a specific subject for a student.
    Crucial for calculating Cluster Points.
    """
    GRADE_CHOICES = [
        ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D+', 'D+'), ('D', 'D'), ('D-', 'D-'),
        ('E', 'E'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='academic_results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    points = models.IntegerField(default=0) # 12 for A, 11 for A-, etc. (Auto-filled via logic later)

    class Meta:
        unique_together = ('student', 'subject') # Prevent duplicate entry of same subject

    def __str__(self):
        return f"{self.student.user.username} - {self.subject.name}: {self.grade}"

class StudentAttribute(models.Model):
    """
    Smart Table: Consolidates Skills, Interests, Hobbies, and Learning Styles 
    into one table to avoid clutter.
    """
    ATTRIBUTE_TYPES = [
        ('SKILL', 'Skill'),
        ('INTEREST', 'Interest'),
        ('HOBBY', 'Hobby'),
        ('STYLE', 'Learning Style'),
        ('VALUE', 'Core Value'),
        ('SKILL_TECH', 'Technical Skill'),
        ('SKILL_SOFT', 'Soft Skill'),
        ('STRENGTH', 'Strength'),
        ('WEAKNESS', 'Weakness'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attributes')
    attribute_type = models.CharField(max_length=10, choices=ATTRIBUTE_TYPES)
    name = models.CharField(max_length=100) # e.g., "Coding", "Football", "Visual Learner"
    weight = models.IntegerField(default=5, help_text="1-10 scale of how important this is to the student")

    def __str__(self):
        return f"{self.get_attribute_type_display()}: {self.name}"

class CareerGoal(models.Model):
    """
    Specific career targets for the student.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='career_goals')
    title = models.CharField(max_length=100) # e.g., "Software Engineer"
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title

class Influence(models.Model):
    """
    External influences like Parents, Teachers, Peers.
    """
    INFLUENCER_TYPES = [
        ('parent', 'Parent/Guardian'),
        ('teacher', 'Teacher/Mentor'),
        ('friend', 'Friend/Peer'),
        ('other', 'Other'),
    ]
    path_choices = [
        ('university', 'University'),
        ('tvet', 'TVET / College'),
        ('employment', 'Employment'),
        ('business', 'Business / Entrepreneurship'),
    ]
    ALIGNMENT_CHOICES = [
        ('agree', 'Agree'),
        ('partially_agree', 'Partially Agree'),
        ('neutral', 'Neutral'),
        ('disagree_but_complying', 'Disagree but Complying'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='influences')
    influencer_type = models.CharField(max_length=20, choices=INFLUENCER_TYPES)
    direction_field = models.CharField(max_length=120, help_text="Where they are directing the student (e.g. Medicine)")
    general_path = models.CharField(max_length=20, choices=path_choices)
    strength = models.PositiveSmallIntegerField(default=1, help_text="1-4 scale")
    reason = models.CharField(max_length=50, blank=True, null=True) # advice/example/pressure/support
    student_alignment = models.CharField(max_length=30, choices=ALIGNMENT_CHOICES)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.influencer_type} -> {self.direction_field}"

class DecisionPriority(models.Model):
    """
    Weighted factors for decision making (Salary, Passion, etc.)
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='decision_priorities')
    key = models.CharField(max_length=50) # choices handled in frontend/service code or we can add choices here
    weight = models.PositiveSmallIntegerField(default=50, help_text="0-100 importance")
    order_index = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'key')

    def __str__(self):
        return f"{self.key}: {self.weight}"

class PromptSubmission(models.Model):
    """
    Stores history of user prompts (wizard data) and the AI matching results.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prompt_submissions')
    payload = models.JSONField(help_text="The full multi-step wizard data.")
    result = models.JSONField(help_text="The generated AI recommendation JSON.")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt by {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"