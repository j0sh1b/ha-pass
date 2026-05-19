"""Tests for token PIN functionality."""
import base64

import pytest

from app.auth import SESSION_COOKIE


class TestTokenPinCreate:
    """Tests for creating tokens with PIN."""

    async def test_create_token_with_pin(self, client, admin_session, mock_ha_client):
        """Token can be created with a PIN."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["pin"] == "1234"

    async def test_create_token_without_pin(self, client, admin_session, mock_ha_client):
        """Token can be created without a PIN."""
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
        assert data["pin"] is None


class TestTokenPinUpdate:
    """Tests for updating token PIN."""

    async def test_update_token_pin(self, client, admin_session, mock_ha_client, created_token):
        """PIN can be set via PATCH endpoint."""
        r = await client.patch(
            f"/admin/tokens/{created_token}/pin",
            json={"pin": "5678"},
            cookies=admin_session,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["pin"] == "5678"

    async def test_remove_token_pin(self, client, admin_session, mock_ha_client, created_token):
        """PIN can be removed by setting to null."""
        # First set a PIN
        await client.patch(
            f"/admin/tokens/{created_token}/pin",
            json={"pin": "9999"},
            cookies=admin_session,
        )
        # Then remove it
        r = await client.patch(
            f"/admin/tokens/{created_token}/pin",
            json={"pin": None},
            cookies=admin_session,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["pin"] is None

    async def test_update_pin_on_nonexistent_token_404(self, client, admin_session, mock_ha_client):
        """Updating PIN on nonexistent token returns 404."""
        r = await client.patch(
            "/admin/tokens/nonexistent/pin",
            json={"pin": "1234"},
            cookies=admin_session,
        )
        assert r.status_code == 404


class TestTokenPinValidation:
    """Tests for PIN field validation."""

    async def test_pin_max_length(self, client, admin_session, mock_ha_client):
        """PIN over 20 characters is rejected."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "x" * 21,
            },
            cookies=admin_session,
        )
        assert r.status_code == 422

    async def test_pin_at_max_length_accepted(self, client, admin_session, mock_ha_client):
        """PIN at exactly 20 characters is accepted."""
        max_pin = "x" * 20
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Test Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": max_pin,
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["pin"] == max_pin


class TestTokenPinGuestAccess:
    """Tests for guest access with PIN."""

    async def test_pin_page_shown_when_pin_set(self, client, admin_session, mock_ha_client):
        """PIN entry page is shown when token has PIN and no PIN provided."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 200
        assert b"Enter PIN" in r.content

    async def test_correct_pin_allows_access(self, client, admin_session, mock_ha_client):
        """Correct PIN in URL allows access."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Encode PIN as URL-safe base64
        encoded = base64.urlsafe_b64encode(b"1234").decode().rstrip("=")

        r = await client.get(f"/g/{token['slug']}?t={encoded}")
        assert r.status_code == 200
        # Should show the PWA, not PIN page
        assert b"Enter PIN" not in r.content
        # Check for PWA-specific content (the header with the token label)
        assert "PIN Token" in r.text or "Remaining" in r.text or "cards-container" in r.text

    async def test_incorrect_pin_shows_error(self, client, admin_session, mock_ha_client):
        """Incorrect PIN shows error."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Try wrong PIN
        encoded = base64.urlsafe_b64encode(b"9999").decode().rstrip("=")

        r = await client.get(f"/g/{token['slug']}?t={encoded}")
        assert r.status_code == 200
        assert b"Enter PIN" in r.content
        assert b"Incorrect PIN" in r.content

    async def test_no_pin_bypasses_check(self, client, admin_session, mock_ha_client):
        """Token without PIN allows direct access."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "No PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 200
        assert b"Enter PIN" not in r.content
        # Should show the PWA (check for PWA-specific content)
        assert "No PIN Token" in r.text or "Remaining" in r.text or "cards-container" in r.text


class TestTokenPinPreStartExpired:
    """Tests that PIN is bypassed for pre-start and expired tokens."""

    async def test_pre_start_token_shows_message_not_pin(self, client, admin_session, mock_ha_client):
        """Pre-start token shows pre-start message, not PIN page."""
        future_time = 4102444800 - 3600  # 1 hour before "never" timestamp
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Future Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "starts_at": future_time,
                "pre_start_message": "Not yet active!",
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 410
        assert b"Not yet active!" in r.content
        # Should NOT show PIN page
        assert b"Enter PIN" not in r.content

    async def test_expired_token_shows_message_not_pin(self, client, admin_session, mock_ha_client):
        """Expired token shows expired message, not PIN page."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Quick Expire Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 1,
                "expired_message": "All done!",
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        import asyncio
        await asyncio.sleep(1.1)

        r = await client.get(f"/g/{token['slug']}")
        assert r.status_code == 410
        assert b"All done!" in r.content
        # Should NOT show PIN page
        assert b"Enter PIN" not in r.content


class TestTokenPinQueryParameter:
    """Tests for PIN in query parameter."""

    async def test_pin_query_parameter_variants(self, client, admin_session, mock_ha_client):
        """PIN can be passed via query parameter with padding variations."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Test various encodings
        for encoded in ["MTIzNA", "MTIzNA==", "MTIzNA==="]:
            r = await client.get(f"/g/{token['slug']}?t={encoded}")
            assert r.status_code == 200
            # Should allow access
            assert b"Enter PIN" not in r.content
