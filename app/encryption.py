"""PIN encryption using AES-256-GCM."""
import base64
import binascii
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

# AES-256-GCM parameters
NONCE_SIZE = 12  # 96 bits recommended for GCM
AUTH_TAG_SIZE = 16  # 128 bits
KEY_SIZE = 32  # 256 bits


def _get_key_bytes() -> bytes:
    """Get the encryption key as bytes from settings."""
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY is not configured")
    try:
        key = binascii.unhexlify(settings.encryption_key)
        if len(key) != KEY_SIZE:
            raise ValueError(f"ENCRYPTION_KEY must be {KEY_SIZE * 2} hex characters (got {len(settings.encryption_key)})")
        return key
    except binascii.Error as e:
        raise ValueError(f"ENCRYPTION_KEY must be valid hex: {e}")


def encrypt_pin(plaintext_pin: str) -> str:
    """Encrypt a PIN using AES-256-GCM.

    Args:
        plaintext_pin: The PIN to encrypt

    Returns:
        Base64-encoded ciphertext (nonce + ciphertext + auth_tag)
    """
    key = _get_key_bytes()
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)

    plaintext_bytes = plaintext_pin.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)

    # ciphertext includes auth_tag at the end
    combined = nonce + ciphertext
    return base64.urlsafe_b64encode(combined).decode("ascii")


def decrypt_pin(ciphertext_b64: str) -> str:
    """Decrypt a PIN using AES-256-GCM.

    Args:
        ciphertext_b64: Base64-encoded ciphertext (nonce + ciphertext + auth_tag)

    Returns:
        The decrypted PIN plaintext
    """
    key = _get_key_bytes()

    try:
        combined = base64.urlsafe_b64decode(ciphertext_b64)
    except Exception as e:
        raise ValueError(f"Invalid base64 ciphertext: {e}")

    # Minimum: nonce (12) + auth_tag (16) = 28 bytes for empty plaintext
    if len(combined) < NONCE_SIZE + AUTH_TAG_SIZE:
        raise ValueError("Ciphertext too short")

    nonce = combined[:NONCE_SIZE]
    ciphertext = combined[NONCE_SIZE:]

    aesgcm = AESGCM(key)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext_bytes.decode("utf-8")
