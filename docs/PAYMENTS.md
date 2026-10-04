# KeDira Payments & Environments

KeDira (PROACTED) takes subscription payments through **PayHero only**. This page explains how the
payment code is organised, how each environment is configured, and how developers work on it
**without any production credentials**.

> **VUKE is a completely separate system.** It has its own Supabase project, Edge Functions and
> PayHero configuration. Nothing in KeDira uses, references or deploys to VUKE, and VUKE values
> must never be copied into KeDira.

---

## 1. Payment flow

```
Customer ─► KeDira frontend ─► Django POST /api/subscriptions/initiate/
                                  price from server settings → Transaction PENDING (PostgreSQL)
                                  └─► PayHero POST /api/v2/payments  ─► M-Pesa prompt on the phone
PayHero ─► Django POST /api/subscriptions/confirmation/?secret=…     (server-to-server)
              secret ✓ → reference ✓ → exact amount ✓ → allowed transition ✓
              → (optional) PayHero GET /api/v2/transaction-status ✓
              → Transaction SUCCESS + user.subscription_tier                (PostgreSQL)
Frontend ─► GET /api/subscriptions/status/ every 3 s (stops after 2 min) ─► shows the result
```

- The frontend **never** holds PayHero values, never calls PayHero, and cannot mark a payment paid.
- Only `services.apply_payment_outcome()` changes a payment's status.

| Status | Meaning | Can become |
|---|---|---|
| `PENDING` | prompt sent, waiting | SUCCESS, FAILED, CANCELLED, EXPIRED, VERIFYING |
| `VERIFYING` | callback passed, waiting for PayHero's status API (only when verification is on) | SUCCESS, FAILED |
| `EXPIRED` | no callback within `PAYMENT_PENDING_TIMEOUT_MINUTES` (default 15) | SUCCESS (a late, verified payment still counts) |
| `SUCCESS` / `FAILED` / `CANCELLED` | final | — |

Duplicate callbacks are acknowledged but never applied twice. Payment rows are never deleted.

## 2. Code map (`backend/apps/subscriptions/`)

| File | Purpose |
|---|---|
| `config.py` | environment rules and per-environment prices (imported by `settings.py`) |
| `providers.py` | `PayHeroProvider` (real) and `MockProvider` (local), same interface: `initiate`, `get_status` |
| `services.py` | all business logic: start a payment, parse callbacks, verify, apply outcomes, expire |
| `views.py` / `urls.py` | thin HTTP layer; `mock/complete/` exists only outside production |
| `management/commands/mock_payment.py` | finish mock payments from the terminal |
| `tests/` | payment flow and configuration-safety tests |
| `migrations/0006_payhero_only_payments.py` | adds `provider_reference`; everything else state-only |

## 3. Environments

`APP_ENV` selects the environment and is **mandatory** for `manage.py`, scripts and shells — a missing
`APP_ENV` refuses to start. Only the production web-server entry points (`passenger_wsgi.py`, `wsgi.py`,
`asgi.py`) default it to `production`, so the live site needs no change.

| | development | test | staging | production |
|---|---|---|---|---|
| Database | `backend/db.sqlite3`, or a Postgres **on this machine** (remote URLs refused) | in-memory SQLite (forced) | its own `DATABASE_URL` (required; the production database is refused) | production `DATABASE_URL` (required) |
| Redis | local only (remote `REDIS_URL` ignored) | none | any | any |
| Payment provider | `mock` (default) | `mock` (forced) | `mock` (default) | `payhero` (required — `mock` refuses to start) |
| Real PayHero allowed? | **never** (mock forced, PayHero credentials discarded) | never | only with `PAYHERO_ALLOW_NON_PRODUCTION=true` and non-production credentials | yes |
| Mentor Elite price | KES 1 | KES 1 | KES 1 | **KES 199** |
| Scholar VVIP price | KES 499 | KES 499 | KES 499 | KES 499 |
| `SECRET_KEY`, `SUPABASE_JWT_SECRET` | optional | not needed | required | required |
| DEBUG default | on | off | off | off |

Running `manage.py test` with any `APP_ENV` other than `test` refuses to start.

## 4. Environment variables

Names only — see `backend/.env.example` and `frontend/.env.example`.

| Variable | dev | staging | production |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` (or unset) |
| `PAYMENT_PROVIDER` | `mock` (only option) | `mock` or `payhero` | `payhero` |
| `PAYHERO_ALLOW_NON_PRODUCTION` | — (ignored) | `true` only if using PayHero | — |
| `PAYHERO_CHANNEL_ID`, `PAYHERO_API_USERNAME`, `PAYHERO_API_PASSWORD` | — | non-production values, if any | **owner only** |
| `PAYHERO_CALLBACK_URL` | — | staging API `/api/subscriptions/confirmation/` | `https://api.proactedai.co.ke/api/subscriptions/confirmation/` |
| `PAYHERO_CALLBACK_SECRET` | — | its own random value | **owner only**, long random string |
| `PAYHERO_VERIFY_WITH_STATUS_API` | — | `true` to try it | `true` once confirmed on staging (§7) |
| `SECRET_KEY`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `ALLOWED_HOSTS` | optional | required | required |
| `OPENAI_API_KEY` | optional | as needed | required for recommendations |

The frontend only needs `VITE_API_BASE_URL`, `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (public by design).

## 5. Local setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # already set to APP_ENV=development + PAYMENT_PROVIDER=mock
python manage.py migrate      # creates backend/db.sqlite3
python manage.py runserver
```

Guards (enforced in `settings.py`, tested in `apps/utils/tests/test_env_safety.py`):
- no `APP_ENV` → refuses to start (an old `.env` can't silently mean production);
- `APP_ENV=development` + a remote `DATABASE_URL` → refuses to start;
- a remote `REDIS_URL` is ignored; PayHero credentials are discarded; the provider is always `mock`;
- `development`/`test`/`staging` refuse the production database; `scripts/manage_roles.py` refuses the
  production Supabase project unless `APP_ENV=production`.

Even so, **keep only development values in `backend/.env`** — e.g. `OPENAI_API_KEY` and Supabase values are still
used locally if present.

## 5a. Development login (Supabase)

| | Local development (`npm run dev`, `APP_ENV=development`) | Production |
|---|---|---|
| Supabase project | **PROACTED KeDira Development** | existing production project (unchanged) |
| Frontend values | `frontend/.env.development.local` (git-ignored) | `frontend/.env.production` |
| Backend values | `backend/.env` → `SUPABASE_URL` | server environment |
| Production project allowed? | **no** — refused by the frontend (dev mode) and by backend startup | yes |

Guards: the frontend ignores a production `VITE_SUPABASE_URL` in development mode
(`src/lib/supabaseClient.js`); the backend refuses to start in development/test with a production
`SUPABASE_URL` or production service-role key, and only production may fall back to the production
project when `SUPABASE_URL` is unset (`apps/users/auth/supabase.py`).

**Connecting the development project** (only public values are needed for login):
1. `frontend/.env.development.local` (create it; never commit it):
   ```
   VITE_SUPABASE_URL=https://<dev-project-ref>.supabase.co
   VITE_SUPABASE_ANON_KEY=<dev project's anon or publishable key>
   ```
2. `backend/.env`:
   ```
   SUPABASE_URL=https://<dev-project-ref>.supabase.co
   ```
   The backend verifies login tokens with the project's public signing keys (JWKS) — no secret needed.
   Only if the development project still signs tokens with the legacy shared JWT secret (HS256) also set
   `SUPABASE_JWT_SECRET` there (local file only).
3. In the development project's dashboard (Authentication → URL configuration): Site URL `http://localhost:5173`;
   redirect URLs `http://localhost:5173/**` (email confirmation, `/auth/callback`, `/reset-password`).
   Google sign-in only works there if the development project gets its own Google OAuth client.
4. Restart `npm run dev` and `manage.py runserver`. Sign up in the app — the account lives only in the
   development project, and its Django user only in your local database (students by default;
   promote with `APP_ENV=development python scripts/manage_roles.py`, which never touches production).

Never put the development project's service-role/secret key in the frontend or in any committed file.

## 6. Testing payments locally (no credentials)

With `PAYMENT_PROVIDER=mock`, starting an upgrade creates a real `PENDING` transaction but nothing
leaves your machine. Then finish it in any of three ways — all run the same code as a real PayHero callback:

1. **In the app**: the "Awaiting Payment" card shows *success / failed / cancelled* buttons
   (only when the backend reports the mock provider).
2. **Terminal**:
   ```bash
   python manage.py mock_payment --list
   python manage.py mock_payment PH-1A2B3C4D success      # or failed / cancelled
   ```
3. **API** (logged-in user, own payment only):
   `POST /api/subscriptions/mock/complete/ {"external_reference": "PH-…", "outcome": "success"}`

Run a completion twice to see idempotency; wait `PAYMENT_PENDING_TIMEOUT_MINUTES` to see expiry.

**Automated tests** (always isolated: in-memory SQLite, mock provider, PayHero HTTP patched).
Known **pre-existing** failures (17 tests, identical before the payment work, left unchanged on purpose):
`students.test_consumers` (2), `students.test_views` (7), `universities.test_requirement_parser` (2),
`universities.test_subject_matcher` (1), `utils.test_integration` (3), `universities.test_api_views` (1),
`universities.test_eligibility_filter` (1) — outdated fixtures/imports; see SYSTEM_REFERENCE.md §11.
```bash
cd backend
python run_tests.py                                     # whole suite
APP_ENV=test python manage.py test apps.subscriptions.tests.test_payments apps.subscriptions.tests.test_config
```

PayHero does not publish a sandbox in its public SDK, so there is no PayHero test mode in this project.
If PROACTED is given a separate non-production PayHero channel, it can be used on **staging** with
`PAYMENT_PROVIDER=payhero` + `PAYHERO_ALLOW_NON_PRODUCTION=true`.

## 7. Server-side verification

The callback is authenticated by `?secret=PAYHERO_CALLBACK_SECRET` (PayHero's public material
documents no signed callbacks). With `PAYHERO_VERIFY_WITH_STATUS_API=true`, a successful callback
is additionally checked against `GET transaction-status?reference=<PayHero reference>`:
only a top-level `"status": "SUCCESS"` activates the plan; anything else leaves the payment in
`VERIFYING`, re-checked while the customer polls.

PayHero does not publish that response's fields, so **confirm it once on staging** (or with a
1 KES production test) before turning it on in production: if the payment sits in `VERIFYING`
although PayHero shows it as paid, leave the flag off and report the response shape.

## 8. Rules for developers

Never ask the project owner for, and never put in code, git, tests, docs, logs, chats or the frontend:
- PROACTED's PayHero channel ID, API username/password or callback secret
- the production database URL, Django `SECRET_KEY`, Supabase JWT secret or service-role key
- HostPinnacle/cPanel access

You don't need any of them: the mock provider and SQLite cover all payment development.
Production configuration is owner-controlled and set directly on the server.

Logging rules (already enforced in code): no credentials, no `Authorization` headers, no full
callback/provider payloads; phone numbers are masked (`+254****678`).
