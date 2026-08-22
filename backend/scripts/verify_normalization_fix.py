
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Django settings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
    django.setup()

from apps.students.eligibility_engine import _build_top_recommendations_from_llm

def test_normalization():
    # Problematic payload observed in logs
    problematic_llm_result = {
        'top_matches': [
            {
                'rank': 1, 
                'course': 'BACHELOR OF SCIENCE IN SOFTWARE ENGINEERING', 
                'university': 'CO-OPERATIVE UNIVERSITY OF KENYA', 
                'explanation': "This program aligns perfectly with your aspiration to become a Software Engineer..."
            },
            {
                'rank': 2, 
                'course': 'BACHELOR OF SCIENCE IN COMPUTER SCIENCE', 
                'university': 'CO-OPERATIVE UNIVERSITY OF KENYA', 
                'explanation': 'Similar to software engineering...'
            }
        ], 
        'action_plan': [
            "Research each university's application process and deadlines.", 
            "Visit the campuses if possible..."
        ]
    }

    normalized = _build_top_recommendations_from_llm(problematic_llm_result)
    
    print(f"Normalized recommendations count: {len(normalized)}")
    for rec in normalized:
        print(f"Rank {rec['rank']}: {rec['course']} @ {rec['university']}")
        print(f"  Reasoning: {rec['reasoning'][:50]}...")
        print(f"  Action Plan: {rec['action_plan'][:50]}...")
        print("-" * 20)

    # Verification checks
    assert len(normalized) == 2
    assert normalized[0]['course'] == 'BACHELOR OF SCIENCE IN SOFTWARE ENGINEERING'
    assert "Research each university" in normalized[0]['action_plan']
    print("\n✅ Verification SUCCESSFUL!")

if __name__ == "__main__":
    test_normalization()
