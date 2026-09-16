"""Password and signed-token primitives for account authentication."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.config import settings

TOKEN_ALGORITHM = "HS256"


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Represent validated claims shared by access and refresh tokens."""

    account_id: UUID
    tenant_id: UUID
    session_id: UUID
    token_type: Literal["access", "refresh"]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PlatformTokenClaims:
    """Represent validated claims for the isolated platform administration audience."""

    account_id: UUID
    session_id: UUID
    token_type: Literal["access", "refresh"]
    expires_at: datetime


class TokenValidationError(ValueError):
    """Indicate that a signed authentication token is invalid or expired."""


def hash_password(password: str) -> str:
    """Hash a password with bcrypt after enforcing supported input bounds."""

    encoded = password.encode("utf-8")
    if not 12 <= len(encoded) <= 72:
        raise ValueError("Password must contain between 12 and 72 UTF-8 bytes")
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a supplied password matches a bcrypt hash."""

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def issue_token_pair(
    account_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    now: datetime | None = None,
) -> tuple[str, str, datetime]:
    """Issue tenant-bound access and refresh tokens for one persisted session."""

    issued_at = now or datetime.now(UTC)
    access_expiry = issued_at + timedelta(minutes=settings.access_token_minutes)
    refresh_expiry = issued_at + timedelta(days=settings.refresh_token_days)
    common = {
        "sub": str(account_id),
        "tid": str(tenant_id),
        "sid": str(session_id),
        "aud": "tenant",
        "iat": issued_at,
    }
    access_token = jwt.encode(
        {**common, "type": "access", "exp": access_expiry, "jti": str(uuid4())},
        settings.secret_key,
        algorithm=TOKEN_ALGORITHM,
    )
    refresh_token = jwt.encode(
        {**common, "type": "refresh", "exp": refresh_expiry, "jti": str(uuid4())},
        settings.secret_key,
        algorithm=TOKEN_ALGORITHM,
    )
    return access_token, refresh_token, refresh_expiry


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> TokenClaims:
    """Validate a signed token and return strongly typed tenant/session claims."""

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[TOKEN_ALGORITHM],
            audience="tenant",
        )
        if payload.get("type") != expected_type:
            raise TokenValidationError("Unexpected token type")
        return TokenClaims(
            account_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tid"]),
            session_id=UUID(payload["sid"]),
            token_type=expected_type,
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, TokenValidationError):
            raise
        raise TokenValidationError("Invalid or expired token") from exc


def issue_platform_token_pair(
    account_id: UUID,
    session_id: UUID,
    now: datetime | None = None,
) -> tuple[str, str, datetime]:
    """Issue access and refresh tokens restricted to platform administration."""

    issued_at = now or datetime.now(UTC)
    access_expiry = issued_at + timedelta(minutes=settings.access_token_minutes)
    refresh_expiry = issued_at + timedelta(days=settings.refresh_token_days)
    common = {
        "sub": str(account_id),
        "sid": str(session_id),
        "aud": "platform",
        "iat": issued_at,
    }
    access_token = jwt.encode(
        {**common, "type": "access", "exp": access_expiry, "jti": str(uuid4())},
        settings.secret_key,
        algorithm=TOKEN_ALGORITHM,
    )
    refresh_token = jwt.encode(
        {**common, "type": "refresh", "exp": refresh_expiry, "jti": str(uuid4())},
        settings.secret_key,
        algorithm=TOKEN_ALGORITHM,
    )
    return access_token, refresh_token, refresh_expiry


def decode_platform_token(
    token: str,
    expected_type: Literal["access", "refresh"],
) -> PlatformTokenClaims:
    """Validate a platform-audience token and return its strongly typed claims."""

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[TOKEN_ALGORITHM],
            audience="platform",
        )
        if payload.get("type") != expected_type:
            raise TokenValidationError("Unexpected token type")
        return PlatformTokenClaims(
            account_id=UUID(payload["sub"]),
            session_id=UUID(payload["sid"]),
            token_type=expected_type,
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, TokenValidationError):
            raise
        raise TokenValidationError("Invalid or expired platform token") from exc


def token_digest(token: str) -> str:
    """Return a one-way digest suitable for persisted refresh-token comparison."""

    return sha256(token.encode("utf-8")).hexdigest()
