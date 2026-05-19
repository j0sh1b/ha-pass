"""Tests for access code functionality.

Access codes provide a secure way to share links without exposing the PIN.
The access code is a random value stored in the database, not the PIN itself.
"""
import pytest


class TestAccessCodeGeneration:
    """Tests for admin API access code generation."""

    async def test_create_access_code_succeeds_without_pin(self, client, admin_session, mock_ha_client):
        """Access code is generated without requiring PIN input (admin is already authenticated)."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        assert r.status_code == 201
        token = r.json()

        # Generate access code without providing PIN (admin auth is sufficient)
        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_code" in data
        assert len(data["access_code"]) == 32  # 32-char hex

    async def test_create_access_code_token_without_pin_fails(self, client, admin_session, mock_ha_client):
        """Cannot generate access code for token without PIN."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "No PIN Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        assert r.status_code == 400
        assert "does not have a PIN" in r.json()["detail"]

    async def test_create_access_code_nonexistent_token_404(self, client, admin_session):
        """404 when trying to create access code for non-existent token."""
        r = await client.post(
            "/admin/tokens/nonexistent/access-code",
            cookies=admin_session,
        )
        assert r.status_code == 404


class TestAccessCodeRevocation:
    """Tests for access code revocation."""

    async def test_revoke_access_code(self, client, admin_session, mock_ha_client):
        """Admin can revoke an access code."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Create access code (no PIN required - admin already authenticated)
        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        access_code = r.json()["access_code"]

        # Revoke it
        r = await client.delete(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        assert r.status_code == 200

        # Access code should no longer work
        r = await client.get(f"/g/{token['slug']}?c={access_code}")
        assert r.status_code == 200  # Shows PIN entry page
        assert "Enter PIN" in r.text or "pin" in r.text.lower()


class TestAccessCodeGuestAccess:
    """Tests for guest access using access codes."""

    async def test_access_code_allows_entry(self, client, admin_session, mock_ha_client):
        """Valid access code allows guest entry without PIN prompt."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        access_code = r.json()["access_code"]

        # Access with code should redirect and set session
        r = await client.get(
            f"/g/{token['slug']}?c={access_code}",
            follow_redirects=False,
        )
        assert r.status_code == 302  # Redirect to clean URL
        assert "ha_guest_pin_session" in r.cookies

        # Follow redirect should show PWA
        r = await client.get(
            f"/g/{token['slug']}?c={access_code}",
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert "Enter PIN" not in r.text

    async def test_invalid_access_code_shows_pin_entry(self, client, admin_session, mock_ha_client):
        """Invalid access code shows PIN entry page."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}?c=invalidcode")
        assert r.status_code == 200
        assert "Enter PIN" in r.text or "pin" in r.text.lower()

    async def test_access_code_reusable_across_devices(self, client, admin_session, mock_ha_client):
        """Same access code works for multiple devices/sessions."""
        import httpx
        from main import app

        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.post(
            f"/admin/tokens/{token['id']}/access-code",
            cookies=admin_session,
        )
        access_code = r.json()["access_code"]

        # First device uses access code
        r1 = await client.get(
            f"/g/{token['slug']}?c={access_code}",
            follow_redirects=False,
        )
        assert r1.status_code == 302
        session1 = r1.cookies.get("ha_guest_pin_session")
        assert session1

        # Second device (new client instance) uses same access code
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client2:
            r2 = await client2.get(
                f"/g/{token['slug']}?c={access_code}",
                follow_redirects=False,
            )
            assert r2.status_code == 302
            session2 = r2.cookies.get("ha_guest_pin_session")
            assert session2
            # Different sessions
            assert session1 != session2

    async def test_old_pin_in_url_no_longer_works(self, client, admin_session, mock_ha_client):
        """Old ?t=PIN parameter no longer works."""
        import base64

        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        # Old style URL with base64 PIN
        encoded = base64.urlsafe_b64encode(b"1234").decode().rstrip("=")
        r = await client.get(f"/g/{token['slug']}?t={encoded}")
        assert r.status_code == 200
        # Should show PIN entry (access code parameter 'c' not provided)
        assert "Enter PIN" in r.text or "pin" in r.text.lower()

    async def test_plaintext_pin_in_url_no_longer_works(self, client, admin_session, mock_ha_client):
        """Plaintext ?t=1234 no longer works."""
        r = await client.post(
            "/admin/tokens",
            json={
                "label": "PIN Protected Token",
                "entity_ids": ["light.living_room"],
                "expires_in_seconds": 3600,
                "pin": "1234",
            },
            cookies=admin_session,
        )
        token = r.json()

        r = await client.get(f"/g/{token['slug']}?t=1234")
        assert r.status_code == 200
        # Should show PIN entry
        assert "Enter PIN" in r.text or "pin" in r.text.lower()


class TestAccessCodeDatabase:
    """Tests for database access code functions."""

    async def test_set_and_get_access_code(self, test_db):
        """Can set and retrieve access code."""
        from app import database as db

        token = await db.create_token(
            label="Test",
            slug="test-access",
            entity_ids=["light.test"],
            expires_at=9999999999,
            ip_allowlist=None,
            pin="5678",
        )

        code = await db.set_token_access_code(token["id"])
        assert len(code) == 32

        retrieved = await db.get_token_by_access_code(code)
        assert retrieved["id"] == token["id"]

    async def test_clear_access_code(self, test_db):
        """Can clear access code."""
        from app import database as db

        token = await db.create_token(
            label="Test",
            slug="test-clear",
            entity_ids=["light.test"],
            expires_at=9999999999,
            ip_allowlist=None,
            pin="5678",
        )

        code = await db.set_token_access_code(token["id"])
        await db.clear_token_access_code(token["id"])

        retrieved = await db.get_token_by_access_code(code)
        assert retrieved is None

    async def test_access_code_is_unique(self, test_db):
        """Access codes are unique across tokens."""
        from app import database as db

        token1 = await db.create_token(
            label="Test 1",
            slug="test-unique-1",
            entity_ids=["light.test1"],
            expires_at=9999999999,
            ip_allowlist=None,
            pin="1111",
        )

        token2 = await db.create_token(
            label="Test 2",
            slug="test-unique-2",
            entity_ids=["light.test2"],
            expires_at=9999999999,
            ip_allowlist=None,
            pin="2222",
        )

        code1 = await db.set_token_access_code(token1["id"])
        code2 = await db.set_token_access_code(token2["id"])

        assert code1 != code2
