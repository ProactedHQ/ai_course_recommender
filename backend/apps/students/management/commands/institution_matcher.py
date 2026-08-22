"""
Institution Name Matcher

Handles fuzzy matching of institution names from PDFs to database records.
Useful when PDF has typos or slight variations in institution names.
"""
from difflib import SequenceMatcher
from typing import Optional, List, Tuple


class InstitutionMatcher:
    """Fuzzy matching for institution names"""
    
    def __init__(self, institution_mapping: dict):
        """
        Args:
            institution_mapping: Dict of uppercase name/code -> canonical name
        """
        self.mapping = institution_mapping
        # Create list of all known names for fuzzy matching
        self.known_names = list(set(institution_mapping.values()))
    
    def find_best_match(self, query: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find best matching institution name using fuzzy matching
        
        Args:
            query: Institution name from PDF
            threshold: Minimum similarity score (0-1)
        
        Returns:
            Best matching institution name or None
        """
        if not query:
            return None
        
        query_clean = query.strip().upper()
        
        # Try exact match first
        if query_clean in self.mapping:
            return self.mapping[query_clean]
        
        # Fuzzy match
        best_match = None
        best_score = 0.0
        
        for known_name in self.known_names:
            score = SequenceMatcher(None, query.upper(), known_name.upper()).ratio()
            if score > best_score:
                best_score = score
                best_match = known_name
        
        if best_score >= threshold:
            return best_match
        
        return None
    
    def get_all_matches(self, query: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get all potential matches with scores
        
        Args:
            query: Institution name from PDF
            threshold: Minimum similarity score
        
        Returns:
            List of (institution_name, score) tuples, sorted by score descending
        """
        if not query:
            return []
        
        matches = []
        for known_name in self.known_names:
            score = SequenceMatcher(None, query.upper(), known_name.upper()).ratio()
            if score >= threshold:
                matches.append((known_name, score))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)
