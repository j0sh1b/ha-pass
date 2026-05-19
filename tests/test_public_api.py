"""Tests for public API endpoints.

Note: Tests that require API_ENABLED=true must be run with:
  API_ENABLED=true API_TOKEN=test-api-key-1234567890abcdef-extra-long pytest tests/test_public_api.py

Other tests verify API returns 403/404 when disabled.
"""
import os
import pytest

from httpx import AsyncClient

# Get token from environment or use default for disabled API tests
API_TOKEN = os.environ.get("API_TOKEN", "test-api-key-1234567890abcdef-extra-long")
API_ENABLED = os.environ.get("API_ENABLED", "false").lower() == "true"


@pytest.mark.skipif(
    API_ENABLED,
    reason="This test only runs when API is disabled"
)
async def test_api_disabled_returns_403_or_404(client: AsyncClient):
    """API endpoints return 403/404 when disabled."""
    response = await client.get("/api/v1/tokens")
    # When API is disabled, either 403 (router included but auth rejects) or 404 (router not included)
    assert response.status_code in (403, 404)


@pytest.mark.skipif(
    API_ENABLED,
    reason="This test only runs when API is disabled"
)
async def test_swagger_not_available_when_disabled(client: AsyncClient):
    """Swagger UI returns 404 when API is disabled."""
    response = await client.get("/api/docs")
    assert response.status_code == 404


# The following tests require API_ENABLED=true environment variable
# Run with: API_ENABLED=true API_TOKEN=test-api-key-1234567890abcdef-extra-long pytest tests/test_public_api.py -k "enabled"


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_api_requires_api_key_enabled(client: AsyncClient):
    """API requires X-API-Key header (requires API_ENABLED=true)."""
    response = await client.get("/api/v1/tokens")
    assert response.status_code == 401

    response = await client.get(
        "/api/v1/tokens",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_list_tokens_enabled(client: AsyncClient):
    """Can list tokens with valid API key (requires API_ENABLED=true)."""
    response = await client.get(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_create_token_enabled(client: AsyncClient):
    """Can create token with valid API key (requires API_ENABLED=true)."""
    response = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Test API Token",
            "entity_ids": ["light.living_room"],
            "expires_in_seconds": 3600
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["label"] == "Test API Token"
    assert data["entity_count"] == 1
    assert "id" in data


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_get_token_enabled(client: AsyncClient):
    """Can get specific token with valid API key (requires API_ENABLED=true)."""
    # First create a token
    create_resp = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Get Test",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600
        }
    )
    assert create_resp.status_code == 201
    token_id = create_resp.json()["id"]

    # Get the token
    response = await client.get(
        f"/api/v1/tokens/{token_id}",
        headers={"X-API-Key": API_TOKEN}
    )
    assert response.status_code == 200
    assert response.json()["id"] == token_id


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_delete_token_enabled(client: AsyncClient):
    """Can delete token with valid API key (requires API_ENABLED=true)."""
    # First create a token
    create_resp = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Delete Test",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600
        }
    )
    assert create_resp.status_code == 201
    token_id = create_resp.json()["id"]

    # Delete the token
    response = await client.delete(
        f"/api/v1/tokens/{token_id}",
        headers={"X-API-Key": API_TOKEN}
    )
    assert response.status_code == 204

    # Verify token is revoked by trying to get it
    get_resp = await client.get(
        f"/api/v1/tokens/{token_id}",
        headers={"X-API-Key": API_TOKEN}
    )
    assert get_resp.json()["revoked"] is True


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_update_token_enabled(client: AsyncClient):
    """Can update token with valid API key (requires API_ENABLED=true)."""
    # First create a token
    create_resp = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Update Test",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600
        }
    )
    assert create_resp.status_code == 201
    token_id = create_resp.json()["id"]

    # Update the token
    response = await client.patch(
        f"/api/v1/tokens/{token_id}",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Updated Label",
            "entity_ids": ["light.test", "switch.test"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Updated Label"
    assert data["entity_count"] == 2


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_create_token_invalid_cidr_enabled(client: AsyncClient):
    """Returns 422 for invalid CIDR (requires API_ENABLED=true)."""
    response = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Invalid CIDR Test",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600,
            "ip_allowlist": ["invalid-cidr"]
        }
    )
    assert response.status_code == 422


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_create_token_duplicate_slug_enabled(client: AsyncClient):
    """Returns 409 for duplicate slug (requires API_ENABLED=true)."""
    # First create a token with specific slug
    response1 = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "First Token",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600,
            "slug": "unique-slug-123"
        }
    )
    assert response1.status_code == 201

    # Try to create another with same slug
    response2 = await client.post(
        "/api/v1/tokens",
        headers={"X-API-Key": API_TOKEN},
        json={
            "label": "Second Token",
            "entity_ids": ["light.test"],
            "expires_in_seconds": 3600,
            "slug": "unique-slug-123"
        }
    )
    assert response2.status_code == 409


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_get_nonexistent_token_enabled(client: AsyncClient):
    """Returns 404 for non-existent token (requires API_ENABLED=true)."""
    response = await client.get(
        "/api/v1/tokens/nonexistent-id",
        headers={"X-API-Key": API_TOKEN}
    )
    assert response.status_code == 404


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_swagger_docs_available_when_enabled_enabled(client: AsyncClient):
    """Swagger UI is available when API is enabled (requires API_ENABLED=true)."""
    response = await client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
    # CSP should allow CDN resources for Swagger UI
    csp = response.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in csp, f"CSP should allow cdn.jsdelivr.net for API docs, got: {csp}"
    assert "https://fastapi.tiangolo.com" in csp, f"CSP should allow fastapi.tiangolo.com for favicon, got: {csp}"


@pytest.mark.skipif(
    not API_ENABLED,
    reason="API must be enabled via API_ENABLED env var"
)
async def test_openapi_schema_available_when_enabled_enabled(client: AsyncClient):
    """OpenAPI schema is available when API is enabled (requires API_ENABLED=true)."""
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "HAPass"
    assert "/api/v1/tokens" in str(schema["paths"])
