# HAPass

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Shareable guest links for controlling Home Assistant devices**

Create time-limited links that give guests control of specific Home Assistant
entities — lights, locks, thermostats, fans, and more. Guests get a
mobile-friendly PWA with real-time state updates. No HA accounts needed, no app
installs, just a link.

## Screenshots

<p align="center">
  <img src="docs/admin-dashboard.png" width="250" alt="Admin dashboard">
  <img src="docs/admin-dark-extend.png" width="250" alt="Extend expiry (dark mode)">
  <img src="docs/admin-entity-picker.png" width="250" alt="Entity picker">
  <img src="docs/guest-pwa.png" width="250" alt="Guest PWA">
</p>

## How Guest Links Work

1. In the admin dashboard, create an **access token** with:
   - Selected entities the guest can control
   - Optional **PIN protection** for extra security
   - Optional **custom messages** for pre-start and expired states
   - An optional **Start From** date/time (for future access)
   - An **Expiry** date/time
2. Share the generated link (`http://<your-ha-ip>:5880/g/{slug}`) with your guest.
3. The guest opens the link on their phone. No app install or HA account needed.
4. If the token has a PIN set, the guest must enter it (or use a link with an access code via `?c={code}`).
5. If the token has a future start time, the guest sees a "not yet available" message (or your custom message) until that time.
6. When the token expires, the guest sees the contact message (or your custom message) and can no longer control devices.

### Link Sharing with Access Codes

For PIN-protected tokens, you can generate **access codes** that allow guests to bypass PIN entry:

- Click **Copy with PIN** or **QR with PIN** in the admin dashboard
- This generates a random access code and creates a link like `http://<your-ha-ip>:5880/g/{slug}?c={access_code}`
- Guests using this link get immediate access without typing the PIN
- The actual PIN is **never** exposed in URLs — only a random access code
- Access codes can be revoked at any time by modifying the token's PIN

### Token Statuses

In the admin dashboard, tokens display one of these statuses:

| Status | Meaning |
|--------|---------|
| **Scheduled** | Token has a future start time; not yet active |
| **Active** | Token is currently valid and can be used |
| **Expiring** | Token expires within 1 hour |
| **Expired** | Token has passed its expiry time |
| **Revoked** | Token was manually revoked by an admin |

## Features

- **Scoped guest tokens** — each token grants access to a specific set of entities
- **PIN protection** — optionally require a PIN for guest access
- **Access codes for link sharing** — generate reusable access codes (`?c=`) for instant access without exposing the PIN
- **PIN encryption** — all PINs encrypted at rest using AES-256-GCM (mandatory, requires encryption key)
- **Secure PIN entry** — PINs submitted via POST (not GET) to avoid exposure in browser history or logs
- **Custom entity ordering** — drag-and-drop to reorder how entities appear on the guest page
- **Custom messages** — personalize the messages guests see before/after token validity
- **Time-limited access** — tokens auto-expire after a configurable duration
- **Scheduled start time** — create tokens that become active at a future date/time
- **Real-time updates** — SSE-powered live state changes with automatic reconnect
- **Installable PWA** — guests can add it to their home screen for an app-like experience
- **Dark mode** — system-aware with manual override
- **Admin dashboard** — create, revoke, extend, and monitor tokens with an intuitive 5-row action layout
- **Recent activity** — see guest link opens and commands in the admin dashboard
- **Service allowlist** — only safe services (toggle, set_temperature, etc.) are permitted
- **Rate limiting** — 30 req/min per token
- **IP allowlisting** — optionally restrict tokens to specific CIDRs
- **Public REST API** — optional API for external integrations (disabled by default)

## Installation

### Home Assistant Add-on (recommended)

1. Add this repository in **Settings → Add-ons → Add-on Store → ⋮ → Repositories**:

   ```
   https://github.com/j0sh1b/ha-pass
   ```

2. Find **HAPass** in the store and click **Install**.
3. Go to the **Configuration** tab and set your options (including the required **Encryption Key**).
4. Start the add-on.
5. Click **Open Web UI** or find HAPass in the HA sidebar.

Admin access works through the HA sidebar — no separate login needed. Guest
links use the direct port (`http://<your-ha-ip>:5880/g/{slug}`) so visitors
don't need HA accounts.

### Docker Compose

```yaml
services:
  ha-pass:
    image: ghcr.io/j0sh1b/ha-pass:latest
    restart: unless-stopped
    ports:
      - 5880:5880
    volumes:
      - ./data:/data
    environment:
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=changeme
      - HA_BASE_URL=http://homeassistant.local:8123
      - HA_TOKEN=your_long_lived_token_here
      - ENCRYPTION_KEY=your_64_char_hex_key_here
```

```bash
docker compose up -d
```

### Docker Run

```bash
docker run -d --restart unless-stopped \
  -p 5880:5880 \
  -v ./data:/data \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=changeme \
  -e HA_BASE_URL=http://homeassistant.local:8123 \
  -e HA_TOKEN=your_long_lived_token_here \
  -e ENCRYPTION_KEY=your_64_char_hex_key_here \
  ghcr.io/j0sh1b/ha-pass:latest
```

The admin dashboard is at `http://localhost:5880/admin/dashboard`.

> **Note:** Docker deployments need a [long-lived access token](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token) from Home Assistant. Create one in your HA profile under **Security → Long-Lived Access Tokens**. The add-on handles this automatically.

## Configuration

### Add-on Options

Set these in **Settings → Add-ons → HAPass → Configuration**:

| Option | Description | Default |
|---|---|---|
| **Admin Username** | Username for direct-port admin access (not needed for sidebar) | — |
| **Admin Password** | Password for direct-port admin access (min 8 chars) | — |
| **App Name** | Display name shown to guests | `Home Access` |
| **Contact Message** | Message shown when a guest link expires | `Please request a new link...` |
| **Background Color** | Hex color for page background | `#F2F0E9` |
| **Primary Color** | Hex color for accents and buttons | `#D9523C` |
| **Guest URL** | External base URL for guest links (e.g. `https://guest.myhouse.com`) | — |
| **Encryption Key** | **Required**: 64-character hex key for PIN encryption. Generate with: `openssl rand -hex 32` | — |
| **API Enabled** | Enable the public REST API for external integrations | `false` |
| **API Token** | API authentication token (min 32 chars, required if API Enabled) | — |

### Docker Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `ADMIN_USERNAME` | Admin login username | Yes | — |
| `ADMIN_PASSWORD` | Admin login password (min 8 chars) | Yes | — |
| `HA_BASE_URL` | Home Assistant base URL | Yes | — |
| `HA_TOKEN` | HA long-lived access token | Yes | — |
| `ENCRYPTION_KEY` | 64-character hex key for PIN encryption | Yes | — |
| `DB_PATH` | SQLite database path | No | `/data/db.sqlite` |
| `APP_NAME` | Display name shown to guests | No | `Home Access` |
| `CONTACT_MESSAGE` | Message shown on expired pages | No | `Please request a new link...` |
| `ACCESS_LOG_RETENTION_DAYS` | Days to retain access logs | No | `90` |
| `BRAND_BG` | Background color (hex) | No | `#F2F0E9` |
| `BRAND_PRIMARY` | Primary/accent color (hex) | No | `#D9523C` |
| `GUEST_URL` | External base URL for guest links | No | — |
| `API_ENABLED` | Enable public REST API | No | `false` |
| `API_TOKEN` | API authentication token (min 32 chars) | No | — |

### Encryption Key Setup

The **Encryption Key** is **required** and must be exactly 64 hexadecimal characters. This key encrypts all PINs using AES-256-GCM before storing them in the database.

**Generate a key:**
```bash
openssl rand -hex 32
```

**Important:**
- Store this key securely — losing it means encrypted PINs cannot be decrypted
- If you change this key, existing encrypted PINs will become unreadable
- The application will not start without a valid encryption key

## Home Assistant Activity Events

HAPass emits a `ha_pass_activity` event after a valid guest page load and after
a successful guest command. These events are best-effort notification hooks:
HAPass logs and drops event failures without blocking the guest. HAPass also
writes matching Home Assistant Logbook entries for the Activity view.

Event payloads do not include the guest slug, internal token ID, or client IP
address.

```json
{
  "schema_version": 1,
  "activity": "command",
  "token_label": "Cleaner",
  "target_entity_id": "lock.front_door",
  "service": "lock.unlock"
}
```

`activity` is either `page_load` or `command`. `page_load` means the guest link
URL was requested; link previews, scanners, stale bookmarks, and refreshes can
also trigger it. Use `command` for higher-signal notifications.

```yaml
alias: HAPass guest activity notification
triggers:
  - trigger: event
    event_type: ha_pass_activity
conditions:
  - condition: template
    value_template: "{{ trigger.event.data.activity == 'command' }}"
actions:
  - action: notify.mobile_app_phone
    data:
      title: "Guest access"
      message: >
        {{ trigger.event.data.token_label }} used
        {{ trigger.event.data.service }}
        on {{ trigger.event.data.target_entity_id }}
```

## Supported Entity Types

### Controllable Domains

| Domain | Allowed Services |
|---|---|
| `light` | `turn_on`, `turn_off`, `toggle` |
| `switch` | `turn_on`, `turn_off`, `toggle` |
| `input_boolean` | `turn_on`, `turn_off`, `toggle` |
| `input_button` | `press` |
| `climate` | `set_temperature`, `set_hvac_mode`, `turn_on`, `turn_off` |
| `lock` | `lock`, `unlock`, `open` |
| `media_player` | `media_play`, `media_pause`, `media_stop`, `volume_set`, `media_play_pause`, `turn_on`, `turn_off` |
| `cover` | `open_cover`, `close_cover`, `stop_cover` |
| `fan` | `turn_on`, `turn_off`, `toggle`, `set_percentage` |

### Read-Only Domains

| Domain | Access |
|---|---|
| `sensor` | Real-time state display only |
| `binary_sensor` | Real-time state display only |

## Architecture

```
Browser (Guest PWA)
    │
    ├── GET  /g/{slug}          → PWA shell (HTML)
    ├── GET  /g/{slug}/state    → initial entity states
    ├── GET  /g/{slug}/stream   → SSE real-time updates
    └── POST /g/{slug}/command  → service call proxy
                                      │
                                      ▼
                                  HAPass
                                  (FastAPI)
                                      │
                                      ├── REST API → Home Assistant
                                      └── WebSocket → HA event bus
```

### Security Architecture

- **PIN Encryption**: All PINs encrypted with AES-256-GCM before storage
- **Secure PIN Entry**: POST-based validation (not GET/query params)
- **Session Management**: Validated PIN sessions use secure, HTTP-only cookies
- **Access Codes**: Random 128-bit codes for link sharing (PIN never in URL)
- **CSRF Protection**: SameSite=Strict cookies for admin sessions
- **Rate Limiting**: Per-token command rate limiting (30 req/min)
- **API Security**: Optional REST API with mandatory API key authentication (disabled by default)

## Public API

HAPass exposes an optional REST API for external integrations. The API is **disabled by default** for security.

### Enabling the API

Add-on users: Set `api_enabled: true` and `api_token: your-secure-token` in the add-on configuration.

Docker users: Set `API_ENABLED=true` and `API_TOKEN=your-secure-token` environment variables.

### Authentication

All API requests must include the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-token-here" \
     http://your-ha-instance:5880/api/v1/tokens
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tokens` | List all tokens |
| POST | `/api/v1/tokens` | Create a new token |
| GET | `/api/v1/tokens/{id}` | Get a specific token |
| PATCH | `/api/v1/tokens/{id}` | Update a token |
| DELETE | `/api/v1/tokens/{id}` | Revoke/delete a token |

### API Documentation

When the API is enabled, interactive documentation is available at:
- Swagger UI: `/api/docs`
- OpenAPI Schema: `/api/openapi.json`

### Security

- API token must be at least 32 characters
- Rate limited to 100 requests per minute per IP
- Constant-time comparison prevents timing attacks

## Disclaimer

HAPass is not affiliated with, endorsed by, or associated with Home Assistant
or Nabu Casa Inc. "Home Assistant" is a trademark of Nabu Casa Inc.

## License

[MIT](LICENSE)
