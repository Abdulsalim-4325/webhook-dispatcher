import hashlib
import hmac
import ipaddress
import socket
import time
from urllib.parse import urlparse


class SSRFSecurityException(Exception):
    """Raised when an outbound URL resolves to a protected, loopback, or private IP address."""
    pass


class SecurityEngine:
    """Enterprise-grade security controls for outbound HTTP dispatching."""

    FORBIDDEN_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),          # Current network
        ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
        ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space
        ipaddress.ip_network("127.0.0.0/8"),        # Loopback
        ipaddress.ip_network("169.254.0.0/16"),     # Link-Local (Cloud Metadata API!)
        ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
        ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
        ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
        ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
        ipaddress.ip_network("198.18.0.0/15"),      # Network Interconnect Benchmarking
        ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
        ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
        ipaddress.ip_network("224.0.0.0/4"),        # Multicast
        ipaddress.ip_network("240.0.0.0/4"),        # Reserved
        ipaddress.ip_network("255.255.255.255/32"), # Broadcast
        # IPv6 blocks
        ipaddress.ip_network("::/128"),             # Unspecified
        ipaddress.ip_network("::1/128"),            # Loopback
        ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
        ipaddress.ip_network("fe80::/10"),          # Link-Local Unicast
    ]

    @classmethod
    def validate_and_resolve_url(cls, target_url: str) -> str:
        """
        Validates target URL against SSRF attacks.
        Resolves the hostname to IP addresses and verifies that no IP falls
        into any reserved, loopback, or cloud-internal CIDR block.
        Returns the validated resolved IP string.
        """
        parsed = urlparse(target_url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFSecurityException(f"Unsupported protocol scheme: '{parsed.scheme}'. Only HTTP/HTTPS allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFSecurityException("Missing destination hostname in URL.")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        try:
            addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except socket.gaierror as err:
            raise SSRFSecurityException(f"DNS resolution failure for host '{hostname}': {err}")

        for family, _, _, _, sockaddr in addr_info:
            raw_ip = sockaddr[0]
            ip_obj = ipaddress.ip_address(raw_ip)

            for forbidden_net in cls.FORBIDDEN_NETWORKS:
                if ip_obj in forbidden_net:
                    raise SSRFSecurityException(
                        f"SSRF Violation: Target host '{hostname}' resolved to restricted IP: {raw_ip}"
                    )

        # Return the first validated IP address for connection binding
        return addr_info[0][4][0]

    @staticmethod
    def generate_hmac_signature(payload_bytes: bytes, secret: str, timestamp: int) -> str:
        """
        Signs the payload using HMAC-SHA256 according to modern API security standards.
        Prepends the timestamp to payload bytes to invalidate replay attacks:
        signature = HMAC-SHA256(secret, f"t={timestamp}.{payload_bytes}")
        """
        signed_payload = f"t={timestamp}.".encode("utf-8") + payload_bytes
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=signed_payload,
            digestmod=hashlib.sha256,
        )
        return mac.hexdigest()

    @staticmethod
    def verify_signature(
        payload_bytes: bytes,
        secret: str,
        received_header: str,
        tolerance_seconds: int = 300,
    ) -> bool:
        """
        Validates an incoming signature header: 't=1700000000,v1=abcdef...'.
        Rejects signatures with timestamps exceeding the drift tolerance.
        Uses constant-time comparison to prevent timing attacks.
        """
        try:
            parts = dict(item.split("=", 1) for item in received_header.split(","))
            timestamp = int(parts["t"])
            received_signature = parts["v1"]
        except (ValueError, KeyError):
            return False

        # Replay attack mitigation
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance_seconds:
            return False

        expected_signature = SecurityEngine.generate_hmac_signature(payload_bytes, secret, timestamp)
        return hmac.compare_digest(expected_signature, received_signature)
