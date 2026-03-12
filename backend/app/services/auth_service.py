"""Authentication service and social identity verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.auth import AuthTokenResponse, SessionRevocationResponse
from app.schemas.user import UserResponse
from app.security.passwords import hash_password, verify_password
from app.services.apple_auth_service import AppleIdentity, AppleTokenVerificationError, AppleTokenVerifierService
from app.services.auth_audit import AuthAuditService
from app.services.token_service import TokenService, TokenServiceError
from app.services.user_service import UserService
from app.utils.enums import AuthProvider
from app.utils.time import utcnow


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400, commit_state: bool = False):
        self.message = message
        self.status_code = status_code
        self.commit_state = commit_state
        super().__init__(message)


@dataclass
class AuthRequestContext:
    device_name: Optional[str] = None
    platform: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class GoogleIdentity:
    sub: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    email_verified: bool


class GoogleTokenVerifier(Protocol):
    def verify(self, raw_id_token: str) -> GoogleIdentity: ...


class GoogleTokenVerifierService:
    def __init__(self, client_id: Optional[str]):
        self.client_id = client_id

    def verify(self, raw_id_token: str) -> GoogleIdentity:
        if not self.client_id:
            raise AuthError("Google Sign-In is not configured on the backend.", status_code=503)
        try:
            payload = google_id_token.verify_oauth2_token(raw_id_token, GoogleRequest(), self.client_id)
        except Exception as exc:  # pragma: no cover - upstream library branches
            raise AuthError("Google ID token verification failed.", status_code=401) from exc
        email = str(payload.get("email") or "").strip().lower()
        if not email or not payload.get("sub"):
            raise AuthError("Google token is missing required identity fields.", status_code=401)
        return GoogleIdentity(
            sub=str(payload["sub"]),
            email=email,
            display_name=payload.get("name"),
            avatar_url=payload.get("picture"),
            email_verified=bool(payload.get("email_verified", False)),
        )


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        google_verifier: GoogleTokenVerifier,
        apple_verifier: AppleTokenVerifierService,
        audit_service: AuthAuditService,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.google_verifier = google_verifier
        self.apple_verifier = apple_verifier
        self.audit_service = audit_service

    def signup(
        self,
        session: Session,
        email: str,
        password: str,
        display_name: Optional[str],
        context: Optional[AuthRequestContext] = None,
    ) -> AuthTokenResponse:
        context = context or AuthRequestContext()
        normalized_email = self.user_service.normalize_email(email)
        if self.user_service.get_user_by_email(session, normalized_email):
            self.audit_service.log(
                session,
                "signup_failed",
                auth_provider=AuthProvider.EMAIL,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"email": normalized_email, "reason": "email_exists"},
            )
            raise AuthError("A user with that email already exists.", status_code=409, commit_state=True)
        user = self.user_service.create_user(
            session,
            email=normalized_email,
            auth_provider=AuthProvider.EMAIL,
            display_name=display_name,
            password_hash=hash_password(password),
            is_verified=False,
        )
        user.last_login_at = utcnow()
        token_pair = self.token_service.issue_token_pair(session, user, device_name=context.device_name, platform=context.platform)
        session.add(user)
        self.audit_service.log(
            session,
            "signup_succeeded",
            user=user,
            auth_provider=AuthProvider.EMAIL,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        return self._build_token_response(user, token_pair)

    def login(
        self,
        session: Session,
        email: str,
        password: str,
        context: Optional[AuthRequestContext] = None,
    ) -> AuthTokenResponse:
        context = context or AuthRequestContext()
        normalized_email = self.user_service.normalize_email(email)
        user = self.user_service.get_user_by_email(session, normalized_email)
        if user is None or not user.password_hash or not verify_password(password, user.password_hash):
            self.audit_service.log(
                session,
                "login_failed",
                auth_provider=AuthProvider.EMAIL,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"email": normalized_email, "reason": "invalid_credentials"},
            )
            raise AuthError("Invalid email or password.", status_code=401, commit_state=True)
        if not user.is_active:
            self.audit_service.log(
                session,
                "login_failed",
                user=user,
                auth_provider=AuthProvider.EMAIL,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"reason": "inactive_user"},
            )
            raise AuthError("This account is inactive.", status_code=403, commit_state=True)
        user.last_login_at = utcnow()
        session.add(user)
        token_pair = self.token_service.issue_token_pair(session, user, device_name=context.device_name, platform=context.platform)
        self.audit_service.log(
            session,
            "login_succeeded",
            user=user,
            auth_provider=AuthProvider.EMAIL,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        return self._build_token_response(user, token_pair)

    def authenticate_google(
        self,
        session: Session,
        raw_id_token: str,
        context: Optional[AuthRequestContext] = None,
    ) -> AuthTokenResponse:
        context = context or AuthRequestContext()
        try:
            identity = self.google_verifier.verify(raw_id_token)
        except AuthError:
            self.audit_service.log(
                session,
                "google_sign_in_failed",
                auth_provider=AuthProvider.GOOGLE,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"reason": "token_verification_failed"},
            )
            raise

        user = self.user_service.get_user_by_google_sub(session, identity.sub)
        if user is None:
            user = self.user_service.get_user_by_email(session, identity.email)
            if user is not None and user.google_sub and user.google_sub != identity.sub:
                self.audit_service.log(
                    session,
                    "google_sign_in_failed",
                    user=user,
                    auth_provider=AuthProvider.GOOGLE,
                    success=False,
                    device_name=context.device_name,
                    platform=context.platform,
                    ip_address=context.ip_address,
                    user_agent=context.user_agent,
                    metadata_json={"reason": "account_conflict"},
                )
                raise AuthError("That email is already linked to a different Google account.", status_code=409, commit_state=True)
            if user is None:
                user = self.user_service.create_user(
                    session,
                    email=identity.email,
                    auth_provider=AuthProvider.GOOGLE,
                    display_name=identity.display_name,
                    avatar_url=identity.avatar_url,
                    google_sub=identity.sub,
                    password_hash=None,
                    is_verified=identity.email_verified,
                )
            else:
                user.google_sub = identity.sub
                if not user.avatar_url and identity.avatar_url:
                    user.avatar_url = identity.avatar_url
                if not user.display_name and identity.display_name:
                    user.display_name = identity.display_name
                user.is_verified = user.is_verified or identity.email_verified
        user.last_login_at = utcnow()
        session.add(user)
        token_pair = self.token_service.issue_token_pair(session, user, device_name=context.device_name, platform=context.platform)
        self.audit_service.log(
            session,
            "google_sign_in_succeeded",
            user=user,
            auth_provider=AuthProvider.GOOGLE,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        return self._build_token_response(user, token_pair)

    def authenticate_apple(
        self,
        session: Session,
        identity_token: str,
        authorization_code: str,
        context: Optional[AuthRequestContext] = None,
    ) -> AuthTokenResponse:
        context = context or AuthRequestContext()
        try:
            identity = self.apple_verifier.verify(identity_token)
        except AppleTokenVerificationError as exc:
            self.audit_service.log(
                session,
                "apple_sign_in_failed",
                auth_provider=AuthProvider.APPLE,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"reason": "token_verification_failed"},
            )
            raise AuthError(str(exc), status_code=401, commit_state=True) from exc

        user = self.user_service.get_user_by_apple_sub(session, identity.sub)
        if user is None and identity.email:
            user = self.user_service.get_user_by_email(session, identity.email)
        if user is not None and user.apple_sub and user.apple_sub != identity.sub:
            self.audit_service.log(
                session,
                "apple_sign_in_failed",
                user=user,
                auth_provider=AuthProvider.APPLE,
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"reason": "account_conflict"},
            )
            raise AuthError("That email is already linked to a different Apple account.", status_code=409, commit_state=True)

        if user is None:
            email = identity.email or self.user_service.synthetic_apple_email(identity.sub)
            user = self.user_service.create_user(
                session,
                email=email,
                auth_provider=AuthProvider.APPLE,
                display_name=None,
                apple_sub=identity.sub,
                password_hash=None,
                is_verified=identity.email_verified or identity.email is None,
            )
        else:
            user.apple_sub = identity.sub
            user.is_verified = user.is_verified or identity.email_verified or identity.email is None
        user.last_login_at = utcnow()
        session.add(user)
        token_pair = self.token_service.issue_token_pair(session, user, device_name=context.device_name, platform=context.platform)
        self.audit_service.log(
            session,
            "apple_sign_in_succeeded",
            user=user,
            auth_provider=AuthProvider.APPLE,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json={
                "authorization_code_supplied": bool(authorization_code),
                "is_private_email": identity.is_private_email,
            },
        )
        return self._build_token_response(user, token_pair)

    def refresh(
        self,
        session: Session,
        refresh_token: str,
        context: Optional[AuthRequestContext] = None,
    ) -> AuthTokenResponse:
        context = context or AuthRequestContext()
        try:
            user, token_pair = self.token_service.refresh(
                session,
                refresh_token,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
            )
        except TokenServiceError as exc:
            self.audit_service.log(
                session,
                "refresh_failed",
                success=False,
                device_name=context.device_name,
                platform=context.platform,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json={"reason": exc.message},
            )
            raise AuthError(exc.message, status_code=exc.status_code, commit_state=True) from exc
        if not user.is_active:
            raise AuthError("This account is inactive.", status_code=403, commit_state=True)
        user.last_login_at = utcnow()
        session.add(user)
        self.audit_service.log(
            session,
            "refresh_succeeded",
            user=user,
            auth_provider=user.auth_provider,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        return self._build_token_response(user, token_pair)

    def logout(self, session: Session, refresh_token: str, context: Optional[AuthRequestContext] = None) -> bool:
        context = context or AuthRequestContext()
        success = self.token_service.revoke(session, refresh_token)
        self.audit_service.log(
            session,
            "logout_succeeded" if success else "logout_failed",
            success=success,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json={"reason": None if success else "refresh_token_not_found"},
        )
        return success

    def revoke_sessions(
        self,
        session: Session,
        user: User,
        context: Optional[AuthRequestContext] = None,
    ) -> SessionRevocationResponse:
        context = context or AuthRequestContext()
        revoked_count = self.token_service.revoke_all_for_user(session, user)
        self.audit_service.log(
            session,
            "sessions_revoked",
            user=user,
            auth_provider=user.auth_provider,
            device_name=context.device_name,
            platform=context.platform,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json={"revoked_count": revoked_count},
        )
        return SessionRevocationResponse(success=True, revoked_count=revoked_count)

    def get_me(self, user: User) -> UserResponse:
        return UserResponse.from_model(user)

    def _build_token_response(self, user: User, token_pair) -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type="bearer",
            access_token_expires_in=token_pair.access_token_expires_in,
            refresh_token_expires_in=token_pair.refresh_token_expires_in,
            user=UserResponse.from_model(user),
        )
