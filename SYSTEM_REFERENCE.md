# KeDira / Proacted AI — System Reference

How the whole system works, end to end: what runs where, every API endpoint, what each
backend function does, how the frontend talks to it, and how to deploy and troubleshoot it.
Companion to [CPANEL_HOSTING_GUIDE.md](./CPANEL_HOSTING_GUIDE.md).

Last reviewed: 2026-10-03.

---

## 1. Architecture at a glance

```
 Student browser (React SPA, proactedai.co.ke — static files on cPanel)
   │  1. Sign in with Supabase (supabase-js)  ──────────────►  Supabase Auth
   │  2. fetch(API, Authorization: Bearer <supabase access token>)
   ▼
 Django REST API (api.proactedai.co.ke — cPanel "Setup Python App", Phusion Passenger, WSGI)
   ├─ SupabaseJWTAuthentication  verifies token, maps it to a CustomUser
   ├─ Postgres (Supabase)        users, KCSE subjects, KUCCPS programmes/cutoffs, history, payments
   ├─ Redis (Upstash, optional)  cache + rate limiting; falls back to per-process memory
   ├─ OpenAI gpt-4o-mini         via LangChain/LangGraph — ranking + personalised advice
   └─ PayHero                    M-Pesa STK push; calls back /api/subscriptions/confirmation/
```

| Piece | Code | Notes |
|---|---|---|
| Frontend | `frontend/` (React 19 + Vite) | `npm run build` → upload `dist/` to `public_html` |
| Backend | `backend/` (Django 5.2, DRF) | entry point `backend/passenger_wsgi.py` |
| Settings | `backend/course_recomeder_backend/settings.py` | the live one. `dev_settings.py` / `prod_settings.py` are older variants, not loaded |
| AI | `backend/apps/proacted_recommender_engine/langgraph_workflow.py` | the only code that calls OpenAI |

**Not used in production:** WebSockets (`asgi.py`, `students/consumers.py`, `frontend/src/api/websocket.js`) — Passenger is WSGI-only.
`proacted_recommender_engine/views.py`, `embedding_service.py`, `db_vectors.py`, `universities/utils/recommender_pipeline.py`
and the `KnowledgeNode`/`KnowledgeLink` tables are an earlier embeddings/RAG experiment and are not routed.
`frontend/src/api/axios.js` and `testApi.js` are unused.

---

## 2. Configuration (environment variables)

`settings.py` reads **only the process environment** — on cPanel that means the variables set in
*Setup Python App*. It does **not** read `backend/.env`. (`manage.py` and `langgraph_workflow.py`
call `load_dotenv()`, so management commands and the OpenAI client *also* see `.env`.)

| Variable | Required | Used by |
|---|---|---|
| `SECRET_KEY` | **yes** (startup fails without it) | Django |
| `DATABASE_URL` | **yes** | Supabase Postgres (SSL forced) |
| `SUPABASE_JWT_SECRET` | **yes** | verifying HS256 tokens |
| `SUPABASE_URL` | recommended | JWKS for RS256/ES256 tokens (falls back to the production project URL) |
| `SUPABASE_JWT_AUDIENCE` | optional (`authenticated`) | token audience check |
| `OPENAI_API_KEY` | **yes** for recommendations | `ChatOpenAI` — missing key = app fails to import the prompts view |
| `ALLOWED_HOSTS` | yes | default `api.proactedai.co.ke` |
| `DEBUG` | no (default False) | also controls whether debug payment endpoints exist |
| `PAYHERO_CHANNEL_ID`, `PAYHERO_API_USERNAME`, `PAYHERO_API_PASSWORD` | **yes** for payments | `subscriptions/utils.py` |
| `PAYHERO_CALLBACK_URL` | **yes** for payments | `https://api.proactedai.co.ke/api/subscriptions/confirmation/` |
| `MPESA_CALLBACK_SECRET` | **yes** for payments | long random string; authenticates PayHero callbacks. Empty = every callback rejected |
| `REDIS_URL` | optional | Upstash URL; enables shared cache + rate limiting |
| `REQUIRE_MPESA` | optional | if `True`, startup fails unless all `MPESA_*` vars are set. Those are the **old Daraja** credentials — leave this `False` |
| `MPESA_CONSUMER_KEY/SECRET/SHORTCODE/PASSKEY/CALLBACK_URL` | no | legacy Daraja, unused |
| `ALLOW_LOCALHOST_CORS` | no | adds `http://localhost:5173` to CORS |
| `DB_CONN_MAX_AGE`, `SECURE_HSTS_SECONDS` | no | tuning |

Frontend (baked in at build time from `frontend/.env.production`):
`VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.

CORS allows only `https://proactedai.co.ke` and `https://www.proactedai.co.ke` (hardcoded in `settings.py`).

---

## 3. Authentication

**Frontend:** `frontend/src/lib/supabaseClient.js` signs in with Supabase. `lib/apiClient.js#apiFetch`
reads the current session on every call and sends `Authorization: Bearer <access_token>`.
Admin screens use `api/adminApi.js` (axios) and the blog uses `api/blogApi.js`; both attach the same token.

**Backend:** `apps/users/auth/supabase.py#SupabaseJWTAuthentication` (the default DRF auth class).

| Function | What it does |
|---|---|
| `authenticate` | Reads the Bearer header (with cPanel/LiteSpeed fallbacks `HTTP_AUTHORIZATION`, `REDIRECT_HTTP_AUTHORIZATION`). No header → anonymous. Bad token → 401 |
| `_verify_token` | HS256 → `SUPABASE_JWT_SECRET`; RS256/ES256 → Supabase JWKS + audience + issuer. Checks expiry |
| `_get_or_create_user` | Finds the user by `email` claim (or by `sub` = username when the token has no email). First login creates a **student-only** user. Never changes roles of existing users |

**Roles** live in the DB (`users.CustomUser`): `is_student`, `is_staff`, `is_superuser`. Staff and student are mutually exclusive
(enforced in `CustomUser.clean`). Admin API access = `IsStaffNonStudent` (staff and not student).
`GET /api/auth/me/` is the frontend's source of truth for role and quota (`context/AuthContext.jsx`).

---

## 4. API reference

All paths are relative to `VITE_API_BASE_URL`. Default permission: authenticated.

### Auth & profile
| Method | Path | View | Purpose | Frontend caller |
|---|---|---|---|---|
| GET / PUT | `/api/auth/me/` | `users.views.me` | role flags, tier, `prompts_remaining`; PUT updates name/phone/bio | `AuthContext.jsx`, `SignIn.jsx`, `AuthCallback.jsx` |
| GET | `/api/auth/profile/` | `users.views.profile` | minimal id/email | — |
| GET | `/api/profile/` | `StudentProfileViewSet.full` | full saved profile for wizard pre-fill (404 if none) | `WizardManager.jsx` |
| CRUD | `/api/profiles/`, `/api/grades/` | `StudentProfileViewSet`, `AcademicResultViewSet` | own profile / grades only | — |

### Recommendations
| Method | Path | Purpose | Frontend caller |
|---|---|---|---|
| POST | `/api/prompts/` | run the recommendation pipeline (§5) | `NewPrompt.jsx` |
| GET | `/api/prompts/` | own history (newest first, soft-deleted hidden) | `PromptHistoryContext.jsx`, `WizardManager.jsx` |
| GET | `/api/prompts/<id>/` | one past result | `HistoryDetail.jsx` |
| DELETE | `/api/prompts/<id>/` | soft delete (`is_deleted=True`) | `PromptHistoryContext.jsx` |
| GET | `/api/subjects/` | KCSE subject list (cached 24h) | `useSubjects.js` |

`POST /api/prompts/` responses:

| Status | `error` | Meaning | Prompt quota |
|---|---|---|---|
| 201 | — | `{received, submission_id, path_used:"llm", recommendations:{top_5:[...], submission_id, path_used, cluster_summary?}}` | used |
| 400 | `Validation Error` / `NO_GRADES` | wizard payload invalid | refunded |
| 403 | `PROMPT_LIMIT_REACHED` | monthly limit hit | not used |
| 422 | `NO_ELIGIBLE_PROGRAMMES` | grades qualify for nothing in the DB | refunded |
| 500 | `ADVISOR_FAILURE` | OpenAI failed or returned nothing usable | refunded |

`top_5` is a historical name: it holds 3 (explorer), 5 (mentor_elite) or 10 (scholar_vvip) items. Each item:
`rank, course, university, public_private, level, location, cluster, programme_code, cutoff_points, cutoff_year,
prev_cutoff, prev_cutoff_year, student_cluster_points, insight, career_preview, action_plan, source:"llm"`.

### Payments (`/api/subscriptions/`)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `initiate/` | user | `{phone_number, target_tier, coupon?}` → PENDING `Transaction` + STK push |
| POST | `confirmation/?secret=…` | PayHero only | callback; upgrades the user (§6) |
| GET | `status/` | user | latest transaction: `completed` / `failed` / `pending` / `not_found` |
| POST | `generate-coupon/` | user | mint a 5-char referral coupon (10% off) |
| GET/POST | `test-stk/`, `debug-headers/` | — | **only routed when `DEBUG=True`** |

### Catalogue & eligibility
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/institutions/?search=` | institutions (cached 12h / 5 min for searches) |
| GET | `/api/programmes/`, `/api/clusters/` | programmes / cluster groups (read-only, cached) |
| POST | `/api/universities/check-eligibility/` | `{student_grades:{code:grade}, target_year?, level_name?}` → eligible programmes (no LLM) |
| POST | `/api/universities/check-eligibility/all/` | same, including ineligible with reasons |

### Admin (staff, non-student)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/analytics` | KPI cards, growth, conversion |
| GET | `/api/admin/chats`, `/api/admin/chats/<id>` | prompt submissions (chat logs) |
| GET | `/api/admin/users`, `/api/admin/users/<id>` | user list / one user |
| PATCH | `/api/admin/users/<id>` | change tier / roles (`AdminUserSerializer`) |
| DELETE | `/api/admin/users/<id>` | hard delete — only the user with the lowest id ("root admin") |

### Blog (public)
`GET /api/blog/stats/<slug>/`, `POST /api/blog/like/<slug>/`, `POST /api/blog/view/<slug>/`.
Post content itself lives in `frontend/src/pages/blog/blogData.js`.

Swagger UI: `/api/docs/` · OpenAPI schema: `/api/schema/`.

---

## 5. The recommendation pipeline (`POST /api/prompts/`)

Code: `backend/apps/students/views.py#PromptSubmissionViewSet.create` → `_generate_recommendations`.

```
create()
 1. Quota      lock user row → sync_subscription_period → get_remaining_prompts → reserve 1 prompt
 _generate_recommendations()
 2. Validate   WizardPayloadSerializer → _extract_student_grades
 3. Eligible   get_eligible_programmes → filter_eligible_only            (rules + DB, no AI)
 4. LLM        _serialize_programmes_for_llm + _build_user_profile_for_llm → run_recommendation_graph
 5. Ground     _build_top_recommendations_from_llm → _ground_recommendations_in_shortlist
 6. Slice      3 / 5 / 10 by tier (+ _build_cluster_summary for VVIP)
 7. Persist    PromptSubmission.save, persist_student_profile_from_wizard (best effort)
create()
 8. Refund     any 4xx/5xx or exception after step 1 → refund_prompt
```

### Step 1 — quota (`apps/users/services/subscription.py`)
| Function | What it does |
|---|---|
| `TIER_LIMITS` | explorer 1, mentor_elite 5, scholar_vvip unlimited (per calendar month) |
| `sync_subscription_period(user)` | resets `prompts_used_in_period` to 0 when a new month has started (lazy, no cron) |
| `get_remaining_prompts(user)` | remaining prompts, `None` = unlimited; unknown tiers get the explorer limit |
| `refund_prompt(user_id)` | gives one prompt back (never below 0) |

### Step 2 — validation (`students/serializers_wizard.py`, `students/eligibility_engine.py`)
- `WizardPayloadSerializer` expects `{student_profile: {kcse, personal_cognitive, practical_factors, interests_exposure, influences, decision_priorities}}`.
  Empty subject rows are dropped; Maths Alt A + Alt B together is rejected; priority weights must total 100 in `weights` mode.
- `_extract_student_grades` maps subject names to KUCCPS codes (`universities/utils/requirement_parser.normalize_subject_name`)
  and adds `MEAN` — taken from the payload, or computed with the 7-subject rule (Maths + best language + best 5 others) in `_compute_mean_grade_from_subjects`.

### Step 3 — eligibility (no AI)
`eligibility_engine.get_eligible_programmes` picks the level from the mean grade
(C+ and above → DEGREE, C/C- → CERTIFICATE, D+/D → CRAFT, below → ARTISAN), then calls
`universities/utils/eligibility_filter.get_eligible_programmes`:

| Path | Rule |
|---|---|
| **Degree** | For each cluster: `find_best_subject_combination` (`subject_matcher.py`) must satisfy all 4 cluster subject requirements → `calculate_cluster_points` (`points_calculator.py`) = √((r/48)·(t/84))·48, where r = 4 cluster subjects, t = 7-subject aggregate. Sub-cluster requirements via `check_subcluster_eligibility`. Eligible if points ≥ the latest cutoff (newest non-null of the last 7 years). |
| **TVET** (certificate/craft/artisan) | Eligible if mean grade ≥ programme `minimum_mean_grade` (or the level default). No cluster points. |

`_apply_quality_filters` then keeps at most 2 offerings per normalised course name and sorts by cutoff
(prestige), penalising very "safe" options for students above 35 points.

### Step 4 — AI (`proacted_recommender_engine/langgraph_workflow.py`)
| Piece | What it does |
|---|---|
| `llm` | `ChatOpenAI(gpt-4o-mini, temperature 0.2, max_tokens 3000, timeout 60s, 1 retry)` |
| `filter_batches_node` | eligible list in batches of 500; one call per batch returns 15 programme codes. A failed batch contributes its first 5 |
| `advisor_node` | one call ranks candidates to ≤10 and writes `insight`, `career_preview`, `action_plan` following the 6-section mentor framework in `ADVISOR_PROMPT` |
| `clean_json_response` | strips code fences/comments before JSON parsing |
| `run_recommendation_graph` | entry point; returns `{recommendations, premium_details}` |

OpenAI calls per submission ≈ ⌈eligible ÷ 500⌉ + 1. All of it runs inside the HTTP request.

### Step 5 — grounding (trust boundary)
`_build_top_recommendations_from_llm` normalises field names (`insight`/`reason`/…, cutoffs from `premium_details`).
`_ground_recommendations_in_shortlist` then **overwrites every factual field** (course, university, location,
level, cluster, cutoffs, student points) with the DB values for that `programme_code`, and **drops** any
recommendation whose code was not in the list sent to the model. The AI only chooses and explains.

---

## 6. Payments (PayHero / M-Pesa)

Code: `backend/apps/subscriptions/` · UI: `frontend/src/pages/app/Subscription.jsx`.

```
Subscription.jsx ── POST initiate/ ──► initiate_payment
                                         ├─ Transaction(ref_id="PH-XXXXXXXX", PENDING, amount, target_tier, coupon)
                                         └─ initiate_payhero_stk_push(callback_url = PAYHERO_CALLBACK_URL?secret=…)
Student phone ◄── STK push ── PayHero
PayHero ── POST confirmation/?secret=… ──► confirmation
                                         ├─ 403 unless secret == MPESA_CALLBACK_SECRET
                                         ├─ 404 unless ExternalReference is a Transaction we created
                                         ├─ already processed? → 200 "Already processed" (no re-apply)
                                         ├─ success but Amount < txn.amount → FAILED
                                         └─ SUCCESS → user.subscription_tier = txn.target_tier, record coupon use
Subscription.jsx ── GET status/ every 3s (gives up after 2 min) ──► payment_status
```

| Function | What it does |
|---|---|
| `get_base_amount` | price per tier: mentor_elite **1 KES (test price)**, scholar_vvip 499 KES |
| `validate_coupon` / `calculate_discounted_amount` | 10% off with any existing coupon code |
| `build_callback_url` | appends `?secret=` to `PAYHERO_CALLBACK_URL` |
| `initiate_payhero_stk_push` | Basic-auth POST to PayHero (30s timeout); returns `{success, status, ...}` or `{success: False, error}` |
| `payment_status` | reports the newest transaction; self-heals a SUCCESS whose tier wasn't applied |
| `generate_unique_coupon` | 5 chars, at least one letter from "PROACTED" |

There is no subscription expiry: once upgraded, a tier stays until changed by an admin.

---

## 7. Data model (main tables)

| App | Model | Key fields |
|---|---|---|
| users | `CustomUser` | role flags, `subscription_tier`, `prompts_used_in_period`, `prompt_period_start`, `phone_number` |
| students | `StudentProfile` (1:1 user) | mean grade, goals, budget, location, … |
| students | `Subject`, `AcademicResult` | KCSE subjects (code e.g. `121`), grade per subject |
| students | `StudentAttribute`, `CareerGoal`, `Influence`, `DecisionPriority` | wizard sections, saved by `services/profile_persistence.py` |
| students | `PromptSubmission` | `payload` (wizard JSON), `result` (recommendations JSON), `is_deleted` |
| universities | `Institution`, `ProgrammeLevel`, `ClusterGroup`, `SubClusterGroup`, `Programme`, `ProgrammeOffering`, `ProgrammeRequirement`, `CutOffPoint` | KUCCPS catalogue; cutoffs per offering per year |
| subscriptions | `Transaction`, `Coupon`, `CouponUsed` | PayHero payments and referrals |
| blog | `BlogLike`, `BlogView` | engagement per slug |

The catalogue is loaded from the PDFs in `backend/KUCCPS PROGRAMMES PDF/` by the scripts in `backend/scripts/` and the
management commands in `apps/*/management/commands/` (see `backend/project_documents/SEEDING_GUIDE.md`).

---

## 8. Frontend map

| Area | Files |
|---|---|
| Routing | `src/routes/AppRoutes.jsx` — public (`/`, `/about`, `/kedira-insider`, auth pages), `/app/*` behind `ProtectedRoute`, `/admin/*` behind `AdminProtectedRoute` |
| Auth state | `src/context/AuthContext.jsx` (Supabase session + `/api/auth/me/`) |
| Wizard | `src/components/app/PromptWizard/WizardManager.jsx` + `steps/*`, client checks in `src/utils/wizardValidation.js`, draft saved in localStorage |
| Results | `src/pages/app/NewPrompt.jsx` → `components/app/PromptResult.jsx`; history in `PromptHistoryContext.jsx`, `HistoryDetail.jsx` |
| Payments | `src/pages/app/Subscription.jsx` |
| Admin | `src/pages/admin/*`, `src/api/adminApi.js` |
| HTTP | `src/lib/apiClient.js` — throws `Error` with `.status` and `.data` (backend JSON) on non-2xx |

---

## 9. Deploying

1. **Backend**: upload changed files under `backend/`, then in the Python app's virtualenv:
   `pip install -r requirements.txt` (only if requirements changed) → `python manage.py migrate` → `python manage.py collectstatic --noinput`
   → `touch tmp/restart.txt`.
2. **Frontend**: locally `cd frontend && npm run build`, upload the contents of `dist/` to `public_html`.
   The SPA needs an `.htaccess` rewrite to `index.html` for deep links such as `/app/new`.
3. Smoke test: sign in → `/app/new` wizard → result; Subscription page → STK push → plan updates.

`manage.py` loads `backend/.env`; if that file has `REQUIRE_MPESA=True` without the `MPESA_*` values, management commands will refuse to start.

---

## 10. Logs & troubleshooting

Logs (`apps/utils/logging_config.py`): `backend/logs/general.log`, `error.log`, `cache.log`, `websocket.log`, plus Passenger's
stderr log in cPanel.

| Symptom | Look for | Likely cause |
|---|---|---|
| Every API call 401 | `[AUTH] Token decode failed` | wrong `SUPABASE_JWT_SECRET` / `SUPABASE_URL`, or the `Authorization` header stripped by the proxy |
| "AI advisor could not generate…" | `Batch N failed`, `Final advisor node failed` | OpenAI key/credit/timeout |
| Payments never complete | `Rejected callback with missing/invalid secret` | `MPESA_CALLBACK_SECRET` unset or changed between push and callback |
| Payment start fails | `PayHero is not configured` | missing `PAYHERO_*` vars |
| Slow prompts | `PROCESSING BATCH` count | very large eligible lists → more OpenAI calls |
| Rate limits not applied | `Redis not available` at startup | expected without `REDIS_URL` |

---

## 11. Tests

Run locally against SQLite. **Do not** run `run_tests.py` as-is: it uses `DATABASE_URL`, which is the production Supabase database.

```bash
cd backend
# point Django at a throwaway settings module that swaps DATABASES for sqlite3 :memory:
DATABASE_URL=sqlite:///x SECRET_KEY=test SUPABASE_JWT_SECRET=test OPENAI_API_KEY=sk-test REQUIRE_MPESA=False REDIS_URL= \
  DJANGO_SETTINGS_MODULE=<your sqlite test settings> python manage.py test apps.users.tests.test_payments
```

Status on 2026-10-03:

| Suite | Result |
|---|---|
| `users.tests` (auth, admin, payments, prompts) | 34/34 pass |
| `universities.tests.test_points_calculator`, `test_views`; `utils.tests.test_cache_utils`, `test_redis_config` | pass |
| `universities.tests.test_api_views`, `test_eligibility_filter` | broken import (`students.models` should be `apps.students.models`) |
| `universities.tests.test_requirement_parser`, `test_subject_matcher`; `students.tests.*`; `utils.tests.test_integration` | pre-existing failures, not yet triaged |

---

## 12. Known gaps (not fixed yet)

Ordered by impact. None of these needed new features to document; they are decisions or follow-ups.

1. **Pricing:** `mentor_elite` costs 1 KES (`subscriptions/views.py#get_base_amount`).
2. **Long requests:** the whole AI pipeline runs inside one Passenger request. With a 60s/1-retry cap per OpenAI call, a large
   Degree list can still take minutes; check the host's request timeout.
3. **Admin UI calls endpoints that don't exist:** `adminApi.impersonateUser` (`/api/admin/impersonate/<id>`),
   `bulkUpdateSubscriptions` (`/api/admin/subscriptions/bulk`), `getUserActivity` (`/api/admin/users/<id>/activity`) → 404.
4. **Root admin rule:** user deletion is allowed only for the user with the lowest id, whoever that is.
5. **Coupons:** any user can mint unlimited coupons, and a coupon can be used on its creator's own purchase.
6. **Rate limiting** only works with Redis; without it `POST /api/prompts/` relies on the monthly quota alone.
7. **Inconsistencies:** `_compute_mean_grade_from_subjects` treats `123` as Maths but `calculate_aggregate_points` does not;
   `_fallback_top_recommendations` (unused) reports student points as the cutoff.
8. **Test suite:** see §11.

### Changes made on 2026-10-03
- Payment callback now authenticated (`?secret=`), idempotent, and checks the paid amount; failed STK pushes are closed as FAILED.
- `PAYHERO_*` settings defined; PayHero request has a timeout; debug payment endpoints only exist with `DEBUG=True`.
- Supabase auth: no more matching on a blank email; `logger` defined; per-request `print`s moved to the logger.
- Prompt quota refunded on every failed submission; new `422 NO_ELIGIBLE_PROGRAMMES`; unknown tiers get the explorer limit.
- AI output grounded in the DB shortlist; invented programmes dropped; OpenAI calls capped at 60s/1 retry.
- Artificial `time.sleep` delays now only run when WebSocket progress is active.
- `GET /api/admin/users/<id>` works.
- Frontend: errors carry status/body; limit-reached and no-eligible messages shown correctly; wizard pre-fill URL fixed;
  payment polling stops after 2 minutes.
- `*env*.zip` ignored by git.
