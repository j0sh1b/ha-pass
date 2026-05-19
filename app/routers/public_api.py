"""Public API router for external integrations."""
import ipaddress
import json
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app import database as db
from app.models import NEVER_EXPIRES_SECONDS, TokenCreateRequest, TokenResponse
from app.public_api_auth import require_api_key

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


class TokenUpdateRequest(BaseModel):
    """Update request with all fields optional."""
    label: str | None = Field(default=None, min_length=1, max_length=200)
    entity_ids: list[str] | None = None
    expires_in_seconds: int | None = Field(default=None, gt=0)
    slug: str | None = None  # Cannot be changed, but included for completeness
    ip_allowlist: list[str] | None = None
    starts_at: int | None = None
    pre_start_message: str | None = Field(default=None, max_length=1000)
    expired_message: str | None = Field(default=None, max_length=1000)
    pin: str | None = Field(default=None, max_length=20)


@router.get("/tokens", response_model=list[TokenResponse])
async def list_tokens() -> list[dict]:
    """List all tokens."""
    rows = await db.list_tokens()
    return [_row_to_response(r) for r in rows]


@router.post("/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(request: Request, body: TokenCreateRequest) -> dict:
    """Create a new token."""
    # Validate IP CIDR list if provided
    if body.ip_allowlist:
        for cidr in body.ip_allowlist:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid CIDR: {cidr}",
                )

    slug = body.slug or secrets.token_hex(16)
    if body.expires_in_seconds == NEVER_EXPIRES_SECONDS:
        expires_at = NEVER_EXPIRES_SECONDS
    else:
        expires_at = int(time.time()) + body.expires_in_seconds

    # Ensure slug uniqueness
    existing = await db.get_token_by_slug(slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug '{slug}' already exists",
        )

    row = await db.create_token(
        label=body.label,
        slug=slug,
        entity_ids=body.entity_ids,
        expires_at=expires_at,
        ip_allowlist=body.ip_allowlist,
        starts_at=body.starts_at,
        pre_start_message=body.pre_start_message,
        expired_message=body.expired_message,
        pin=body.pin,
    )
    entity_ids = await db.get_token_entities(row["id"])
    return _row_to_response(row, entity_ids)


@router.get("/tokens/{token_id}", response_model=TokenResponse)
async def get_token(token_id: str) -> dict:
    """Get a specific token by ID."""
    row = await db.get_token_by_id(token_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    entity_ids = await db.get_token_entities(token_id)
    return _row_to_response(row, entity_ids)


@router.patch("/tokens/{token_id}", response_model=TokenResponse)
async def update_token(token_id: str, body: TokenUpdateRequest) -> dict:
    """Update a token's properties."""
    row = await db.get_token_by_id(token_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Apply updates based on provided fields
    if body.label is not None:
        await db.update_token_label(token_id, body.label)
    if body.entity_ids is not None:
        await db.update_token_entities(token_id, body.entity_ids)
    if body.expires_in_seconds is not None:
        new_expires = int(time.time()) + body.expires_in_seconds
        await db.update_token_expiry(token_id, new_expires)
    if body.starts_at is not None:
        await db.update_token_starts_at(token_id, body.starts_at)
    if body.pre_start_message is not None or body.expired_message is not None:
        await db.update_token_messages(
            token_id,
            pre_start_message=body.pre_start_message,
            expired_message=body.expired_message,
        )
    if body.pin is not None:
        await db.update_token_pin(token_id, body.pin)

    row = await db.get_token_by_id(token_id)
    entity_ids = await db.get_token_entities(token_id)
    return _row_to_response(row, entity_ids)


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(token_id: str) -> None:
    """Delete (revoke) a token."""
    row = await db.get_token_by_id(token_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.revoke_token(token_id)


def _row_to_response(row: Any, entity_ids: list[str] | None = None) -> dict:
    """Convert database row to response dict."""
    import json
    ip_raw = row["ip_allowlist"]
    ip_list = json.loads(ip_raw) if ip_raw else None
    if entity_ids is not None:
        count = len(entity_ids)
    elif "entity_count" in row.keys():
        count = row["entity_count"]
    else:
        count = 0
    return {
        "id": row["id"],
        "slug": row["slug"],
        "label": row["label"],
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "revoked": bool(row["revoked"]),
        "last_accessed": row["last_accessed"],
        "ip_allowlist": ip_list,
        "entity_count": count,
        "entity_ids": entity_ids,
        "starts_at": row["starts_at"] if "starts_at" in row.keys() else row["created_at"],
        "pre_start_message": row["pre_start_message"] if "pre_start_message" in row.keys() else None,
        "expired_message": row["expired_message"] if "expired_message" in row.keys() else None,
        "pin": row["pin"] if "pin" in row.keys() else None,
    }
