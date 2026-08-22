"""
Requirement Parser for KCSE Cluster/Subcluster Requirements

Parses requirement strings like:
- "ENG/KIS" → specific subjects with alternatives
- "ANY GROUP II" → any subject from group
- "ENG/KIS - B (PLAIN)" → specific subject with minimum grade
-

 "MAT ALTERNATIVE A/MAT ALTERNATIVE B/ANY GROUP II" → complex alternatives
"""

import re
from typing import Dict, List, Optional
from functools import lru_cache


# Complete subject code mapping (all 31 KCSE subjects)
SUBJECT_CODE_MAP = {
    # Group 1 - Compulsory
    'ENGLISH': '101',
    'ENG': '101',
    'KISWAHILI': '102',
    'KIS': '102',
    'MATHEMATICS ALTERNATIVE A': '121',
    'MATHEMATICS ALT A': '121',
    'MAT ALTERNATIVE A': '121',
    'MAT ALT A': '121',
    'MATHEMATICS ALTERNATIVE B': '122',
    'MATHEMATICS ALT B': '122',
    'MAT ALTERNATIVE B': '122',
    'MAT ALT B': '122',
    
    # Group 2 - Sciences
    'PHYSICS': '231',
    'PHY': '231',
    'BIOLOGY': '232',
    'BIO': '232',
    'CHEMISTRY': '233',
    'CHEM': '233',
    'CHE': '233',
    'HOME SCIENCE': '236',
    'HSC': '236',
    'AGRICULTURE': '245',
    'AGRIC': '245',
    'AGR': '245',
    'BIOLOGICAL SCIENCES': '246',
    'PHYSICAL SCIENCES': '247',
    'GENERAL SCIENCE': '247',
    'GSC': '247',
    
    # Group 3 - Humanities
    'GEOGRAPHY': '311',
    'GEO': '311',
    'HISTORY': '312',
    'HISTORY AND GOVERNMENT': '312',
    'HIST': '312',
    'HIS': '312',
    'HAG': '312',
    'CHRISTIAN RELIGIOUS EDUCATION': '313',
    'CRE': '313',
    'ISLAMIC RELIGIOUS EDUCATION': '314',
    'IRE': '314',
    'HINDU RELIGIOUS EDUCATION': '315',
    'HRE': '315',
    
    # Group 4 - Technical
    'AVIATION TECHNOLOGY': '433',
    'AVIATION': '433',
    'COMPUTER STUDIES': '440',
    'COMP': '440',
    'ELECTRICITY': '442',
    'ELEC': '442',
    'POWER MECHANICS': '443',
    'METALWORK': '444',
    'METAL': '444',
    'BUILDING CONSTRUCTION': '445',
    'CONSTRUCTION': '445',
    'WOODWORK': '446',
    'WOOD': '446',
    'DRAWING AND DESIGN': '447',
    'DRAWING': '447',
    'ART AND DESIGN': '448',
    'ART': '448',
    
    # Group 5 - Applied
    'ACCOUNTING': '511',
    'ACC': '511',
    'FRENCH': '565',
    'FRE': '565',
    'GERMAN': '566',
    'GER': '566',
    'BUSINESS STUDIES': '571',
    'BUSINESS': '571',
    'BUS': '571',
    'MUSIC': '574',
    'MUS': '574',
    'ARABIC': '579',
    'ARB': '579',
}

# Reverse mapping: code → name
CODE_TO_NAME = {
    '101': 'English',
    '102': 'Kiswahili',
    '121': 'Mathematics Alternative A',
    '122': 'Mathematics Alternative B',
    '231': 'Physics',
    '232': 'Biology',
    '233': 'Chemistry',
    '236': 'Home Science',
    '245': 'Agriculture',
    '246': 'Biological Sciences',
    '247': 'Physical Sciences',
    '311': 'Geography',
    '312': 'History and Government',
    '313': 'Christian Religious Education',
    '314': 'Islamic Religious Education',
    '315': 'Hindu Religious Education',
    '433': 'Aviation Technology',
    '440': 'Computer Studies',
    '442': 'Electricity',
    '443': 'Power Mechanics',
    '444': 'Metalwork',
    '445': 'Building Construction',
    '446': 'Woodwork',
    '447': 'Drawing and Design',
    '448': 'Art and Design',
    '511': 'Accounting',
    '565': 'French',
    '566': 'German',
    '571': 'Business Studies',
    '574': 'Music',
    '579': 'Arabic',
}


def normalize_subject_name(name: str) -> Optional[str]:
    """
    Convert subject name to standard code.
    
    Args:
        name: Subject name or code (e.g., "ENG", "MATHEMATICS", "101")
    
    Returns:
        Standard subject code (e.g., "101") or None if not found
    """
    name_upper = name.strip().upper()
    
    # Check if it's already a code
    if name_upper in CODE_TO_NAME:
        return name_upper
    
    # Look up by name
    return SUBJECT_CODE_MAP.get(name_upper)


# @lru_cache(maxsize=256)  # Temporarily disabled to test performance
def parse_requirement(req_string: Optional[str]) -> Dict:
    """
    Parse a requirement string into structured format.
    
    Examples:
        "ENG/KIS" → {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': None}
        "ENG/KIS - B (PLAIN)" → {'type': 'specific', 'subjects': ['101', '102'], 'min_grade': 'B'}
        "ANY GROUP II" → {'type': 'group', 'groups': ['GP2']}
        "A GROUP II or a GROUP III" → {'type': 'group', 'groups': ['GP2', 'GP3']}
        None or empty → {'type': 'none'}
    
    Args:
        req_string: Requirement string from database
    
    Returns:
        Dict with parsed requirement details
    """
    if not req_string or req_string.strip() == '' or str(req_string).lower() in ['null', 'none']:
        return {'type': 'none'}
    
    req_string = str(req_string).strip()
    
    # Extract minimum grade if present (e.g., "- B (PLAIN)", "- C+")
    min_grade = None
    grade_match = re.search(r'-\s*([A-E][+-]?)\s*(?:\(|PLAIN)?', req_string, re.IGNORECASE)
    if grade_match:
        min_grade = grade_match.group(1).strip()
        # Remove grade part from string
        req_string = req_string[:grade_match.start()].strip()
    
    req_upper = req_string.upper()
    
    # Check for GROUP requirements
    if 'GROUP' in req_upper:
        groups = []
        # Extract all group numbers (roman numerals or arabic)
        for match in re.finditer(r'GROUP\s+([IVX]+|[0-9]+)', req_upper):
            group_num = match.group(1)
            # Convert to GP format
            group_mapping = {
                'I': 'GP1', 'II': 'GP2', 'III': 'GP3', 
                'IV': 'GP4', 'V': 'GP5',
                '1': 'GP1', '2': 'GP2', '3': 'GP3',
                '4': 'GP4', '5': 'GP5'
            }
            if group_num in group_mapping:
                groups.append(group_mapping[group_num])
        
        if groups:
            return {
                'type': 'group',
                'groups': list(set(groups)),  # Remove duplicates
                'min_grade': min_grade
            }
    
    # Check for specific subjects (slash or 'or' separated alternatives)
    if '/' in req_string or ' OR ' in req_upper:
        # Split by slash or 'or' and normalize each
        # Using regex to split by / or " or "
        parts = re.split(r'\s*/\s*|\s+OR\s+', req_string, flags=re.IGNORECASE)
        subject_codes = []
        
        for part in parts:
            code = normalize_subject_name(part)
            if code:
                subject_codes.append(code)
            elif 'GROUP' in part.upper():
                # Mixed case: e.g., "MAT ALT A/MAT ALT B/ANY GROUP II"
                # Already handled above, but might be mixed with specific subjects
                # For now, treat this as complex - return as is
                pass
        
        if subject_codes:
            return {
                'type': 'specific',
                'subjects': subject_codes,
                'min_grade': min_grade
            }
    
    # Single specific subject
    code = normalize_subject_name(req_string)
    if code:
        return {
            'type': 'specific',
            'subjects': [code],
            'min_grade': min_grade
        }
    
    # Couldn't parse - return as text for manual handling
    return {
        'type': 'unknown',
        'raw_text': req_string,
        'min_grade': min_grade
    }


def parse_all_cluster_requirements(cluster) -> List[Dict]:
    """
    Parse all 4 subject requirements for a cluster.
    
    Args:
        cluster: ClusterGroup model instance
    
    Returns:
        List of 4 parsed requirement dicts
    """
    return [
        parse_requirement(cluster.subject_1),
        parse_requirement(cluster.subject_2),
        parse_requirement(cluster.subject_3),
        parse_requirement(cluster.subject_4),
    ]


def parse_all_subcluster_requirements(subcluster) -> List[Dict]:
    """
    Parse all 4 subject requirements for a subcluster.
    
    Args:
        subcluster: SubClusterGroup model instance
    
    Returns:
        List of 4 parsed requirement dicts
    """
    return [
        parse_requirement(subcluster.subject_1),
        parse_requirement(subcluster.subject_2),
        parse_requirement(subcluster.subject_3),
        parse_requirement(subcluster.subject_4),
    ]
