"""
Supabase JWT Authentication for Django REST Framework.

The frontend signs users in with Supabase (supabase-js) and sends the access token
on every API call as `Authorization: Bearer <token>` (see frontend/src/lib/apiClient.js).
This class verifies that token and maps it to a local CustomUser.

Verification:
  - HS256 tokens  -> checked with SUPABASE_JWT_SECRET (legacy Supabase projects)
  - RS256 / ES256 -> checked with the project's public keys from
                     {SUPABASE_URL}/auth/v1/.well-known/jwks.json, plus audience/issuer

User mapping: the Django DB is the source of truth for roles. A first-time token
creates a student-only user; existing users are returned untouched.
"""
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

# Production project (public URL; also in the production frontend bundle). Production-only fallback.
PRODUCTION_SUPABASE_URL = "https://zuoujlipkmoqxrwcrdij.supabase.co"


@dataclass
class _JwksCache:
    jwks: Optional[dict] = None
    fetched_at: float = 0.0

_JWKS_CACHE = _JwksCache()

def _get_supabase_url() -> str:
    """
    The Supabase project whose tokens this backend accepts (SUPABASE_URL).
    Production may fall back to the production project; every other environment must name its
    own project (e.g. "PROACTED KeDira Development") and never silently uses production auth.
    """
    url = os.environ.get("SUPABASE_URL", "").strip()
    if url:
        return url.rstrip("/")
    if getattr(settings, "APP_ENV", "production") == "production":
        return PRODUCTION_SUPABASE_URL
    raise exceptions.AuthenticationFailed(
        _(f"SUPABASE_URL is not configured for APP_ENV={settings.APP_ENV}.")
    )

def _jwks_url() -> str:
    return f"{_get_supabase_url()}/auth/v1/.well-known/jwks.json"

def _issuer() -> str:
    return f"{_get_supabase_url()}/auth/v1"

def _audience() -> str:
    return os.environ.get("SUPABASE_JWT_AUDIENCE", "").strip() or "authenticated"

def _get_jwks(max_age_seconds: int = 3600) -> dict:
    """Fetch (and cache for an hour) the Supabase JWKS document."""
    now = time.time()
    if _JWKS_CACHE.jwks and (now - _JWKS_CACHE.fetched_at) < max_age_seconds:
        return _JWKS_CACHE.jwks

    try:
        resp = requests.get(_jwks_url(), timeout=10)
        resp.raise_for_status()
        _JWKS_CACHE.jwks = resp.json()
        _JWKS_CACHE.fetched_at = now
        return _JWKS_CACHE.jwks
    except Exception as e:
        raise exceptions.AuthenticationFailed(f"Could not fetch JWKS: {str(e)}")

class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class (configured in settings.REST_FRAMEWORK).

    Returns None (anonymous) when there is no Bearer header, so AllowAny views still
    work; raises AuthenticationFailed (401) when a token is present but invalid.
    """
    keyword = "Bearer"

    def authenticate(self, request) -> Optional[Tuple[object, dict]]:
        # 1) Standard DRF/Django header
        auth_header = request.headers.get("Authorization", "")

        # 2) Fallback for cPanel/Apache/LiteSpeed stripping headers
        if not auth_header:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        # 3) Fallback for redirected headers
        if not auth_header:
            auth_header = request.META.get("REDIRECT_HTTP_AUTHORIZATION", "")

        logger.debug("[AUTH] Request: %s %s", request.method, request.path)

        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1].strip()
        if not token:
            return None

        try:
            payload = self._verify_token(token)
        except jwt.ExpiredSignatureError as e:
            raise exceptions.AuthenticationFailed(_("Token expired.")) from e
        except Exception as e:
            raise exceptions.AuthenticationFailed(_(f"Invalid token: {str(e)}")) from e

        user = self._get_or_create_user(payload)
        return (user, payload)

    def _verify_token(self, token: str) -> dict:
        """Verify signature/expiry (and aud/iss for asymmetric keys); return the claims."""
        # Determine algorithm from header
        try:
            # Try PyJWT version first
            if hasattr(jwt, 'get_unverified_header'):
                header = jwt.get_unverified_header(token)
            else:
                # Jose/jose-python version
                from jose import jwt as jose_jwt
                header = jose_jwt.get_unverified_header(token)
        except Exception as e:
            logger.warning("[AUTH] Failed to parse token header: %s", e)
            raise exceptions.AuthenticationFailed(_("Malformed token header."))

        alg = header.get("alg")

        # Safety: Only allow Supabase standard algorithms
        allowed_algs = ["HS256", "RS256", "ES256"]
        if alg not in allowed_algs:
            logger.warning("[AUTH] Rejected token with algorithm %s", alg)
            raise exceptions.AuthenticationFailed(_(f"Unsupported algorithm: {alg}"))

        signing_key = None
        # HS256 (shared secret) tokens skip aud/iss checks; asymmetric tokens verify both
        decode_kwargs = {
            "algorithms": [alg],
            "options": {
                "verify_aud": alg != "HS256",
                "verify_iss": alg != "HS256",
                "verify_exp": True,
            }
        }

        if alg == "HS256":
            signing_key = os.environ.get("SUPABASE_JWT_SECRET")
            if not signing_key:
                logger.error("SUPABASE_JWT_SECRET is not set in environment!")
                raise exceptions.AuthenticationFailed(_("Backend configuration error: secret missing."))
            signing_key = signing_key.strip()
        else:
            # Production (RS256, ES256): Get public key from Supabase JWKS
            try:
                # PyJWT style
                if hasattr(jwt, 'PyJWKClient'):
                    jwk_client = jwt.PyJWKClient(_jwks_url())
                    signing_key = jwk_client.get_signing_key_from_jwt(token).key
                else:
                    raise Exception(f"PyJWKClient required for {alg} but library missing.")
            except Exception as e:
                logger.error("[AUTH] JWKS failure: %s", e)
                raise exceptions.AuthenticationFailed(_(f"Auth server unreachable or key error: {str(e)}"))

        # Final Decode Attempt
        try:
            if alg != "HS256":
                decode_kwargs["audience"] = _audience()
                decode_kwargs["issuer"] = _issuer()

            # Retry with a single-string algorithm for older PyJWT/jose versions
            try:
                payload = jwt.decode(token, signing_key, **decode_kwargs)
            except Exception as list_err:
                logger.debug("[AUTH] List-decode failed, retrying with single alg: %s", list_err)
                decode_kwargs["algorithms"] = alg
                payload = jwt.decode(token, signing_key, **decode_kwargs)

            return payload
        except Exception as e:
            logger.warning("[AUTH] Token decode failed (%s): %s", type(e).__name__, e)
            if alg == "HS256" and "signature" in str(e).lower():
                logger.warning("[AUTH] HINT: SUPABASE_JWT_SECRET might be incorrect.")
            raise exceptions.AuthenticationFailed(_(f"Invalid token: {str(e)}"))

    def _get_or_create_user(self, payload: dict):
        """
        Map verified claims to a CustomUser.

        Lookup key: the email claim; for tokens without an email (e.g. phone sign-in)
        the Supabase user id (`sub`), which is what new users get as username.
        """
        User = get_user_model()

        supabase_uid = payload.get("sub")
        email = payload.get("email") or ""

        if not email and not supabase_uid:
            raise exceptions.AuthenticationFailed(_("Token has no user identity."))

        # ── ROLE SYNC RULES ────────────────────────────────────────────
        # 1) Existing user → return as-is (DB is source of truth for roles)
        #    Never overwrite is_student / is_staff / is_superuser on login.
        # 2) New user → create as student-only:
        #    is_student=True, is_staff=False, is_superuser=False
        #    Promotion to admin/superuser is done ONLY via admin-sync script.
        # ───────────────────────────────────────────────────────────────

        # Never match on an empty email: that would hand this token whichever
        # existing account happens to have a blank email.
        if email:
            user = User.objects.filter(email=email).first()
        else:
            user = User.objects.filter(username=supabase_uid).first()

        if user:
            return user

        # New user: create as student only (safe default)
        logger.info("[AUTH] Creating new student user: %s", email or supabase_uid)
        user = User.objects.create(
            username=email or supabase_uid,
            email=email,
            is_student=True,
            is_staff=False,
            is_superuser=False,
            is_institution_admin=False,
        )

        return user
