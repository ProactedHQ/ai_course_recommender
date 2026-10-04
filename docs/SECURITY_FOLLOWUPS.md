# Security follow-ups (owner actions)

Open items that need a production-side action by the project owner. Developers do not need
production access for any of them. Never record credentials, emails or phone numbers here.

## SF-1 — Historical debug account `wizard_tester` (open)

**Found:** 2026-10-04, during the repository cleanup before moving to `ProactedHQ/ai_course_recommender`.

**What:** Removed debug scripts (`backend/test_initiate_payment.py`, `backend/test_prompt_workflow.py`)
created or logged in a Django user `wizard_tester` with a hard-coded password, against whatever
database `backend/.env` pointed at — at the time, production. The password and the associated
third-party email address have been scrubbed from the git history published to ProactedHQ, but
they still exist in the old personal repository's history and must be treated as exposed.

**Action (production, owner only, not yet done):**
1. In the production Django admin (or a production shell with `APP_ENV=production`), check whether a
   user named `wizard_tester` exists.
2. If it exists: delete it, or at minimum set an unusable password and deactivate it.
3. Check whether a Supabase Auth user with the same email exists in the production project and remove it
   if it was only a test account.
4. Record the outcome below.

**Outcome:** _pending_

## SF-2 — Old personal repository history (open)

`amakaluvitalis/ai-course-recommender` still contains the unscrubbed history (the debug credential above,
a third-party email address and a personal phone number). Once the ProactedHQ repository is the canonical
source, make the personal repository private or archive/delete it (owner decision).

**Outcome:** _pending_
