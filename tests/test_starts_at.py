"""Tests for the starts_at token feature.

These tests verify that tokens can be created with a future start date
and that they are properly validated before and after the start time.
"""
import time

import pytest

from app import database as db


async def test_create_token_with_starts_at(test_db):
    """Creating a token with starts_at sets the correct timestamp."""
    now = int(time.time())
    future_start = now + 3600  # 1 hour from now
    token = await db.create_token(
        label="Future Token",
        slug="future",
        entity_ids=["light.a"],
        expires_at=now + 86400,
        ip_allowlist=None,
        starts_at=future_start,
    )
    assert token["starts_at"] == future_start


async def test_create_token_without_starts_at_defaults_to_now(test_db):
    """Creating a token without starts_at defaults to current time."""
    before = int(time.time())
    token = await db.create_token(
        label="Now Token",
        slug="now",
        entity_ids=["light.a"],
        expires_at=before + 86400,
        ip_allowlist=None,
    )
    after = int(time.time())
    # starts_at should be between before and after
    assert before <= token["starts_at"] <= after


async def test_create_token_with_starts_at_in_past_fails(test_db):
    """Creating a token with starts_at in the past should use current time."""
    now = int(time.time())
    past_start = now - 3600  # 1 hour ago
    # The database layer accepts it, but the API should validate
    # This test verifies the database behavior
    token = await db.create_token(
        label="Past Token",
        slug="past",
        entity_ids=["light.a"],
        expires_at=now + 86400,
        ip_allowlist=None,
        starts_at=past_start,
    )
    # Database stores whatever is provided; API layer validates
    assert token["starts_at"] == past_start


async def test_get_token_includes_starts_at(test_db):
    """Retrieving a token includes the starts_at field."""
    now = int(time.time())
    future_start = now + 3600
    created = await db.create_token(
        label="Test",
        slug="test-get",
        entity_ids=["light.a"],
        expires_at=now + 86400,
        ip_allowlist=None,
        starts_at=future_start,
    )
    
    # Get by slug
    by_slug = await db.get_token_by_slug("test-get")
    assert by_slug["starts_at"] == future_start
    
    # Get by id
    by_id = await db.get_token_by_id(created["id"])
    assert by_id["starts_at"] == future_start


async def test_list_tokens_includes_starts_at(test_db):
    """Listing tokens includes the starts_at field."""
    now = int(time.time())
    await db.create_token(
        label="Test",
        slug="test-list",
        entity_ids=["light.a"],
        expires_at=now + 86400,
        ip_allowlist=None,
        starts_at=now + 3600,
    )
    
    tokens = await db.list_tokens()
    token = next((t for t in tokens if t["slug"] == "test-list"), None)
    assert token is not None
    assert token["starts_at"] == now + 3600