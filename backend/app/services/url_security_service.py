import socket
import ipaddress
import urllib.parse
from typing import List, Optional
from app.config import settings

class URLSecurityService:
    """
    SSRF Protection Service validating HTTP protocols, host DNS resolution,
    loopback addresses, RFC 1918 private ranges, and domain allowlists.
    """

    @classmethod
    def validate_url(cls, url: str, allowed_domains: Optional[List[str]] = None) -> bool:
        if not url:
            raise ValueError("URL cannot be empty.")

        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as err:
            raise ValueError(f"Malformed URL structure: {str(err)}")

        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"Invalid URL scheme: '{parsed.scheme}'. Only HTTP and HTTPS schemes are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL hostname is missing or invalid.")

        hostname_lower = hostname.lower()

        # Enforce Allowed Domain Allowlist check if list is specified
        if allowed_domains:
            allowed_clean = [d.lower() for d in allowed_domains]
            is_allowed = False

            # Allow fallback for local mock portal development
            if hostname_lower in ["localhost", "127.0.0.1"] and settings.ALLOW_LOCAL_URLS_FOR_DEV:
                is_allowed = True
            else:
                for allowed in allowed_clean:
                    if allowed.startswith("*."):
                        suffix = allowed[2:]
                        if hostname_lower == suffix or hostname_lower.endswith("." + suffix):
                            is_allowed = True
                            break
                    elif hostname_lower == allowed:
                        is_allowed = True
                        break

            if not is_allowed:
                raise ValueError(f"Domain '{hostname}' is not allowed by application safety constraints.")

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            ips = {info[4][0] for info in addr_info}
        except socket.gaierror as e:
            if settings.ALLOW_LOCAL_URLS_FOR_DEV:
                ips = {"127.0.0.1"}
            else:
                raise ValueError(f"DNS Resolution failed for domain '{hostname}': {str(e)}")

        for ip_str in ips:
            # Strip scope id if IPv6 link-local
            if "%" in ip_str:
                ip_str = ip_str.split("%")[0]

            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                raise ValueError(f"Invalid IP address format resolved: {ip_str}")

            # Strict block for cloud metadata IP in all environments (including dev)
            if ip_str == "169.254.169.254":
                raise ValueError(f"Outbound connection to metadata endpoint {ip_str} is blocked.")

            # In development/test mode, we allow local host loopback connection
            if settings.ALLOW_LOCAL_URLS_FOR_DEV:
                continue

            if ip.is_loopback:
                raise ValueError(f"Outbound connection to loopback IP {ip_str} is blocked.")
            if ip.is_private:
                raise ValueError(f"Outbound connection to private network IP {ip_str} is blocked (SSRF protection).")
            if ip.is_link_local:
                raise ValueError(f"Outbound connection to link-local IP {ip_str} is blocked.")
            if ip.is_multicast:
                raise ValueError(f"Outbound connection to multicast IP {ip_str} is blocked.")

        return True
