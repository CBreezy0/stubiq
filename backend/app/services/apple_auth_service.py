"""Sign in with Apple identity token verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt as pyjwt


APPLE_ISSUER = "https://appleid.apple.com"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"


class AppleTokenVerificationError(Exception):
    pass


@dataclass
class AppleIdentity:
    sub: str
    email: Optional[str]
    email_verified: bool
    is_private_email: bool


class AppleTokenVerifierService:
    def __init__(self, client_id: Optional[str]):
        self.client_id = client_id
        self.jwks_client = pyjwt.PyJWKClient(APPLE_KEYS_URL)

    def verify(self, identity_token: str) -> AppleIdentity:
        if not self.client_id:
            raise AppleTokenVerificationError("Sign in with Apple is not configured on the backend.")
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(identity_token)
            payload = pyjwt.decode(
                identity_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=APPLE_ISSUER,
            )
        except Exception as exc:  # pragma: no cover - upstream library branches
            raise AppleTokenVerificationError("Apple identity token verification failed.") from exc

        sub = str(payload.get("sub") or "").strip()
        if not sub:
            raise AppleTokenVerificationError("Apple identity token is missing the subject claim.")

        email_raw = payload.get("email")
        email = str(email_raw).strip().lower() if email_raw else None
        email_verified_raw = payload.get("email_verified", False)
        is_private_email_raw = payload.get("is_private_email", False)
        return AppleIdentity(
            sub=sub,
            email=email,
            email_verified=email_verified_raw in {True, "true", "True", 1, "1"},
            is_private_email=is_private_email_raw in {True, "true", "True", 1, "1"},
        )
