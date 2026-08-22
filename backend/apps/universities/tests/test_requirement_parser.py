"""
Unit tests for KCSE requirement parser utility.
"""
from django.test import TestCase
from apps.universities.utils.requirement_parser import (
    normalize_subject_name,
    parse_requirement,
    parse_all_cluster_requirements,
    SUBJECT_CODE_MAP,
    CODE_TO_NAME
)
from apps.universities.models import ClusterGroup, ProgrammeLevel


class SubjectCodeMappingTests(TestCase):
    """Test subject code mapping completeness."""
    
    def test_all_31_subjects_mapped(self):
        """Verify all 31 KCSE subjects are in CODE_TO_NAME."""
        self.assertEqual(len(CODE_TO_NAME), 31, "Should have exactly 31 KCSE subjects")
    
    def test_reverse_mapping_consistency(self):
        """Verify SUBJECT_CODE_MAP and CODE_TO_NAME are consistent."""
        # Get unique codes from SUBJECT_CODE_MAP
        unique_codes = set(SUBJECT_CODE_MAP.values())
        
        # All codes in CODE_TO_NAME should be in SUBJECT_CODE_MAP
        for code in CODE_TO_NAME.keys():
            self.assertIn(code, unique_codes, f"Code {code} in CODE_TO_NAME but not in SUBJECT_CODE_MAP")


class NormalizeSubjectNameTests(TestCase):
    """Test subject name normalization."""
    
    def test_normalize_english(self):
        """Test English subject variations."""
        self.assertEqual(normalize_subject_name('ENG'), '101')
        self.assertEqual(normalize_subject_name('ENGLISH'), '101')
        self.assertEqual(normalize_subject_name('english'), '101')
    
    def test_normalize_mathematics(self):
        """Test Mathematics variations."""
        self.assertEqual(normalize_subject_name('MATH'), '121')
        self.assertEqual(normalize_subject_name('MAT'), '121')
        self.assertEqual(normalize_subject_name('MATHEMATICS'), '121')
        self.assertEqual(normalize_subject_name('MAT ALTERNATIVE A'), '121')
        self.assertEqual(normalize_subject_name('MAT ALTERNATIVE B'), '122')
    
    def test_normalize_sciences(self):
        """Test science subject normalization."""
        self.assertEqual(normalize_subject_name('PHYSICS'), '231')
        self.assertEqual(normalize_subject_name('PHY'), '231')
        self.assertEqual(normalize_subject_name('BIOLOGY'), '232')
        self.assertEqual(normalize_subject_name('BIO'), '232')
        self.assertEqual(normalize_subject_name('CHEMISTRY'), '233')
        self.assertEqual(normalize_subject_name('CHEM'), '233')
    
    def test_normalize_invalid_subject(self):
        """Test invalid subject returns None."""
        self.assertIsNone(normalize_subject_name('INVALID'))
        self.assertIsNone(normalize_subject_name('XYZ'))
    
    def test_already_normalized_code(self):
        """Test that subject codes pass through unchanged."""
        self.assertEqual(normalize_subject_name('101'), '101')
        self.assertEqual(normalize_subject_name('121'), '121')
        self.assertEqual(normalize_subject_name('231'), '231')


class ParseRequirementTests(TestCase):
    """Test requirement parsing logic."""
    
    def test_parse_none_requirement(self):
        """Test parsing empty/none requirements."""
        result = parse_requirement(None)
        self.assertEqual(result['type'], 'none')
        
        result = parse_requirement('')
        self.assertEqual(result['type'], 'none')
        
        result = parse_requirement('null')
        self.assertEqual(result['type'], 'none')
    
    def test_parse_specific_subject(self):
        """Test parsing specific subject requirements."""
        result = parse_requirement('ENG')
        self.assertEqual(result['type'], 'specific')
        self.assertEqual(result['subjects'], ['101'])
        self.assertIsNone(result['min_grade'])
    
    def test_parse_subject_with_alternatives(self):
        """Test parsing slash-separated alternatives."""
        result = parse_requirement('ENG/KIS')
        self.assertEqual(result['type'], 'specific')
        self.assertIn('101', result['subjects'])  # English
        self.assertIn('102', result['subjects'])  # Kiswahili
    
    def test_parse_subject_with_minimum_grade(self):
        """Test parsing requirements with minimum grades."""
        result = parse_requirement('ENG/KIS - B (PLAIN)')
        self.assertEqual(result['type'], 'specific')
        self.assertEqual(result['min_grade'], 'B')
        self.assertIn('101', result['subjects'])
    
    def test_parse_group_requirement(self):
        """Test parsing group-based requirements."""
        result = parse_requirement('ANY GROUP II')
        self.assertEqual(result['type'], 'group')
        self.assertIn('GP2', result['groups'])
    
    def test_parse_multiple_groups(self):
        """Test parsing multiple group alternatives."""
        result = parse_requirement('A GROUP II or a GROUP III')
        self.assertEqual(result['type'], 'group')
        self.assertIn('GP2', result['groups'])
        self.assertIn('GP3', result['groups'])
    
    def test_parse_complex_alternatives(self):
        """Test parsing complex subject alternatives."""
        result = parse_requirement('MAT ALTERNATIVE A/MAT ALTERNATIVE B')
        self.assertEqual(result['type'], 'specific')
        self.assertIn('121', result['subjects'])  # Alt A
        self.assertIn('122', result['subjects'])  # Alt B


class ParseClusterRequirementsTests(TestCase):
    """Test parsing cluster requirements from database models."""
    
    def setUp(self):
        """Create test data."""
        self.level = ProgrammeLevel.objects.create(name='DEGREE')
        self.cluster = ClusterGroup.objects.create(
            level=self.level,
            code='1',
            name='Test Cluster',
            subject_1='ENG/KIS',
            subject_2='MATH',
            subject_3='PHY/CHEM',
            subject_4='ANY GROUP II'
        )
    
    def test_parse_all_four_requirements(self):
        """Test parsing all 4 cluster requirements."""
        requirements = parse_all_cluster_requirements(self.cluster)
        
        self.assertEqual(len(requirements), 4)
        
        # Check first requirement (ENG/KIS)
        self.assertEqual(requirements[0]['type'], 'specific')
        self.assertIn('101', requirements[0]['subjects'])
        
        # Check second requirement (MATH)
        self.assertEqual(requirements[1]['type'], 'specific')
        self.assertIn('121', requirements[1]['subjects'])
        
        # Check third requirement (PHY/CHEM)
        self.assertEqual(requirements[2]['type'], 'specific')
        self.assertIn('231', requirements[2]['subjects'])
        self.assertIn('233', requirements[2]['subjects'])
        
        # Check fourth requirement (ANY GROUP II)
        self.assertEqual(requirements[3]['type'], 'group')
        self.assertIn('GP2', requirements[3]['groups'])
