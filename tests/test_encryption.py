"""Tests for PIN encryption module."""
import pytest

from app.encryption import encrypt_pin, decrypt_pin, _get_key_bytes, NONCE_SIZE, KEY_SIZE


class TestEncryptionBasics:
    """Basic encryption/decryption tests."""

    async def test_encrypt_decrypt_roundtrip(self):
        """Encrypting and decrypting returns original plaintext."""
        original_pin = "1234"
        encrypted = encrypt_pin(original_pin)
        decrypted = decrypt_pin(encrypted)
        assert decrypted == original_pin

    async def test_encrypt_produces_different_ciphertexts(self):
        """Same PIN encrypts to different ciphertexts due to random nonce."""
        pin = "5678"
        encrypted1 = encrypt_pin(pin)
        encrypted2 = encrypt_pin(pin)
        assert encrypted1 != encrypted2

    async def test_decrypt_different_pins(self):
        """Different PINs decrypt correctly."""
        pins = ["1234", "567890", "0000", "99999999", "abc123"]
        for pin in pins:
            encrypted = encrypt_pin(pin)
            decrypted = decrypt_pin(encrypted)
            assert decrypted == pin

    async def test_encrypt_empty_string_works(self):
        """Encrypting empty string works and decrypts to empty."""
        encrypted = encrypt_pin("")
        decrypted = decrypt_pin(encrypted)
        assert decrypted == ""


class TestDecryptionErrors:
    """Decryption error handling tests."""

    async def test_decrypt_invalid_base64_raises(self):
        """Decrypting invalid base64 raises ValueError."""
        # Use invalid base64 characters that will cause decode to fail
        with pytest.raises(ValueError, match="Invalid base64"):
            decrypt_pin("not valid base64 ~`^&*()")

    async def test_decrypt_too_short_ciphertext_raises(self):
        """Decrypting too short data raises ValueError."""
        import base64
        short_data = base64.urlsafe_b64encode(b"short").decode("ascii")
        with pytest.raises(ValueError, match="too short"):
            decrypt_pin(short_data)

    async def test_decrypt_tampered_ciphertext_raises(self):
        """Decrypting tampered data raises exception (auth tag verification)."""
        import base64
        original_pin = "1234"
        encrypted = encrypt_pin(original_pin)
        # Decode, modify a byte, re-encode
        data = base64.urlsafe_b64decode(encrypted)
        modified = data[:-5] + bytes([data[-5] ^ 0xFF]) + data[-4:]
        tampered = base64.urlsafe_b64encode(modified).decode("ascii")
        with pytest.raises(Exception):
            decrypt_pin(tampered)


class TestKeyHandling:
    """Encryption key handling tests."""

    async def test_get_key_bytes_returns_correct_length(self):
        """Key is decoded to correct byte length."""
        key_bytes = _get_key_bytes()
        assert len(key_bytes) == KEY_SIZE

    async def test_key_is_32_bytes(self):
        """KEY_SIZE constant is 32 bytes (256 bits)."""
        assert KEY_SIZE == 32


class TestNonceHandling:
    """Nonce generation and handling tests."""

    async def test_nonce_size_constant(self):
        """NONCE_SIZE constant is 12 bytes (96 bits)."""
        assert NONCE_SIZE == 12

    async def test_encrypt_includes_nonce(self):
        """Encrypted output includes nonce prefix."""
        import base64
        encrypted = encrypt_pin("1234")
        data = base64.urlsafe_b64decode(encrypted)
        # Data should be: nonce (12) + ciphertext + auth_tag (16)
        assert len(data) > NONCE_SIZE + 16
