import time
from backend.app.core.security import SecurityEngine


def test_hmac_signature_generation_and_verification():
    """Verify standard HMAC-SHA256 generation matches verification."""
    payload = b'{"event":"order.placed","total":1500}'
    secret = "test_super_secret_webhook_key_12345"
    now = int(time.time())

    sig = SecurityEngine.generate_hmac_signature(payload, secret, now)
    header_val = f"t={now},v1={sig}"

    is_valid = SecurityEngine.verify_signature(payload, secret, header_val, tolerance_seconds=300)
    assert is_valid is True


def test_hmac_signature_rejects_tampered_payload():
    """Verify signature verification fails if payload has been modified in flight."""
    payload = b'{"event":"order.placed","total":1500}'
    tampered_payload = b'{"event":"order.placed","total":9999}'
    secret = "test_super_secret_webhook_key_12345"
    now = int(time.time())

    sig = SecurityEngine.generate_hmac_signature(payload, secret, now)
    header_val = f"t={now},v1={sig}"

    is_valid = SecurityEngine.verify_signature(tampered_payload, secret, header_val)
    assert is_valid is False


def test_hmac_signature_rejects_expired_timestamp():
    """Verify signatures older than tolerance window (e.g. 300s) are rejected as replay attacks."""
    payload = b'{"event":"order.placed"}'
    secret = "test_super_secret_webhook_key_12345"
    stale_timestamp = int(time.time()) - 600  # 10 minutes ago

    sig = SecurityEngine.generate_hmac_signature(payload, secret, stale_timestamp)
    header_val = f"t={stale_timestamp},v1={sig}"

    is_valid = SecurityEngine.verify_signature(payload, secret, header_val, tolerance_seconds=300)
    assert is_valid is False
