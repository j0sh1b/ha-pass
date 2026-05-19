"""Tests for entity ordering functionality."""
import pytest

from app import database as db


@pytest.mark.asyncio
async def test_create_token_preserves_entity_order(test_db):
    """Creating a token should preserve the order of entity_ids."""
    entity_ids = [
        "light.living_room",
        "switch.kitchen",
        "light.bedroom",
        "lock.front_door",
        "climate.thermostat",
    ]

    token = await db.create_token(
        label="Test Order",
        slug="test-order",
        entity_ids=entity_ids,
        expires_at=9999999999,
        ip_allowlist=None,
    )

    # Retrieve entities - should be in same order
    retrieved = await db.get_token_entities(token["id"])
    assert retrieved == entity_ids


@pytest.mark.asyncio
async def test_update_token_entities_preserves_order(test_db):
    """Updating entities should preserve the new order."""
    # Create token with initial entities
    initial_ids = ["light.a", "light.b", "light.c"]
    token = await db.create_token(
        label="Test Update",
        slug="test-update",
        entity_ids=initial_ids,
        expires_at=9999999999,
        ip_allowlist=None,
    )

    # Update with reordered and new entities
    new_order = ["light.c", "light.a", "switch.new", "light.b"]
    await db.update_token_entities(token["id"], new_order)

    # Retrieve and verify order
    retrieved = await db.get_token_entities(token["id"])
    assert retrieved == new_order


@pytest.mark.asyncio
async def test_update_token_entities_deduplicates_preserving_order(test_db):
    """Updating entities should deduplicate while preserving first occurrence order."""
    token = await db.create_token(
        label="Test Dedupe",
        slug="test-dedupe",
        entity_ids=["light.a", "light.b"],
        expires_at=9999999999,
        ip_allowlist=None,
    )

    # Update with duplicates
    with_duplicates = ["light.c", "light.a", "light.c", "light.b", "light.a"]
    await db.update_token_entities(token["id"], with_duplicates)

    # Should be deduplicated preserving first occurrence order
    retrieved = await db.get_token_entities(token["id"])
    expected = ["light.c", "light.a", "light.b"]
    assert retrieved == expected


@pytest.mark.asyncio
async def test_create_token_deduplicates_preserving_order(test_db):
    """Creating a token should deduplicate entities while preserving order."""
    with_duplicates = ["light.first", "light.second", "light.first", "light.third", "light.second"]

    token = await db.create_token(
        label="Test Create Dedupe",
        slug="test-create-dedupe",
        entity_ids=with_duplicates,
        expires_at=9999999999,
        ip_allowlist=None,
    )

    retrieved = await db.get_token_entities(token["id"])
    expected = ["light.first", "light.second", "light.third"]
    assert retrieved == expected
