"""Tests for custom token message fields."""
import pytest

from app.auth import SESSION_COOKIE


class TestTokenMessagesCreate:
    """Tests for creating tokens with custom messages."""

    async def test_create_token_with_pre_start_message(self, client, admin_session, mock_ha_client):
        """Token can be created with pre_start_message."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pre_start_message": "Your stay starts tomorrow!",
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["pre_start_message"] == "Your stay starts tomorrow!"
        assert data["expired_message"] is None

    async def test_create_token_with_expired_message(self, client, admin_session, mock_ha_client):
        """Token can be created with expired_message."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "expired_message": "Thanks for staying with us!",
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["expired_message"] == "Thanks for staying with us!"
        assert data["pre_start_message"] is None

    async def test_create_token_with_both_messages(self, client, admin_session, mock_ha_client):
        """Token can be created with both messages."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pre_start_message": "Check-in starts at 3 PM",
                "expired_message": "Thanks for visiting!",
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["pre_start_message"] == "Check-in starts at 3 PM"
        assert data["expired_message"] == "Thanks for visiting!"

    async def test_create_token_without_messages_defaults_null(self, client, admin_session, mock_ha_client):
        """Token messages default to None when not provided."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["pre_start_message"] is None
        assert data["expired_message"] is None


class TestTokenMessagesUpdate:
    """Tests for updating token messages."""

    async def test_update_token_messages(self, client, admin_session, mock_ha_client, created_token):
        """Messages can be updated via PATCH endpoint."""
        r = await client.patch(
            f"/admin/tokens/{created_token}/messages",
            json={
                "pre_start_message": "Updated pre-start",
                "expired_message": "Updated expired",
            },
            cookies=admin_session,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["pre_start_message"] == "Updated pre-start"
        assert data["expired_message"] == "Updated expired"

    async def test_update_messages_on_nonexistent_token_404(self, client, admin_session, mock_ha_client):
        """Updating messages on nonexistent token returns 404."""
        r = await client.patch(
            "/admin/tokens/nonexistent/messages",
            json={"pre_start_message": "Test"},
            cookies=admin_session,
        )
        assert r.status_code == 404

    async def test_update_messages_requires_auth(self, client, mock_ha_client, created_token):
        """Updating messages requires authentication."""
        r = await client.patch(
            f"/admin/tokens/{created_token}/messages",
            json={"pre_start_message": "Test"},
        )
        assert r.status_code == 401


class TestTokenMessagesInList:
    """Tests that messages appear in token responses."""

    async def test_list_tokens_includes_messages(self, client, admin_session, mock_ha_client, created_token):
        """Token list includes message fields."""
        # Update messages first
        await client.patch(
            f"/admin/tokens/{created_token}/messages",
            json={
                "pre_start_message": "Listed pre-start",
                "expired_message": "Listed expired",
            },
            cookies=admin_session,
        )

        r = await client.get(
            "/admin/tokens",
            cookies=admin_session,
        )
        assert r.status_code == 200
        tokens = r.json()
        token = next((t for t in tokens if t["id"] == created_token), None)
        assert token is not None
        assert token["pre_start_message"] == "Listed pre-start"
        assert token["expired_message"] == "Listed expired"

    async def test_get_token_detail_includes_messages(self, client, admin_session, mock_ha_client, created_token):
        """Token detail includes message fields."""
        # Update messages first
        await client.patch(
            f"/admin/tokens/{created_token}/messages",
            json={
                "pre_start_message": "Detail pre-start",
                "expired_message": "Detail expired",
            },
            cookies=admin_session,
        )

        r = await client.get(
            f"/admin/tokens/{created_token}",
            cookies=admin_session,
        )
        assert r.status_code == 200
        token = r.json()
        assert token["pre_start_message"] == "Detail pre-start"
        assert token["expired_message"] == "Detail expired"


class TestTokenMessagesGuestDisplay:
    """Tests for guest-facing message display."""

    async def test_expired_page_shows_custom_message(self, client, admin_session, mock_ha_client):
        """Expired token page shows custom expired_message."""
        # Create an already-expired token with custom message
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Expired Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 1,  # Will expire immediately
                "expired_message": "Custom expired message for guests",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Wait for token to expire and request page
        import asyncio
        await asyncio.sleep(1.1)

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 410
        assert b"Custom expired message for guests" in r.content

    async def test_pre_start_page_shows_custom_message(self, client, admin_session, mock_ha_client):
        """Pre-start token page shows custom pre_start_message."""
        import time

        future_time = int(time.time()) + 3600  # 1 hour from now

        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Future Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "starts_at": future_time,
                "pre_start_message": "Check back later for access!",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 410
        assert b"Check back later for access!" in r.content

    async def test_expired_page_shows_default_when_no_custom(self, client, admin_session, mock_ha_client):
        """Expired token page shows default message when no custom message set."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Expired Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 1,
            },
            cookies=admin_session,
        )
        token = r.json()

        import asyncio
        await asyncio.sleep(1.1)

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 410
        # Default message should be shown
        assert b"Access Expired" in r.content


class TestTokenMessagesValidation:
    """Tests for message field validation."""

    async def test_message_max_length(self, client, admin_session, mock_ha_client):
        """Messages over 1000 characters are rejected."""
        long_message = "x" * 1001
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pre_start_message": long_message,
            },
            cookies=admin_session,
        )
        assert r.status_code == 422

    async def test_message_at_max_length_accepted(self, client, admin_session, mock_ha_client):
        """Messages at exactly 1000 characters are accepted."""
        max_message = "x" * 1000
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "expired_message": max_message,
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert len(data["expired_message"]) == 1000
