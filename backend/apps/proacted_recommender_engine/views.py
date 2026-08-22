from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.rate_limit import rate_limit


# Assuming these are already set up in your project
from embedding_service import get_embedding  # ← your new function (Cohere or OpenAI)
from db_vectors import get_all_course_vectors  # ← fetches from Postgres: list of (course_id, vector)
from langgraph_workflow import run_recommendation_graph  # ← your LangGraph app
from apps.universities.utils.recommender_pipeline import RecommendationEngine
from apps.students.models import Subject
from apps.universities.models import ProgrammeOffering
from unittest.mock import MagicMock


#Mindmap: The Proacted Workflow
"""
1: Take in user input from the frontend: 
    - Subjects done and Grade (Minimum 7)
    - Personal statement (strenght description, Short term goals, Long term goals, Current Skills)
    - Practical factors/constraints (Location, Time, Budget)
    - Interests & hobbies (5 max interests/hobbies keywords (will weigh heavily on course matching), extracurricula acivities)
    - Decision Priorities: List of ordered priorities
    - Influences: Type, Influence Direction, General Path, Influence Strength, Reason for Influence, Student Alignment

-> Check if they are premium users of not. If not, assign a prompt count (Max 2 prompts).
-> If they want to upgrade, take them to becomePremium view to pay and upgrade.

2: Calculate: Overall grade & points, Overall Cluster points.
3: Find clusters they qualify for based on required subjects of that cluster (check if they have done the required subjects), Cluster points for each of the qualified cluster groups.
4: Filter subcluster programs based on subject grade requirements (check if they have done the required subjects with the required grade). -> You will have all qualified programs.
5: Use cut-off points and student's cluster points to further filter the programs. -> Now we have programs they qualify based on cutoff points (and their universities whose cut-off they qualified for).
6: With Programme + Universtiy, pass onto LLM the practical constraints, decision priorities, influences, and most important hobbies & interests to further reduce the list. The output is the refined list.

7: Generate Output: 
    FREE TIER:
    - (RANKED): COURSE NAME, UNIVERSITY, PUBLIC PRIVATE, CUTOFF POINTS (PREV. YEAR), BRIEF REASONING, ESTIMATED 2026 CUTOFF, LOCATION, APPROX ANNUAL FEES.

    PREMIUM:
    - CLUSTER OF RECOMMENDED COURSE, PROGRAM CODE, CLUSTER POINTS, QUALIFIED?, LIST OF ALL INSTITUTIONS OFFERING RECOMMENDED COURSE + CUTOFF POINTS FOR EACH, FEE COMPARISON (GVT VS SELF), CAREER PATH PREVIEW, MATCHED COURSES THEY DIDNT QUALIFY DUE TO CLUSTER REQS, PERSONALISED ACTION PLAN.
"""


# Cache course vectors if possible (load once, or use Redis)
# For production: move to app startup or use caching framework
ALL_COURSE_VECTORS = None  # Will be lazy-loaded or cached


@login_required
@require_POST
@rate_limit(key_prefix='recommendation', rate='3/h', methods=['POST'])
def recommend_courses(request):
    global ALL_COURSE_VECTORS

    # ── 1. Collect MUCH more structured user data ───────────────────────────────
    user_inputs = {
        # Core free text & interests (used for semantic search)
        "personal_statement":    ''.join(request.POST.getlist('additionalInfo')).strip(),
        "interests_hobbies":     ' '.join(request.POST.getlist('interests[]')).strip(),
        "subjects_done":         ' '.join(request.POST.getlist('subjects[]')).strip(),   # e.g. "Mathematics Alt A Chemistry Biology English Kiswahili"

        # KCSE performance - very important for cluster qualification
        "kcse_mean_grade":       request.POST.get('mean_grade', '').strip().upper(),      # e.g. "B+", "B-", "C+"
        "kcse_points":           float(request.POST.get('kcse_points', 0) or 0),           # actual cluster points if known
        "subject_grades":        request.POST.get('subject_grades', '').strip(),           # e.g. "MAT:A, ENG:B+, CHE:B, BIO:C+"

        # Practical & preference constraints
        "preferred_location":    request.POST.get('preferred_location', '').strip().lower(),  # e.g. "nairobi", "western", "coast", "any"
        "max_annual_fees_ksh":   int(request.POST.get('max_fees', 0) or 0),                 # e.g. 250000
        "program_level_preferred": request.POST.get('level', 'degree').lower(),             # degree / diploma / certificate / artisan

        # Life & career priorities (very important for LLM reasoning)
        "top_priorities":        request.POST.getlist('priorities[]'),                      # e.g. ["high_salary", "passion", "job_stability", "location"]
        "career_goals":          request.POST.get('career_goals', '').strip(),
    }

    # For semantic search we still combine main descriptive parts
    user_text_for_embedding = (
        f"{user_inputs['personal_statement']} "
        f"{user_inputs['interests_hobbies']} "
        f"{user_inputs['career_goals']} "
        f"{user_inputs['subjects_done']}"
    ).strip()

    if not user_text_for_embedding:
        return JsonResponse({"error": "Please provide some information about yourself"}, status=400)

    # ── 2. Generate embedding (same as before) ────────────────────────────────
    try:
        user_vector = get_embedding(user_text_for_embedding)
    except Exception as e:
        return JsonResponse({"error": f"Embedding service error: {str(e)}"}, status=503)

    # ── 3–4. Get top 20 (same logic) ──────────────────────────────────────────
    if ALL_COURSE_VECTORS is None:
        ALL_COURSE_VECTORS = get_all_course_vectors()  # must return richer data now!

    course_ids = [item['course_id'] for item in ALL_COURSE_VECTORS]
    course_vecs = np.array([item['vector'] for item in ALL_COURSE_VECTORS])

    similarities = cosine_similarity(user_vector.reshape(1, -1), course_vecs)[0]
    top_indices = np.argsort(similarities)[::-1][:20]

    top_20 = [ALL_COURSE_VECTORS[i] for i in top_indices]   # ← now should contain full course info!

    # ── 5. Strict KUCCPS Eligibility Filtering (New) ──────────────────────────
    try:
        # A. Mock student profile from POST data
        mock_student = MagicMock()
        mock_student.mean_grade = user_inputs['kcse_mean_grade']
        
        # B. Parse subject grades for the engine
        results = []
        subject_grades_str = str(user_inputs.get('subject_grades', ''))
        if subject_grades_str:
            # Expecting "MAT:A, ENG:B+"
            for pair in subject_grades_str.split(','):
                if ':' in pair:
                    code, grade = pair.strip().split(':')
                    res = MagicMock()
                    res.subject.code = str(code)
                    res.grade = str(grade)
                    results.append(res)
        mock_student.academic_results.all.return_value = results

        # C. Fetch full ProgrammeOffering objects for the top 20 candidates
        candidate_ids = [p['course_id'] for p in top_20]
        offerings = list(ProgrammeOffering.objects.filter(
            id__in=candidate_ids
        ).select_related('programme', 'institution', 'programme__level', 'programme__cluster').prefetch_related('programme__requirements'))

        # D. Run the Verified Eligibility Engine
        level_name = str(user_inputs.get('program_level_preferred', 'degree')).upper()
        engine = RecommendationEngine(mock_student, level_name=level_name, offerings=offerings)
        engine_results = engine.run()
        
        # E. Only pass ELIGIBLE candidates to the AI for reasoning
        eligible_candidates = [res['offering'] for res in engine_results]
        
        if not eligible_candidates:
            return JsonResponse({
                "recommendations": [], 
                "message": f"Based on your grade ({user_inputs['kcse_mean_grade']}), you are not currently eligible for {level_name} courses at these institutions. Try searching for { 'Diploma' if level_name == 'DEGREE' else 'TVET' } options instead."
            })

        # Convert back to dict format for the graph (or update graph to use objects)
        # For now, we'll keep the AI's expectation of dicts
        ai_candidates = []
        for offering in eligible_candidates:
            ai_candidates.append({
                "programme_code": offering.programme.kuccps_code,
                "course_name": offering.programme.name,
                "university": offering.institution.name,
                "latest_cutoff": 0.0, # Placeholder or fetch actual
                "level": offering.programme.level.name if offering.programme.level else level_name,
                "cost": float(offering.cost) if offering.cost else 0.0
            })

        result = run_recommendation_graph(
            user_profile=user_inputs,
            shortlisted_programs=ai_candidates,
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)