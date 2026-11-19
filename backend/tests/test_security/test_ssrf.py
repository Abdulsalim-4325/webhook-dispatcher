import pytest
from backend.app.core.security import SecurityEngine, SSRFSecurityException


def test_ssrf_rejects_loopback():
    """Verify that localhost and 127.0.0.1 are blocked."""
    with pytest.raises(SSRFSecurityException, match="restricted IP"):
        SecurityEngine.validate_and_resolve_url("http://127.0.0.1:8000/webhook")

    with pytest.raises(SSRFSecurityException, match="restricted IP"):
        SecurityEngine.validate_and_resolve_url("http://localhost:8000/webhook")


def test_ssrf_rejects_cloud_metadata():
    """Verify that AWS/GCP/Azure link-local metadata IP (169.254.169.254) is blocked."""
    with pytest.raises(SSRFSecurityException, match="restricted IP"):
        SecurityEngine.validate_and_resolve_url("http://169.254.169.254/latest/meta-data/")


def test_ssrf_rejects_rfc1918_private_ranges():
    """Verify that internal 10.x and 192.168.x private subnets are blocked."""
    with pytest.raises(SSRFSecurityException, match="restricted IP"):
        SecurityEngine.validate_and_resolve_url("http://10.0.0.5/api")

    with pytest.raises(SSRFSecurityException, match="restricted IP"):
        SecurityEngine.validate_and_resolve_url("http://192.168.1.1:8080/hook")


def test_ssrf_rejects_unsupported_schemes():
    """Verify that non-http/https schemes (file://, ftp://, gopher://) are rejected."""
    with pytest.raises(SSRFSecurityException, match="Unsupported protocol scheme"):
        SecurityEngine.validate_and_resolve_url("file:///etc/passwd")

    with pytest.raises(SSRFSecurityException, match="Unsupported protocol scheme"):
        SecurityEngine.validate_and_resolve_url("ftp://ftp.example.com/data")
