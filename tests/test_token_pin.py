"""Tests for token PIN functionality."""
import base64

import pytest

from app.auth import SESSION_COOKIE
from app.routers.guest import GUEST_PIN_COOKIE


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

    async def test_access_code_allows_access(self, client, admin_session, mock_ha_client):
        """Access code in URL allows access without PIN prompt."""
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

        # Generate access code via admin API
        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            json={"pin": "1234"},
            cookies=admin_session,
        )
        assert r.status_code == 200
        access_code = r.json()["access_code"]

        # Use access code in URL
        r = await client.get(f"/g/{token['slug']}?c={access_code}", follow_redirects=True)
        assert r.status_code == 200
        # Should show the PWA, not PIN page
        assert b"Enter PIN" not in r.content
        # Check for PWA-specific content (the header with the token label)
        assert "PIN Token" in r.text or "Remaining" in r.text or "cards-container" in r.text

    async def test_invalid_access_code_shows_pin_page(self, client, admin_session, mock_ha_client):
        """Invalid access code shows PIN entry page."""
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

        # Try invalid access code
        r = await client.get(f"/g/{token['slug']}?c=invalidcode")
        assert r.status_code == 200
        assert b"Enter PIN" in r.content

    async def test_old_pin_in_url_no_longer_works(self, client, admin_session, mock_ha_client):
        """Old ?t=PIN parameter no longer grants access."""
        import base64

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

        # Try old-style base64 encoded PIN
        encoded = base64.urlsafe_b64encode(b"1234").decode().rstrip("=")
        r = await client.get(f"/g/{token['slug']}?t={encoded}")
        assert r.status_code == 200
        # Should show PIN page (old parameter no longer works)
        assert b"Enter PIN" in r.content

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


class TestAccessCodeReuse:
    """Tests for access code reusability."""

    async def test_access_code_reusable_multiple_times(self, client, admin_session, mock_ha_client):
        """Same access code works multiple times."""
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

        # Generate access code
        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            json={"pin": "1234"},
            cookies=admin_session,
        )
        access_code = r.json()["access_code"]

        # Use access code multiple times
        for _ in range(3):
            # Each use gets its own session
            r = await client.get(
                f"/g/{token['slug']}?c={access_code}",
                follow_redirects=True
            )
            assert r.status_code == 200
            assert b"Enter PIN" not in r.content


class TestTokenPinPostValidation:
    """Tests for POST-based PIN validation (more secure than GET)."""

    async def test_post_pin_validates_and_redirects(self, client, admin_session, mock_ha_client):
        """POST with correct PIN creates session and redirects to PWA."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "POST PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "5678",
            },
            cookies=admin_session,
        )
        token = r.json()

        # POST PIN to validation endpoint
        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "5678"},
            follow_redirects=False,
        )
        assert r.status_code == 303  # See Other redirect
        assert f"/g/{token['slug']}" in r.headers.get("location", "")
        # Should set session cookie
        assert GUEST_PIN_COOKIE in r.cookies

    async def test_post_pin_incorrect_shows_error(self, client, admin_session, mock_ha_client):
        """POST with incorrect PIN shows PIN entry page with error."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "POST PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "5678",
            },
            cookies=admin_session,
        )
        token = r.json()

        # POST wrong PIN
        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "9999"},
        )
        assert r.status_code == 401
        assert b"Enter PIN" in r.content
        assert b"Incorrect PIN" in r.content

    async def test_post_pin_creates_session_for_subsequent_requests(self, client, admin_session, mock_ha_client):
        """After POST PIN validation, subsequent requests use session cookie."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Session PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # First request: POST PIN
        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "1234"},
            follow_redirects=False,
        )
        assert r.status_code == 303
        session_cookie = r.cookies.get(GUEST_PIN_COOKIE)
        assert session_cookie is not None

        # Second request: Access PWA with session cookie
        r = await client.get(
            f"/g/{token['slug']}",
            cookies={GUEST_PIN_COOKIE: session_cookie},
        )
        assert r.status_code == 200
        # Should show PWA, not PIN page
        assert b"Enter PIN" not in r.content
        assert b"Session PIN Token" in r.content or "cards-container" in r.text

    async def test_post_pin_invalid_session_requires_revalidation(self, client, admin_session, mock_ha_client):
        """Invalid/expired session cookie requires PIN re-entry."""
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

        # Access with invalid session cookie
        r = await client.get(
            f"/g/{token['slug']}",
            cookies={GUEST_PIN_COOKIE: "invalid_session_id"},
        )
        # Should show PIN entry page
        assert r.status_code == 200
        assert b"Enter PIN" in r.content

    async def test_post_pin_to_wrong_slug_returns_expired(self, client, admin_session, mock_ha_client):
        """POST PIN to non-existent slug returns expired page."""
        r = await client.post(
            "/g/nonexistent-slug/pin",
            data={"pin": "1234"},
        )
        assert r.status_code == 410
        assert b"Access unavailable" in r.content or b"expired" in r.content.lower()

    async def test_post_pin_without_pin_token_redirects(self, client, admin_session, mock_ha_client):
        """POST PIN to token without PIN requirement redirects directly."""
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

        # POST to pin endpoint even though no PIN is required
        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "anything"},
            follow_redirects=False,
        )
        assert r.status_code == 303
        assert f"/g/{token['slug']}" in r.headers.get("location", "")

    async def test_post_pin_expired_token_shows_expired(self, client, admin_session, mock_ha_client):
        """POST PIN to expired token shows expired message."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Expired Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 1,
                "expired_message": "Token expired!",
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        import asyncio
        await asyncio.sleep(1.1)

        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "1234"},
        )
        assert r.status_code == 410
        assert b"Token expired!" in r.content

    async def test_post_pin_pre_start_shows_pre_start(self, client, admin_session, mock_ha_client):
        """POST PIN to pre-start token shows pre-start message."""
        future_time = 4102444800 - 3600  # 1 hour before "never" timestamp
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "Future Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 86400,
                "starts_at": future_time,
                "pre_start_message": "Not started yet!",
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.post(
            f"/g/{token['slug']}/pin",
            data={"pin": "1234"},
        )
        assert r.status_code == 410
        assert b"Not started yet!" in r.content
