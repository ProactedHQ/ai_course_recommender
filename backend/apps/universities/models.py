from django.db import models
from apps.students.models import Subject

class Institution(models.Model):
    """
    University or College (e.g., JKUAT, UoN, Kabete National Polytechnic).
    """
    TYPE_CHOICES = [
        ('PUBLIC_UNIVERSITY', 'Public University'),
        ('PRIVATE_UNIVERSITY', 'Private University'),
        ('TVET', 'TVET/College'),
    ]

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="KUCCPS Institution Code")
    institution_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='PUBLIC_UNIVERSITY')
    location = models.CharField(max_length=100, help_text="City or Town")
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class ProgrammeLevel(models.Model):
    """Distinguishes Degree, Diploma, Certificate, Artisan"""
    LEVEL_CHOICES = [
        ('DEGREE', 'Degree'),
        ('DIPLOMA', 'Diploma/Level 6'),
        ('CERTIFICATE', 'Certificate/Level 5'),
        ('ARTISAN', 'Artisan/Level 4'),
    ]
    name = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    
    def __str__(self):
        return self.name

class ClusterGroup(models.Model):
    """Clusters/Themes – now tied to level with subject requirements"""
    level = models.ForeignKey(ProgrammeLevel, on_delete=models.CASCADE, related_name='clusters')
    code = models.CharField(max_length=20, blank=True)  # e.g., "1" for Degree Law; blank or descriptive for TVET
    name = models.CharField(max_length=255)  # e.g., "Law" or "Business & Related"
    
    # Subject requirements for this cluster (e.g., "ENG C+", "MATH B")
    subject_1 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_2 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_3 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_4 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    
    def __str__(self):
        return f"{self.level} - {self.code or ''} {self.name}".strip()

class SubClusterGroup(models.Model):
    """Sub-clusters within a cluster (e.g., 1A, 2A, 2B, 2C) with specific subject requirements"""
    code = models.CharField(max_length=10, unique=True, help_text="e.g., '1A', '2A', '2B', '2C'")
    cluster = models.ForeignKey(
        ClusterGroup, 
        on_delete=models.CASCADE, 
        related_name='subclusters',
        help_text="Parent cluster this subcluster belongs to"
    )
    
    # Subject requirements specific to this subcluster (can be empty)
    subject_1 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_2 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_3 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    subject_4 = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'ENG C+', 'MATH B'")
    
    def __str__(self):
        return f"{self.code} - {self.cluster.name}"

class Programme(models.Model):
    """Generic Programme (the abstract course)"""
    kuccps_code = models.CharField(max_length=20, unique=True)  # Master programme code
    name = models.CharField(max_length=255)
    level = models.ForeignKey(ProgrammeLevel, on_delete=models.PROTECT, related_name='programmes')
    cluster = models.ForeignKey(ClusterGroup, on_delete=models.SET_NULL, null=True, blank=True)
    sub_cluster = models.ForeignKey(
        SubClusterGroup, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='programmes',
        help_text="Optional: specific subcluster within the cluster"
    )
    description = models.TextField(blank=True)
    
    # Job market demand (optional metadata)
    job_market_demand = models.CharField(
        max_length=20, 
        choices=[('HIGH', 'High'), ('MODERATE', 'Moderate'), ('LOW', 'Low')],
        default='MODERATE'
    )
    
    # For TVET programmes (Diploma/Certificate/Artisan)
    minimum_mean_grade = models.CharField(
        max_length=3, 
        blank=True, 
        null=True,
        help_text="Minimum mean grade for TVET programmes (e.g., C-, D+, C)"
    )
    
    def __str__(self):
        return f"{self.kuccps_code}: {self.name}"

class ProgrammeOffering(models.Model):
    """Specific offering of a programme at an institution – this is where cut-offs live"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='offerings')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='offerings')
    
    # Optional: capacity, fees, duration, etc.
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Annual tuition/programme cost in KES"
    )
    
    class Meta:
        unique_together = ('programme', 'institution')  # One offering per inst per programme
    
    def __str__(self):
        return f"{self.programme.name} at {self.institution.name}"

class ProgrammeRequirement(models.Model):
    """Subject requirements – now tied to generic Programme (same for all offerings)"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='requirements')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True, help_text="Specific subject required (e.g. Math)")
    
    # If subject is NULL, we can use a description for broader rules (e.g., "Any Group 2 Subject")
    subject_category = models.CharField(
        max_length=3, 
        choices=Subject.CATEGORY_CHOICES, 
        null=True, blank=True,
        help_text="If no specific subject, require a category (e.g. Any Group 2)"
    )
    
    minimum_grade = models.CharField(
        max_length=2, 
        choices=[('A', 'A'), ('A-', 'A-'), ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'), ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'), ('D+', 'D+'), ('D', 'D'), ('D-', 'D-')], 
        default='C+'
    )
    
    # For complex/alternative requirements
    is_category = models.BooleanField(
        default=False,
        help_text="True if requiring 'Any Group 2' or alternatives like 'ENG or KIS'"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Full requirement text for complex rules (e.g., 'ENG(101)/KIS(102):C+' or 'Any two Group II subjects')"
    )
    
    def __str__(self):
        target = self.subject.name if self.subject else (self.description or self.subject_category or "Any")
        return f"{self.programme.kuccps_code}: Requires {target} >= {self.minimum_grade}"

class CutOffPoint(models.Model):
    """Historical cut-offs – now per specific offering"""
    CUTOFF_TYPE_CHOICES = [
        ('WEIGHTED_POINTS', 'Weighted Cluster Points'),
        ('MEAN_GRADE', 'Mean Grade'),
    ]
    
    offering = models.ForeignKey(ProgrammeOffering, on_delete=models.CASCADE, related_name='cutoffs')
    year = models.IntegerField()  # e.g., 2024
    
    # For degree programmes (weighted cluster points)
    weighted_cluster_points = models.DecimalField(
        max_digits=6, decimal_places=3, 
        null=True, blank=True,
        help_text="Cut-off for degree programmes (e.g., 42.155)"
    )
    
    # For TVET programmes (mean grade)
    mean_grade_cutoff = models.CharField(
        max_length=2, 
        null=True, blank=True,
        help_text="Cut-off for TVET programmes (e.g., C-, C+)"
    )
    
    # Type indicator
    cutoff_type = models.CharField(
        max_length=20, 
        choices=CUTOFF_TYPE_CHOICES, 
        default='WEIGHTED_POINTS',
        help_text="Whether this uses weighted points or mean grade"
    )
    
    # Capacity and placement data
    capacity = models.IntegerField(null=True, blank=True, help_text="Declared slots for this offering")
    placed_students = models.IntegerField(null=True, blank=True, help_text="Number of students placed")
    
    class Meta:
        unique_together = ('offering', 'year')
        ordering = ['-year']
    
    def __str__(self):
        if self.cutoff_type == 'WEIGHTED_POINTS':
            return f"{self.offering} ({self.year}): {self.weighted_cluster_points} points"
        else:
            return f"{self.offering} ({self.year}): Mean Grade {self.mean_grade_cutoff}"

class KnowledgeNode(models.Model):
    """Represents a subject area, skill, or career outcome in the knowledge graph."""
    TYPE_CHOICES = [
        ('SUBJECT_AREA', 'Subject Area'),
        ('SKILL', 'Skill'),
        ('CAREER_OUTCOME', 'Career Outcome'),
    ]
    name = models.CharField(max_length=255, unique=True)
    node_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.node_type}] {self.name}"

class KnowledgeLink(models.Model):
    """Directed link between knowledge nodes (e.g., Mathematics -> Engineering)."""
    LINK_TYPE_CHOICES = [
        ('PREREQUISITE', 'Prerequisite For'),
        ('LEADS_TO', 'Leads To'),
        ('COMPONENT_OF', 'Component Of'),
        ('RELATED_TO', 'Related To'),
    ]
    source = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name='outgoing_links')
    target = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name='incoming_links')
    link_type = models.CharField(max_length=20, choices=LINK_TYPE_CHOICES)

    class Meta:
        unique_together = ('source', 'target', 'link_type')

    def __str__(self):
        return f"{self.source.name} --{self.link_type}--> {self.target.name}"

class ProgrammeOutcomeMapping(models.Model):
    """Maps a specific programme to its primary knowledge/career outcomes."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='outcome_mappings')
    outcome = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, limit_choices_to={'node_type': 'CAREER_OUTCOME'})

    class Meta:
        unique_together = ('programme', 'outcome')

    def __str__(self):
        return f"{self.programme.name} -> {self.outcome.name}"