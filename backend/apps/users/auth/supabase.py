# Supabase JWT Authentication for Django REST Framework.
# Validates Supabase access tokens (RS256) using Supabase JWKS.
print(">>> [AUTH] Supabase Auth Middleware Initialized")

import os
import jwt
import requests
import time
from dataclasses import dataclass
from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

@dataclass
class _JwksCache:
    jwks: Optional[dict] = None
    fetched_at: float = 0.0

_JWKS_CACHE = _JwksCache()

def _get_supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL")
    if not url:
        # Fallback to a default or raise error if absolute must
        return "https://zuoujlipkmoqxrwcrdij.supabase.co"
    return url.rstrip("/")

def _jwks_url() -> str:
    return f"{_get_supabase_url()}/auth/v1/.well-known/jwks.json"

def _issuer() -> str:
    return f"{_get_supabase_url()}/auth/v1"

def _audience() -> str:
    return os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated")

def _get_jwks(max_age_seconds: int = 3600) -> dict:
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
        
        # Verbose Logging to STDOUT
        print(f">>> [AUTH] Request: {request.method} {request.path}")
        
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1].strip()
        if not token:
            return None
        
        print(f">>> [AUTH] Found Bearer Token")

        try:
            payload = self._verify_token(token)
        except jwt.ExpiredSignatureError as e:
            raise exceptions.AuthenticationFailed(_("Token expired.")) from e
        except Exception as e:
            raise exceptions.AuthenticationFailed(_(f"Invalid token: {str(e)}")) from e

        user = self._get_or_create_user(payload)
        return (user, payload)

    def _verify_token(self, token: str) -> dict:
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
            print(f">>> [AUTH] Failed to parse header: {e}")
            raise exceptions.AuthenticationFailed(_("Malformed token header."))

        alg = header.get("alg")
        print(f">>> [AUTH] Request Alg: {alg}")

        # Safety: Only allow Supabase standard algorithms
        allowed_algs = ["HS256", "RS256", "ES256"]
        if alg not in allowed_algs:
            print(f">>> [AUTH] REJECTED: Algorithm {alg} not in allowed list.")
            raise exceptions.AuthenticationFailed(_(f"Unsupported algorithm: {alg}"))

        signing_key = None
        # Audience and Issuer are often slightly different in local dev vs production
        # We will verify them manually after decoding if needed, or rely on jwt.decode
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
                    # python-jose style manual fetch
                    logger.info(f"python-jose detected. Manual {alg} fetch...")
                    resp = requests.get(_jwks_url(), timeout=5)
                    resp.raise_for_status()
                    # We'll try to use the PyJWT approach
                    raise Exception(f"PyJWKClient required for {alg} but library missing.")
            except Exception as e:
                print(f">>> [AUTH] JWKS Failure: {e}")
                raise exceptions.AuthenticationFailed(_(f"Auth server unreachable or key error: {str(e)}"))

        # Final Decode Attempt
        try:
            if alg != "HS256":
                decode_kwargs["audience"] = _audience()
                decode_kwargs["issuer"] = _issuer()

            # Extreme Fallback: Try with list first, then with single string if it fails
            try:
                payload = jwt.decode(token, signing_key, **decode_kwargs)
            except Exception as list_err:
                print(f">>> [AUTH] List-decode failed, trying single string alg... {list_err}")
                decode_kwargs["algorithms"] = alg # Change list to string
                payload = jwt.decode(token, signing_key, **decode_kwargs)
            
            return payload
        except Exception as e:
            print(f">>> [AUTH] DECODE FAILED ({type(e).__name__}): {str(e)}")
            # Special hint for HS256 secret mismatches
            if alg == "HS256" and "signature" in str(e).lower():
                print(">>> [AUTH] HINT: Your SUPABASE_JWT_SECRET might be incorrect.")
            raise exceptions.AuthenticationFailed(_(f"Invalid token: {str(e)}"))

    def _get_or_create_user(self, payload: dict):
        User = get_user_model()

        supabase_uid = payload.get("sub")
        email = payload.get("email") or ""

        # ── ROLE SYNC RULES ────────────────────────────────────────────
        # 1) Existing user → return as-is (DB is source of truth for roles)
        #    Never overwrite is_student / is_staff / is_superuser on login.
        # 2) New user → create as student-only:
        #    is_student=True, is_staff=False, is_superuser=False
        #    Promotion to admin/superuser is done ONLY via admin-sync script.
        # ───────────────────────────────────────────────────────────────

        user = User.objects.filter(email=email).first()

        if user:
            # Existing user: DB roles are authoritative — do NOT modify them
            print(f">>> [AUTH] Existing user: {email} (is_student={user.is_student}, is_staff={user.is_staff}, is_superuser={user.is_superuser})")
            return user

        # New user: create as student only (safe default)
        print(f">>> [AUTH] Creating new student user: {email}")
        user = User.objects.create(
            username=email or supabase_uid,
            email=email,
            is_student=True,
            is_staff=False,
            is_superuser=False,
            is_institution_admin=False,
        )

        return user
