# HAPass

Shareable guest links for controlling Home Assistant devices.

## What it does

HAPass lets you create time-limited guest links that expose specific Home Assistant entities (lights, locks, switches, etc.) to visitors. No HA account required. Guests get a mobile-friendly PWA with real-time state updates.

## Accessing the admin UI

After installing, HAPass appears in the Home Assistant side panel. Click it to open the admin dashboard. No separate login needed, HA handles authentication automatically.

For direct port access (e.g., `http://<your-ha-ip>:5880/admin/dashboard`), set **Admin Username** and **Admin Password** in the configuration below.

## How guest links work

1. In the admin dashboard, create an **access token** with selected entities and an expiration time.
2. Optionally set **custom messages** that guests will see before the token starts or after it expires.
3. Optionally add **PIN protection** for extra security.
4. Optionally reorder the selected entities by dragging them in the "Entities" modal.
5. Share the generated link (`http://<your-ha-ip>:5880/g/{slug}`) with your guest.
6. The guest opens the link on their phone. No app install or HA account needed.
7. When the token expires, the guest sees the contact message (or your custom message) and can no longer control devices.

## Admin Dashboard

The admin dashboard provides a clean, intuitive interface for managing guest access tokens. Each token card shows:

- **Status**: Active, Expiring, Scheduled, Expired, or Revoked
- **Entity count** and **expiry time**
- **Last accessed** time and **IP allowlist** (if set)
- **PIN protection** status

### Token Actions

Each token has a row of action buttons:

| Button | Purpose |
|--------|---------|
| **Copy** | Copy the guest link to clipboard |
| **QR** | Show a QR code for the guest link |
| **Copy with PIN** | Generate an access code and copy link with `?c=` parameter (disabled if no PIN set) |
| **QR with PIN** | Generate an access code and show QR code with `?c=` parameter (disabled if no PIN set) |
| **Entities** | Open the entity picker to change which devices the guest can control |
| **Expiry** | Modify the expiry date/time and start date/time |
| **Messages** | Edit custom pre-start and expired messages |
| **Duplicate** | Create a new token with the same settings |
| **Set PIN / Change PIN** | Add, change, or remove PIN protection |
| **Revoke** | Immediately disable the token |

### Managing Token Lifecycle

**Extending or Renewing:**
- Click **Expiry** on any token to modify its validity period
- For expired or revoked tokens, this acts as a "renew" function
- You can also change the **Start From** time to schedule when the token becomes active

**PIN Protection:**
- Click **Set PIN** (or **Change PIN** if one exists) to add PIN protection
- Leave the PIN field empty and save to remove protection
- Use **Copy with PIN** or **QR with PIN** to share links with an access code that grants immediate access

## Entity Ordering

When creating or editing a token, you can customize the order in which entities appear on the guest page:

1. Click **Entities** on any token to open the entity picker
2. In the **Selected** section, drag entities using the ⋮⋮ handle to reorder them
3. The new order is saved automatically when you click **Save**
4. Guests will see entities in exactly the order you specified

This is useful for prioritizing important controls (e.g., putting the main living room light first) or grouping related devices together.

## Custom Messages

You can set custom messages that guests will see instead of the default messages:

| Message Type | When Shown | Default if Empty |
|--------------|------------|------------------|
| **Pre-Start Message** | When a guest opens a link before its scheduled start time | "This guest session has not started yet. Please check back later." |
| **Expired Message** | When a guest opens an expired or revoked link | "This guest session has ended or the link is no longer valid." |

### Setting Custom Messages

When creating a token:
1. Fill in the optional **Pre-Start Message** and **Expired Message** textareas
2. These messages support multi-line text

For existing tokens:
1. Click the **Messages** button on any active token
2. Edit the messages in the modal
3. Click **Save**

Messages are preserved when duplicating tokens.

## PIN Protection

You can add an optional PIN to any token for extra security. When a PIN is set, guests must enter it before accessing the control page.

### How PIN Protection Works

| Scenario | Behavior |
|----------|----------|
| **No PIN** | Guest opens link and sees controls immediately |
| **PIN set, no access code** | Guest sees a PIN entry page |
| **PIN set, access code in URL (`?c=`)** | Guest sees controls immediately (direct access) |
| **Wrong PIN** | Guest sees error message and can retry |
| **Pre-start/Expired** | PIN check is skipped; guest sees custom/default message |

### Setting a PIN

When creating a token:
1. Fill in the optional **PIN** field (up to 20 characters)
2. The PIN will be required for guest access

For existing tokens:
1. Click the **Set PIN** or **Change PIN** button on any token
2. Enter the new PIN (or leave empty to remove)
3. Click **Save**

### Sharing Links with Access Codes

When a token has a PIN, you'll see **Copy with PIN** and **QR with PIN** buttons in the admin dashboard. These generate a random **access code** and include it in the link:

```
http://<your-ha-ip>:5880/g/{slug}?c={access_code}
```

Guests opening this link won't need to type the PIN — they'll have direct access. This is useful for:
- Sharing via trusted messaging apps
- QR codes that should work immediately
- Guests who may have difficulty remembering a PIN

**Security Notes:**
- Access codes are random 32-character hex strings (128-bit entropy)
- The actual PIN is **never** exposed in URLs, browser history, or server logs
- Access codes can be revoked by clearing them (the admin must regenerate to re-enable)
- Anyone with the access code link has the same access as knowing the PIN

### Revoking Access Codes

To revoke an access code and force guests to enter the PIN:
1. Click **Set PIN** or **Change PIN** on the token
2. The access code will be cleared automatically when you modify the PIN
3. Guests with the old link will now need to enter the PIN manually

### Security Considerations

- PINs are encrypted at rest using **AES-256-GCM** (authenticated encryption)
- The slug in the URL is the primary security mechanism
- PINs add a layer of protection against accidental link sharing
- For highly sensitive access, consider combining IP allowlisting with PIN protection
- PIN entry uses POST requests (not GET) to avoid exposing PINs in browser history or server logs
- Validated PIN sessions use secure, HTTP-only cookies with SameSite=Strict protection

## Configuration

Set these options in the add-on Configuration tab:

| Option | Description |
|--------|-------------|
| **Admin Username** | Username for direct port access. Not needed when using the HA side panel. |
| **Admin Password** | Password for direct port access (min 8 characters). Not needed when using the HA side panel. |
| **App Name** | Display name shown to guests (default: "Home Access") |
| **Contact Message** | Message shown when a guest link expires |
| **Background Color** | Hex color for page background (e.g., `#F2F0E9`) |
| **Primary Color** | Hex color for accents and buttons (e.g., `#D9523C`) |
| **Guest URL** | External base URL for guest links (e.g., `https://guest.myhouse.com`). Leave empty for local network. |
| **Encryption Key** | **Required**: 64-character hex key for PIN encryption. Generate with: `openssl rand -hex 32` |

### Encryption Key Setup

The **Encryption Key** is **required** for HAPass to start. This key is used to encrypt PINs before storing them in the database using AES-256-GCM authenticated encryption.

**Generating a key:**
```bash
openssl rand -hex 32
```

**Example output:**
```
7c4a8d09ca3762af61e59520943dc26494f8941b76b6b25fef0b9f0c56f1c4f2
```

Copy this value into the **Encryption Key** field in the add-on configuration.

**Important:**
- Keep this key secure and back it up — losing it means you cannot decrypt existing PINs
- The key must be exactly 64 hexadecimal characters (0-9, a-f, A-F)
- If you change this key, existing encrypted PINs will become unreadable
- The application will not start without a valid encryption key

## Public API

HAPass exposes a REST API for external integrations. The API is disabled by default for security.

### Enabling the Public API

1. Go to the addon configuration in Home Assistant
2. Set `api_enabled` to `true`
3. Set `api_token` to a secure random string (at least 32 characters)
4. Restart the addon

### Authentication

All API requests must include the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-token-here" \
     https://your-ha-instance:5880/api/v1/tokens
```

### API Documentation

When the API is enabled, interactive documentation is available at:
- Swagger UI: `/api/docs`
- OpenAPI Schema: `/api/openapi.json`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tokens` | List all tokens |
| POST | `/api/v1/tokens` | Create a new token |
| GET | `/api/v1/tokens/{id}` | Get a specific token |
| PATCH | `/api/v1/tokens/{id}` | Update a token |
| DELETE | `/api/v1/tokens/{id}` | Revoke/delete a token |

### Rate Limiting

The API is rate-limited to 100 requests per minute per IP address.

### Security Considerations

- Keep your API token secret
- Use HTTPS in production
- The API has the same permissions as the admin dashboard
- Disable the API when not needed
