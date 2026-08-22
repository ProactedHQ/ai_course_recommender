"""
eligibility_engine.py - Bridge for Student KCSE eligibility checking.

Bridges the Student View logic with the robust, optimized eligibility filter
living in backend/apps/universities/utils/eligibility_filter.py.
"""

import logging
from typing import Dict, List, Any, Optional

# Standard imports for university utilities
from apps.universities.utils.eligibility_filter import (
    get_eligible_programmes as get_eligible_optimized,
    filter_eligible_only as filter_eligible_optimized
)
from apps.universities.utils.requirement_parser import normalize_subject_name
from apps.universities.utils.points_calculator import calculate_aggregate_points
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

# Grade value map used for computing mean from aggregate
_GRADE_VALUE_MAP = {
    'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
}
_POINTS_TO_GRADE = {v: k for k, v in _GRADE_VALUE_MAP.items()}

_MATH_CODES = {'121', '122', '123'}  # All Math variants
_LANG_CODES = {'101', '102'}          # English, Kiswahili

def _compute_mean_grade_from_subjects(grades: Dict[str, str]) -> str:
    """
    Compute KCSE mean grade using the 7-subject rule:
    Math (compulsory) + best language + 5 best other subjects.
    """
    try:
        grade_vals = {
            code: _GRADE_VALUE_MAP[gr]
            for code, gr in grades.items()
            if code != 'MEAN' and gr in _GRADE_VALUE_MAP
        }

        # Pick Math
        math_present = _MATH_CODES & grade_vals.keys()
        best_math = max(math_present, key=lambda c: grade_vals[c]) if math_present else None
        math_val = grade_vals.pop(best_math) if best_math else 0

        # Pick best language
        lang_present = _LANG_CODES & grade_vals.keys()
        best_lang = max(lang_present, key=lambda c: grade_vals[c]) if lang_present else None
        lang_val = grade_vals.pop(best_lang) if best_lang else 0

        # Take 5 best remaining subjects
        others = sorted(grade_vals.values(), reverse=True)[:5]

        selected = [math_val, lang_val] + others
        # Pad to 7 if fewer subjects
        while len(selected) < 7:
            selected.append(0)

        aggregate = sum(selected[:7])
        mean_val = max(1, min(12, round(aggregate / 7)))
        computed = _POINTS_TO_GRADE.get(mean_val, 'E')

        logger.info("[MEAN CALC] Subjects: %d | Aggregate: %d/84 | Mean points: %d | Grade: %s",
                    len(grades), aggregate, mean_val, computed)
        return computed

    except Exception as exc:
        logger.warning("[MEAN CALC] Failed: %s", exc, exc_info=True)
        return 'E'


# ---------------------------------------------------------------------------
# 1. Extract KCSE grades from the validated wizard payload (with Code Mapping)
# ---------------------------------------------------------------------------
def _extract_student_grades(validated_payload: dict) -> Dict[str, str]:
    """
    Parse the wizard payload and return {subject_code: grade} + MEAN key.
    MEAN is computed server-side if not provided by the frontend.
    """
    try:
        kcse = validated_payload.get('student_profile', {}).get('kcse', {})
        subjects = kcse.get('subjects', [])
        custom_subjects = kcse.get('custom_subjects', [])

        grades: Dict[str, str] = {}

        for s in subjects:
            name = str(s.get('name', '')).strip()
            grade = str(s.get('grade', '')).strip().upper()
            code = normalize_subject_name(name)
            if code and grade:
                grades[code] = grade

        for s in custom_subjects:
            name = str(s.get('name', '')).strip()
            grade = str(s.get('grade', '')).strip().upper()
            code = normalize_subject_name(name)
            if code and grade:
                grades[code] = grade

        # ---- MEAN Grade Resolution ----
        # Priority 1: Use mean_grade from payload summary if provided
        summary = kcse.get('summary', {})
        mean_from_payload = summary.get('mean_grade') if summary else None

        if mean_from_payload and str(mean_from_payload).strip().upper() in _GRADE_VALUE_MAP:
            grades['MEAN'] = str(mean_from_payload).strip().upper()
            logger.info("[GRADES] MEAN grade from payload: %s", grades['MEAN'])
        else:
            # Priority 2: Compute from subject grades (frontend doesn't send mean_grade)
            logger.info("[GRADES] mean_grade not in payload, computing from %d subjects...", len(grades))
            grades['MEAN'] = _compute_mean_grade_from_subjects(grades)

        return grades

    except Exception as exc:
        logger.warning("_extract_student_grades failed: %s", exc, exc_info=True)
        return {}



# ---------------------------------------------------------------------------
# 2. Eligibility bridge using the optimized university filter
# ---------------------------------------------------------------------------
def get_eligible_programmes(student_grades: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Calls the optimized eligibility engine and applies quality/diversity filters.
    Dynamically determines the target level based on the student's Mean Grade.
    
    STRICT RULE: Never returns fallback or ineligible results to the student.
    If truly nothing is found, returns an empty list and logs the reason clearly.
    """
    # ---- STEP 0: Identify Mean Grade & Determine Target Level ----
    mean_grade = student_grades.get('MEAN', 'E')
    grade_values = {'A':12,'A-':11,'B+':10,'B':9,'B-':8,'C+':7,'C':6,'C-':5,'D+':4,'D':3,'D-':2,'E':1}
    gv = grade_values.get(mean_grade, 1)
    
    if gv >= 7:
        target_level = 'DEGREE'
    elif gv >= 5:
        # Note: In the database, Diploma programs are often under the 'CERTIFICATE' level
        target_level = 'CERTIFICATE'
    elif gv >= 3:
        target_level = 'CRAFT'
    else:
        target_level = 'ARTISAN'

    logger.info("[ELIGIBILITY] STEP 1: Determined target level = %s", target_level)

    # ---- STEP 1: Fetch raw results for the target level ----
    try:
        raw_programmes = get_eligible_optimized(student_grades, target_year=2024, level_name=target_level)
        logger.info("[ELIGIBILITY] STEP 2: Raw results from eligibility_filter = %d programmes", len(raw_programmes))
    except Exception as exc:
        logger.error("[ELIGIBILITY] STEP 2 FAILED: eligibility_filter threw an exception: %s", exc, exc_info=True)
        return []

    # ---- STEP 2: Separate eligible from ineligible (strict - no fallback) ----
    eligible = [p for p in raw_programmes if p.get('is_eligible')]
    ineligible = [p for p in raw_programmes if not p.get('is_eligible')]

    logger.info("[ELIGIBILITY] STEP 3: Eligible=%d | Ineligible (hidden from student)=%d",
                len(eligible), len(ineligible))
    
    if ineligible:
        # Log a sample reason so developers can debug without exposing it to students
        sample = ineligible[:3]
        for p in sample:
            prog_name = p.get('programme', {})
            reason = p.get('eligibility', {}).get('reason', 'Unknown reason') if isinstance(p.get('eligibility'), dict) else 'N/A'
            logger.debug("[ELIGIBILITY] Ineligible sample: programme=%s | reason=%s", prog_name, reason)

    # STRICT: If no eligible results, do NOT fall back to ineligible data
    if not eligible:
        logger.warning(
            "[ELIGIBILITY] STEP 3: No eligible programmes found for Mean Grade %s at level %s. "
            "Returning empty list - student will see a 'no results' message.", mean_grade, target_level
        )
        return []

    # ---- STEP 3: Calculate total 7-subject aggregate for sorting ----
    from apps.universities.utils.points_calculator import calculate_aggregate_points
    total_aggregate = calculate_aggregate_points(student_grades)
    logger.info("[ELIGIBILITY] STEP 4: Student 7-subject aggregate points = %d/84", total_aggregate)

    # ---- STEP 4: Apply quality & diversity filters ----
    # Note: student_max_points was used before, but aggregate is better for sorting here
    student_max_points = max(p.get('student_points', 0) for p in eligible)
    final_results = _apply_quality_filters(eligible, student_max_points)
    logger.info("[ELIGIBILITY] STEP 5: After quality/diversity filters = %d programmes", len(final_results))

    return final_results

def _normalize_course_name(name: str) -> str:
    """Normalize course name for diversity grouping."""
    n = name.lower()
    # Remove degree prefixes
    n = re.sub(r'^(bachelor of science|bachelor of arts|bachelor of|bsc|ba|b\.)(\s+in\s+|\s+)', '', n)
    # Remove common suffixes/extras
    n = n.replace('program', '').replace('programme', '')
    n = re.sub(r'\s{2,}', ' ', n).strip()
    return n

def _apply_quality_filters(programmes: List[Dict[str, Any]], student_points: float) -> List[Dict[str, Any]]:
    """
    Groups by normalized name to ensure diversity and sorts by prestige.
    - Diversity: Max 2 offerings per course name across all universities.
    - Prestige: Favors higher cutoffs that are still within student's range.
    """
    # 1. Group by Normalized Name
    grouped = defaultdict(list)
    for p in programmes:
        course_name = p['programme'].name
        norm_name = _normalize_course_name(course_name)
        grouped[norm_name].append(p)

    diverse_list = []
    for norm_name, items in grouped.items():
        # Sort items in group by cutoff (prestige) desc
        # If multiple universities offer it, we want the most prestigious ones first
        items.sort(key=lambda x: x.get('cutoff_points', 0), reverse=True)
        # Keep top 2 from each course group to allow some choice but prevent dominance
        diverse_list.extend(items[:2])

    # 2. Final Prestige-Aware Sort
    # We want courses where Cutoff is close to Student Points (high prestige)
    # Score = Cutoff (higher is more prestigious) + tiny bonus for margin (stability)
    # A student with 45 points should see a 40 point course above a 15 point course.
    def prestige_score(p):
        cutoff = p.get('cutoff_points', 0)
        # We penalize if cutoff is "too low" compared to student points to avoid "over-qualification"
        # but only if user has high points (e.g. > 35)
        gap_penalty = 0
        if student_points > 35:
            gap = student_points - cutoff
            if gap > 15: # Very safe, perhaps "too safe"
                gap_penalty = (gap - 15) * 0.5 
        
        return cutoff - gap_penalty

    diverse_list.sort(key=prestige_score, reverse=True)
    
    return diverse_list


def filter_eligible_only(all_programmes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only the programmes where is_eligible=True."""
    return filter_eligible_optimized(all_programmes)


# ---------------------------------------------------------------------------
# 4. Serialize eligible programmes for the LLM prompt
# ---------------------------------------------------------------------------
def _serialize_programmes_for_llm(eligible_programmes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert the optimized-engine dictionaries into LLM-friendly formats.
    """
    serialized = []
    for p in eligible_programmes:
        prog = p['programme']
        inst = p['institution']
        
        serialized.append({
            'course': prog.name,
            'university': inst.name,
            'public_private': inst.institution_type,
            'level': prog.level.name if prog.level else 'DEGREE',
            'cluster': p['cluster'].name if p.get('cluster') else '',
            'location': inst.location,
            'latest_cutoff': p.get('cutoff_points'),
            'latest_year': p.get('cutoff_year'),
            'prev_cutoff': p.get('prev_cutoff_points'),
            'prev_year': p.get('prev_cutoff_year'),
            'student_cluster_points': p.get('student_points', 0),
            'programme_code': prog.kuccps_code,
        })
    return serialized


# ---------------------------------------------------------------------------
# 5. Build the user profile dict for the LLM prompt
# ---------------------------------------------------------------------------
def _build_user_profile_for_llm(
    validated_payload: dict, 
    eligibility_meta: dict,
    student_grades: Dict[str, str],
    user_tier: str = 'explorer'
) -> Dict[str, Any]:
    """
    Builds a rich profile dict for the AI Advisor, passing all 6 wizard sections.
    Uses computed mean grade from student_grades for accuracy.
    """
    sp = validated_payload.get('student_profile', {})
    pc = sp.get('personal_cognitive', {})
    pf = sp.get('practical_factors', {})
    ie = sp.get('interests_exposure', {})
    dp = sp.get('decision_priorities', {})
    kcse = sp.get('kcse', {})

    # Use the computed mean from our extraction logic
    computed_mean = student_grades.get('MEAN', 'E')
    
    # Calculate aggregate for LLM reasoning
    from apps.universities.utils.points_calculator import calculate_aggregate_points
    aggregate = calculate_aggregate_points(student_grades)

    # --- 1. ACADEMIC: Subject name -> grade map (use original names from payload) ---
    subject_grades = {}
    for s in kcse.get('subjects', []):
        name = str(s.get('name', '')).strip()
        grade = str(s.get('grade', '')).strip()
        if name and grade:
            subject_grades[name] = grade
    for s in kcse.get('custom_subjects', []):
        name = str(s.get('name', '')).strip()
        grade = str(s.get('grade', '')).strip()
        if name and grade:
            subject_grades[name] = grade

    # --- 5. INFLUENCES: Clean, skip empty notes ---
    cleaned_influences = []
    for inf in sp.get('influences', []):
        item = {
            'influencer': inf.get('influencer_type', ''),
            'direction': inf.get('direction_field', ''),
            'reason': inf.get('reason', ''),
            'student_alignment': inf.get('student_alignment', ''),
        }
        note = inf.get('notes', '').strip()
        if note:
            item['notes'] = note
        cleaned_influences.append(item)

    # --- 6. PRIORITIES: Pre-format as clean string ---
    priority_items = dp.get('items', [])
    formatted_priorities = ', '.join(
        f"{p.get('label', '')}: {p.get('weight', 0)}%"
        for p in priority_items
        if p.get('label')
    )

    return {
        # Academic
        'kcse_mean_grade': computed_mean,
        'kcse_aggregate_points': aggregate,
        'kcse_subjects': subject_grades,

        # Personal
        'self_description': pc.get('self_description', ''),
        'strengths': pc.get('strengths', []),
        'weaknesses': pc.get('weaknesses', []),
        'current_skills': pc.get('current_skills', {}),
        'career_aspirations': pc.get('career_aspirations', []),
        'long_term_goals': pc.get('long_term_goals_career', ''),
        'short_term_goals': pc.get('short_term_goals_1_3_years', []),
        'learning_styles': pc.get('preferred_learning_styles', []),

        # Practical
        'preferred_location': pf.get('preferred_location', ''),
        'budget_kes': pf.get('budget_kes_estimate'),
        'time_hours_per_week': pf.get('time_hours_per_week'),

        # Interests
        'interests_hobbies': ie.get('interests_hobbies', []),
        'extracurriculars': ie.get('extracurriculars', []),

        # Influences
        'influences': cleaned_influences,

        # Priorities (pre-formatted)
        'decision_priorities': formatted_priorities,

        # Meta
        'eligible_count': eligibility_meta.get('eligible_programmes_count', 0),
        'user_tier': user_tier,
    }

def _build_cluster_summary(eligible_programmes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract a unique list of qualifying clusters and their points.
    Scholar VVIP exclusive data.
    """
    clusters = {}
    for p in eligible_programmes:
        cluster = p.get('cluster')
        if cluster and cluster.name not in clusters:
            clusters[cluster.name] = {
                'name': cluster.name,
                'code': getattr(cluster, 'code', ''),
                'points': p.get('student_points', 0)
            }
    
    # Sort by points descending for better readability
    return sorted(clusters.values(), key=lambda x: x['points'], reverse=True)


# ---------------------------------------------------------------------------
# 6. Parse LLM output into the top_5 list
# ---------------------------------------------------------------------------
def _build_top_recommendations_from_llm(llm_result: Any) -> List[Dict[str, Any]]:
    """
    Normalizes AI recommendations for frontend consumption.
    
    Rules enforced:
    1. Canonical insight field name is 'insight'.
    2. Stamps source: 'llm' on every item.
    3. NO fabricated match scores.
    4. Canonical extraction from llm_result.
    """
    recs = []
    premium_data = []
    root_action_plan = None

    if isinstance(llm_result, dict):
        # Enforce canonical 'recommendations' key
        recs = llm_result.get('recommendations', [])
        premium_data = llm_result.get('premium_details', [])
        root_action_plan = llm_result.get('action_plan')
    elif isinstance(llm_result, list):
        recs = llm_result

    result = []
    for i, r in enumerate(recs[:10]):
        # Match premium detail by index if available
        p = premium_data[i] if i < len(premium_data) else {}
        
        # ── Field Mapping ───────────────────────────────────────────────────
        # Normalize various LLM naming quirks into our canonical 'insight' field.
        # We prioritize 'insight' as it's now explicitly in the LLM prompt.
        insight_text = (
            r.get('insight')
            or r.get('brief_reasoning')
            or r.get('explanation')
            or r.get('reason')
            or r.get('reasoning')
            or ''
        ).strip()

        # Handle trade-off if present
        trade_off = (r.get('trade_off') or r.get('tradeoff') or '').strip()
        if trade_off:
            insight_text = f"{insight_text}\n\nTrade-off: {trade_off}" if insight_text else trade_off

        # Priority: Technical data from PremiumDetails (p) is more reliable than LLM rankings (r)
        
        # Robust Cutoff Extraction
        l_cutoff = p.get('latest_cutoff') or p.get('cutoff_points') or p.get('prev_cutoff') or r.get('latest_cutoff') or r.get('cutoff_points')
        l_year = p.get('latest_year') or p.get('cutoff_year') or r.get('latest_year') or r.get('cutoff_year') or 2024
        
        p_cutoff = p.get('prev_cutoff') if (p.get('prev_cutoff') != l_cutoff) else None
        p_year = p.get('prev_year') or p.get('prev_cutoff_year')
        
        prog_code = p.get('programme_code') or r.get('programme_code') or p.get('program_code') or r.get('program_code') or ''
        
        logger.debug(f"[DEBUG MAPPING {i}] P_KEYS: {list(p.keys())}")
        logger.debug(f"[DEBUG MAPPING {i}] R_KEYS: {list(r.keys())}")
        logger.debug(f"[DEBUG MAPPING {i}] EXTRACTED: l_cutoff={l_cutoff}, l_year={l_year}, p_code={prog_code}")

        result_item = {
            'source': 'llm',
            'rank': r.get('rank', i + 1),
            'course': r.get('course') or r.get('course_name') or '',
            'university': r.get('university', ''),
            'public_private': r.get('public_private', ''),
            'level': r.get('level') or r.get('degree_level', ''),
            'location': p.get('location') or r.get('location', ''),
            
            # Dual Cutoffs - We keep 'cutoff_points' and 'cutoff_year' as primary keys for frontend compat
            'cutoff_points': l_cutoff,
            'cutoff_year': l_year,
            
            # Historical Cutoff
            'prev_cutoff': p_cutoff or r.get('prev_cutoff'),
            'prev_cutoff_year': p_year or r.get('prev_year'),
            
            # ---- Canonical Contract Field ----
            'insight': insight_text,
            # ---- Premium / Detail Fields ----
            'cluster': p.get('cluster') or r.get('cluster', ''),
            'programme_code': prog_code,
            'student_cluster_points': p.get('student_cluster_points') or r.get('student_cluster_points'),
            'action_plan': p.get('action_plan') or (root_action_plan if isinstance(root_action_plan, (str, list)) else ''),
            'career_preview': p.get('career_preview', ''),
        }
        
        result.append(result_item)
        
        # Note: 'match_score' is explicitly OMITTED to prevent fabrication.
    return result


# ---------------------------------------------------------------------------
# 7. Fallback recommendations
# ---------------------------------------------------------------------------
def _fallback_top_recommendations(eligible_programmes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fallback path when LLM produces no results.
    Uses data-driven insights (cutoff margins) instead of marketing copy.
    """
    # Sort by margin (best match = largest positive margin above cutoff)
    sorted_progs = sorted(eligible_programmes, key=lambda x: x.get('points_margin', 0), reverse=True)
    
    result = []
    for i, p in enumerate(sorted_progs[:5], start=1):
        prog = p['programme']
        inst = p['institution']
        student_pts = p.get('student_points')
        cutoff_pts = p.get('cutoff_points')

        # Build data-anchored insight string
        if student_pts is not None and cutoff_pts is not None:
            margin = round(float(student_pts) - float(cutoff_pts), 3)
            sign = '+' if margin >= 0 else ''
            insight = (
                f"Eligible: your cluster points ({student_pts}) meet the previous cutoff ({cutoff_pts}) "
                f"with a margin of {sign}{margin}. AI reasoning unavailable - ranked by cluster point feasibility."
            )
        elif cutoff_pts is not None:
            insight = (
                f"Previous cutoff: {cutoff_pts} pts. "
                "You qualify based on subject requirements. AI reasoning unavailable."
            )
        else:
            insight = (
                "Eligible based on your subject cluster requirements. "
                "Official cutoff data unavailable. AI reasoning unavailable."
            )

        result.append({
            'source': 'fallback',
            'rank': i,
            'course': prog.name,
            'university': inst.name,
            'public_private': inst.institution_type,
            'level': prog.level.name if prog.level else 'DEGREE',
            'location': inst.location,
            'cluster': p['cluster'].name if p.get('cluster') else '',
            'cutoff_points': student_pts,
            'cutoff_year': p.get('cutoff_year', 2024),
            'prev_cutoff': p.get('prev_cutoff_points'),
            'prev_cutoff_year': p.get('prev_cutoff_year'),
            # ---- Canonical Contract Field ----
            'insight': insight,
            'programme_code': prog.kuccps_code,
            'student_cluster_points': student_pts,
        })
        # Note: 'reasoning' and 'match_score' are explicitly OMITTED.
    return result
