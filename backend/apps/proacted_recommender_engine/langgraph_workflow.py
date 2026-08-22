# python_scripts/langgraph_workflow.py
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import logging
import json
import re

load_dotenv()

logger = logging.getLogger(__name__)

# LLM setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_tokens=3000)

# Structured output definition
class Recommendation(BaseModel):
    rank: int = Field(..., description="Recommendation rank (1 = best)")
    course: str = Field(..., alias="course_name", description="Full name of the academic course")
    university: str = Field(...)
    public_private: str = Field(..., description="public or private")
    latest_cutoff: float = Field(..., description="Latest year cutoff points (e.g. 2024)")
    latest_year: int = Field(2024, description="The year the latest cutoff applies to")
    prev_cutoff: Optional[float] = Field(None, description="The cutoff previous to the latest one (e.g. 2023)")
    prev_year: Optional[int] = Field(None, description="The year of the previous cutoff")
    location: str = Field(..., description="University location/campus")
    level: str = Field(..., description="Degree level (e.g., DEGREE, DIPLOMA)")
    cluster: str = Field(..., description="Cluster group name")
    programme_code: str = Field(..., description="KUCCPS program code")
    insight: str = Field(..., alias="reason", description="1-2 sentences explaining why this fits (personalized)")

    class Config:
        populate_by_name = True

# Premium fields (output always, tiering handled in view)
class PremiumDetails(BaseModel):
    programme_code: str = Field(..., description="KUCCPS program code")
    student_cluster_points: float = Field(..., description="Student's estimated cluster points for this")
    latest_cutoff: float = Field(...)
    latest_year: int = Field(...)
    prev_cutoff: Optional[float] = Field(None)
    prev_year: Optional[int] = Field(None)
    qualified: bool = Field(True, description="Should be true since shortlisted")
    career_preview: str = Field(..., description="Short career path overview")
    action_plan: str = Field(..., description="A 3-5 step plan specifically for this course")

class AdvisorOutput(BaseModel):
    recommendations: List[Recommendation] = Field(..., description="LIST of 10 recommendation objects", max_items=10, min_items=10)
    premium_details: List[PremiumDetails] = Field(..., description="LIST of 10 objects, one for each recommendation in the same order")

# Batch Filter schema (for intermediate steps)
class BatchFilterOutput(BaseModel):
    candidate_program_codes: List[str] = Field(..., description="List of KUCCPS codes for top 15 candidates from this batch")

# Parsers
parser = JsonOutputParser(pydantic_object=AdvisorOutput)
batch_parser = JsonOutputParser(pydantic_object=BatchFilterOutput)

# System Prompts
BATCH_FILTER_PROMPT = """You are an expert KUCCPS placement filter. Your task is to scan a BATCH of 500 qualified programs and select the top 15 candidates that best match this student's profile.

Selection Criteria & Priorities:
1. VARIETY: Ensure the 15 candidates cover at least 5-7 distinct career domains (e.g. don't just pick 15 variations of Computer Science).
2. PRESTIGE MATCHING: If the student has high cluster points (e.g. 35+), favor competitive institutions and programs with higher cutoffs. Avoid "too safe" options that don't match the student's academic effort.
3. PERSONAL FIT: Match with priorities: {top_priorities}, interests: {interests}, and goals: {goals}.
4. KUCCPS ELIGIBILITY KNOWLEDGE:
   - Degree: Min Mean Grade C+
   - Diploma/Certificate: Min Mean Grade C-
   - Craft Certificate: Min Mean Grade D
   - Artisan Certificate: Min Mean Grade E
   Ensure you only consider programs the student is qualified for based on their Mean Grade in the profile.

Student Profile (JSON):
{user_profile}

Batch of Programs:
{batch_programs}

Output Requirements:
- Select exactly 15 candidate program codes from the list provided.
- Output ONLY valid JSON in the format: {{"candidate_program_codes": ["code1", "code2", ...]}}
- DO NOT include any comments (like // or /* */) or extra text in your JSON output.
- Ensure the result is strictly parseable as standard JSON.
"""

ADVISOR_PROMPT = """You are a trusted, realistic KUCCPS placement advisor helping Kenyan Form 4 graduates (2025/2026 intake) choose the best realistic academic pathway.

You are speaking directly to an 18-year-old student — use warm, encouraging, honest, and straightforward yet candid language. You are their guide through the complex Kenyan Higher Education landscape.

### THE KNOWLEDGE CONTEXT (Your "BRAIN")
1. HARD ELIGIBILITY: The 500+ candidate programs provided have ALREADY PASSED strict backend checks:
   - Student meets ALL 4 Cluster Subject requirements.
   - Student's KCSE Mean Grade meets level minimums (Degree: C+, Diploma: C-, Craft: D, Artisan: E).
   - Student's Cluster Points (calculated via the √((r/R)*(t/T))*48 formula) are competitive against previous years.
2. YOUR MISSION: Conduct "Deep Reasoning" to narrow these down to the TOP 10. Focus on:
   - Interest Alignment: Does the course match their hobbies/passion?
   - Practical Feasibility: Does the campus location and institution type match their reality?
   - Strategic Fit: Is this a high-prestige match or a stable fallback?

### MANDATORY STEP-BY-STEP REASONING:
1. PROFILE AUDIT: Identify the student's "North Star" (their top priority). Is it salary? Location? Passion?
2. PORTFOLIO BUILDING: Don't just recommend 10 versions of the same thing. Build a portfolio:
   - 4-5 "Ideal Matches" (High prestige, high interest).
   - 3-4 "Stable Matches" (Great fit, safe entry).
   - 1-2 "Pivot Options" (Related fields they might not have considered but qualify for).
3. RANKING: Use the ranking 1-10 to reflect this portfolio.

### MANDATORY INSIGHT FRAMEWORK:
You are writing a personal mentor message to THIS specific student — not a generic course description.
Every insight MUST address the student's actual words and actual data. If you deviate from any of their stated preferences, explicitly say why.
Use a warm, candid, direct tone — like a trusted advisor who has read their full profile.

Address every subsection below. Be specific. Quote or reference their actual values.

---

**SECTION 1 — ACADEMIC**
- kcse_subjects: Name the specific subjects and grades that directly qualify this student for this course. Which subject is the strongest match? Is there any subject they scored lower on that could be relevant?
- kcse_mean_grade: How does their overall mean grade position them competitively for this specific programme? Are they well above the cutoff, right at it, or borderline?

**SECTION 2 — PERSONAL**
- self_description: Reference something specific they said about themselves. What about their self-described character makes this a smart pick?
- strengths: Which of their listed strengths (e.g. "Problem solving", "Teamwork") are directly exercised in this career path?
- weaknesses: Acknowledge at least one weakness and explain how this particular course/environment may help them grow past it — or warn them if it could be a genuine challenge.
- long_term_goals: Does this course directly serve their 5-year vision? If yes, show the connection. If no (e.g. they want mechanical engineering but this is software), explain why this is still a worthwhile pathway.
- short_term_goals: Does this programme help them achieve any of their 1-3 year goals (scholarships, clubs, side hustle, technical skills)?

**SECTION 3 — PRACTICAL**
- preferred_location: Is this institution in or near their preferred location? If it is farther, give an honest distance estimate and what that means practically.
- budget_kes: Is this programme's estimated cost compatible with their stated budget? Flag if it likely exceeds it.
- time_hours_per_week: They have stated a study commitment of X hours/week. Is this programme's intensity realistic given that?

**SECTION 4 — INTERESTS**
- interests_hobbies: Pull out at least one specific interest (e.g. "Technology", "Health") and explain how it connects to this field.
- extracurriculars: Name a specific extracurricular they listed and connect it to a skill or quality needed in this career.

**SECTION 5 — INFLUENCES**
- influences: If there is an influencer listed, name their role (e.g. "parent", "teacher") and their stated direction (e.g. "Doctor"). Explain how this recommendation aligns with, bridges, or respectfully diverges from that advice. If the student's alignment is "neutral", acknowledge the tension directly.

**SECTION 6 — PRIORITIES**
- decision_priorities: These are given as weighted percentages. Explicitly score this recommendation against each of the student's top priorities. State directly which priorities this course serves well, which it serves moderately, and if any are a poor fit.

---

TONE RULES:
- Use "you" and "your" — speak directly to the student.
- If you deviate from any stated preference (location, career, influence), say: "I know you said X, but here's why I still recommend this..."
- Do NOT write generic phrases like "this course offers great career prospects." Be specific to THIS student.
- VVIP tier: Full paragraph per section above. Others: At least one sentence per section, covering all 6.

Student Profile:
{user_profile}

User Tier: {user_tier}

Final Candidate Programs:
{final_candidates}

### OUTPUT FORMAT:
Your response must be a SINGLE JSON object with exactly two keys:
1. "recommendations": A list of exactly {n_recommendations} objects. Each must include:
   - "rank": (1 to {n_recommendations})
   - "course": (The exact course name provided)
   - "university": (The exact institution name)
   - "location": (The location provided)
   - "insight": (Your personalized reasoning/mentor advice)
   - "programme_code": (The EXACT KUCCPS code provided)
   - [PLUS all other technical fields provided like level, cluster, latest_cutoff, etc.]
2. "premium_details": A list of {n_recommendations} objects in the same order, each containing:
   - "programme_code", "career_preview", and "action_plan".

DO NOT change the field names. DO NOT omit the programme_code.
Think like a mentor. Respond with ONLY valid JSON.
"""

# Chains
batch_chain = ChatPromptTemplate.from_template(BATCH_FILTER_PROMPT) | llm
advisor_chain = ChatPromptTemplate.from_template(ADVISOR_PROMPT) | llm


# --- Helper Functions ---

def clean_json_response(raw_text: str) -> str:
    """
    Cleans common LLM artifacts from a string to make it valid JSON.
    - Removes markdown code blocks (```json ... ```)
    - Removes // or /* */ comments
    """
    # 1. Remove markdown code blocks
    text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', raw_text, flags=re.DOTALL)
    
    # 2. Remove single-line comments //
    text = re.sub(r'//.*', '', text)
    
    # 3. Remove multi-line comments /* ... */
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    return text.strip()


# --- Graph state ---
class GraphState(TypedDict):
    user_profile: dict
    shortlisted_programs: List[Dict[str, Any]]
    batch_candidates: List[Dict[str, Any]]  # Programs selected from batches
    final_result: dict
    user_tier: str

# Nodes
def filter_batches_node(state: GraphState) -> GraphState:
    all_programs = state["shortlisted_programs"]
    batch_size = 500
    candidates = []
    
    # Process in batches
    for i in range(0, len(all_programs), batch_size):
        batch = all_programs[i : i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"PROCESSING BATCH {batch_num} ({len(batch)} programs)...")
        
        # Get top 15 from this batch
        raw_response = None
        try:
            # 1. Get raw LLM response
            ai_message = batch_chain.invoke({
                "top_priorities": state["user_profile"].get("decision_priorities", {}),
                "interests": state["user_profile"].get("interests_exposure", {}),
                "goals": state["user_profile"].get("personal_cognitive", {}).get("long_term_goals_career", ""),
                "user_profile": state["user_profile"],
                "batch_programs": batch
            })
            raw_response = ai_message.content
            
            # 2. Clean and Parse JSON
            cleaned_response = clean_json_response(raw_response)
            
            # Use json.loads first to handle potential list-only responses
            try:
                parsed_data = json.loads(cleaned_response)
                
                # If LLM returned a plain list, wrap it in our expected dict
                if isinstance(parsed_data, list):
                    batch_result = {"candidate_program_codes": parsed_data}
                else:
                    batch_result = parsed_data
                    
                # Finally, validate with the parser if needed, or just use the data
                # Since we already have the data, we can just use batch_result.get()
            except json.JSONDecodeError:
                # Fallback to the standard parser if json.loads fails (e.g. for fixing small syntax errors)
                batch_result = batch_parser.parse(cleaned_response)
            
            # Defensive handling: sometimes LLM might return a list directly instead of dict
            if isinstance(batch_result, list):
                codes = batch_result
            elif isinstance(batch_result, dict):
                codes = batch_result.get("candidate_program_codes", [])
            else:
                codes = []
                
            # Map codes back to full program objects
            found_count = 0
            for p in batch:
                if p.get("programme_code") in codes:
                    candidates.append(p)
                    found_count += 1
            logger.info(f"Added {found_count} candidates from Batch {batch_num}")
                    
        except Exception as e:
            logger.error(f"Batch {batch_num} failed!")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            if raw_response:
                logger.error(f"RAW LLM RESPONSE: {raw_response}")
            else:
                logger.error("No raw response captured (LLM call failed before returning).")
                
            # Fallback: add first 5 from batch if LLM fails completely
            fallback = batch[:5]
            candidates.extend(fallback)
            logger.warning(f"Added {len(fallback)} fallback candidates from Batch {batch_num}")
            
    state["batch_candidates"] = candidates
    logger.info(f"Total candidates collected for final reasoning: {len(candidates)}")
    return state

def advisor_node(state: GraphState) -> GraphState:
    logger.info("GENERATING FINAL RECOMMENDATIONS FROM CANDIDATES...")
    raw_response = None
    try:
        # Dynamically set N based on actual candidate count (cap at 10)
        candidates = state["batch_candidates"]
        n_recs = min(10, max(1, len(candidates)))
        logger.info("[ADVISOR] Requesting %d recommendations from %d candidates.", n_recs, len(candidates))

        # 1. Get raw LLM response
        ai_message = advisor_chain.invoke({
            "user_profile": state["user_profile"],
            "user_tier": state["user_tier"],
            "final_candidates": candidates,
            "n_recommendations": n_recs,
        })
        raw_response = ai_message.content
        
        # 2. Clean and Parse JSON
        cleaned_response = clean_json_response(raw_response)
        
        # Log raw response for debugging (truncated to 2000 chars)
        logger.info("[ADVISOR RAW] LLM output (first 2000 chars):\n%s", raw_response[:2000])
        
        try:
            # First try parsing with our Pydantic schema
            result = parser.parse(cleaned_response)
        except Exception:
            # Fallback to direct json loads + manual mapping if schema fails
            logger.warning("Pydantic parsing failed, attempting manual JSON mapping...")
            data = json.loads(cleaned_response)
            
            # Handle common key variations
            recs = data.get("recommendations") or data.get("top_programs") or data.get("top_10") or []
            premium = data.get("premium_details") or []
            
            result = {
                "recommendations": recs,
                "premium_details": premium
            }
        
        # 3. Validation: Ensure we have recommendations
        recs = result.get("recommendations", [])
        logger.info("[ADVISOR PARSED] recommendations=%d | premium_details=%d",
                    len(recs), len(result.get('premium_details', [])))
        
        if len(recs) == 0:
            logger.warning("LLM returned 0 recommendations. This will trigger a server error.")
            
        state["final_result"] = result
        logger.info("Successfully generated final recommendations.")
        
    except Exception as e:
        logger.error("Final advisor node failed!")
        logger.debug(f"Error Trace: {str(e)}", exc_info=True)
        state["final_result"] = {"recommendations": [], "premium_details": []}
        
    return state

# Graph construction
workflow = StateGraph(GraphState)
workflow.add_node("filter_batches", filter_batches_node)
workflow.add_node("advisor", advisor_node)

workflow.set_entry_point("filter_batches")
workflow.add_edge("filter_batches", "advisor")
workflow.add_edge("advisor", END)

app = workflow.compile()

def run_recommendation_graph(
    user_profile: dict,
    shortlisted_programs: List[Dict[str, Any]],
    user_tier: str = 'explorer'
) -> dict:
    initial_state = {
        "user_profile": user_profile,
        "shortlisted_programs": shortlisted_programs,
        "batch_candidates": [],
        "final_result": {},
        "user_tier": user_tier
    }
    final_state = app.invoke(initial_state)
    
    # Print a summary of final recommendations
    result = final_state.get("final_result", {})
    recs = result.get("recommendations", [])[:10]
    
    logger.info("FINAL TOP 10 RECOMMENDATIONS (RAW SUMMARY)")
    for i, r in enumerate(recs):
        # Defensive print to avoid KeyError during debug log
        course = r.get('course_name') or r.get('course') or 'Unknown Course'
        univ = r.get('university') or 'Unknown University'
        rank = r.get('rank') or (i + 1)
        # Use robust keys for debug log too
        cutoff = r.get('cutoff_points') or r.get('latest_cutoff') or r.get('prev_cutoff') or 'N/A'
        year = r.get('cutoff_year') or r.get('latest_year') or ''
        logger.info(f"Rank {rank}: {course} @ {univ} (Cutoff {year}: {cutoff})")
    
    return result
