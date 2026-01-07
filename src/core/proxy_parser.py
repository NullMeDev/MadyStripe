"""
Proxy Parser Utility
Handles multiple proxy formats and converts them to standard format
"""

import re
from typing import Optional, Tuple


class ProxyParser:
    """
    Parse and normalize proxy strings from various formats
    """
    
    @staticmethod
    def parse(proxy_string: str, default_protocol: str = 'http') -> Optional[str]:
        """
        Parse proxy string and return in standard format
        
        Supported formats:
        1. http://user:pass@host:port
        2. socks5://user:pass@host:port
        3. user:pass@host:port (adds http://)
        4. host:port:user:pass (converts to http://user:pass@host:port)
        5. host:port (no auth, adds http://)
        
        Args:
            proxy_string: Proxy in any supported format
            default_protocol: Protocol to use if not specified (default: http)
        
        Returns:
            Proxy in standard format: protocol://user:pass@host:port
            or None if invalid
        """
        if not proxy_string or not isinstance(proxy_string, str):
            return None
        
        proxy_string = proxy_string.strip()
        
        # Format 1 & 2: Already in standard format (protocol://user:pass@host:port)
        if '://' in proxy_string:
            # Validate it has the right structure
            if '@' in proxy_string and ':' in proxy_string:
                return proxy_string
            # No auth: protocol://host:port
            elif proxy_string.count(':') == 2:  # protocol://host:port
                return proxy_string
            return None
        
        # Count colons to determine format
        colon_count = proxy_string.count(':')
        
        # Format 3: user:pass@host:port
        if '@' in proxy_string and colon_count == 3:
            # user:pass@host:port -> http://user:pass@host:port
            return f"{default_protocol}://{proxy_string}"
        
        # Format 4: host:port:user:pass (alternative format)
        elif colon_count == 3 and '@' not in proxy_string:
            parts = proxy_string.split(':')
            if len(parts) == 4:
                host, port, user, password = parts
                # Validate port is numeric
                try:
                    int(port)
                    return f"{default_protocol}://{user}:{password}@{host}:{port}"
                except ValueError:
                    return None
        
        # Format 5: host:port (no auth)
        elif colon_count == 1 and '@' not in proxy_string:
            parts = proxy_string.split(':')
            if len(parts) == 2:
                host, port = parts
                # Validate port is numeric
                try:
                    int(port)
                    return f"{default_protocol}://{host}:{port}"
                except ValueError:
                    return None
        
        return None
    
    @staticmethod
    def parse_to_dict(proxy_string: str) -> Optional[dict]:
        """
        Parse proxy and return as dict for requests library
        
        Returns:
            {'http': 'protocol://user:pass@host:port',
             'https': 'protocol://user:pass@host:port'}
        """
        parsed = ProxyParser.parse(proxy_string)
        if not parsed:
            return None
        
        return {
            'http': parsed,
            'https': parsed
        }
    
    @staticmethod
    def extract_components(proxy_string: str) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
        """
        Extract proxy components
        
        Returns:
            (protocol, host, port, username, password) or None
        """
        parsed = ProxyParser.parse(proxy_string)
        if not parsed:
            return None
        
        # Parse standard format: protocol://[user:pass@]host:port
        match = re.match(r'(\w+)://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', parsed)
        if not match:
            return None
        
        protocol, user, password, host, port = match.groups()
        return (protocol, host, port, user, password)
    
    @staticmethod
    def test_formats():
        """Test various proxy formats"""
        test_cases = [
            # Format 1: Standard with protocol
            "http://user:pass@proxy.com:8080",
            "socks5://user:pass@proxy.com:1080",
            
            # Format 2: Standard without protocol
            "user:pass@proxy.com:8080",
            
            # Format 3: Alternative format (host:port:user:pass)
            "proxy.com:8080:user:pass",
            "evo-pro.porterproxies.com:62345:PP_5J7SVIL0BJ-country-US-state-Florida:95cc2n4b",
            
            # Format 4: No auth
            "proxy.com:8080",
            
            # Format 5: Complex usernames
            "user_pinta:1acNvmOToR6d-country-US-state-Washington-city-Benton@residential.ip9.io:8000",
        ]
        
        print("="*70)
        print("PROXY PARSER TEST")
        print("="*70)
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. Input: {test}")
            parsed = ProxyParser.parse(test)
            if parsed:
                print(f"   ✅ Parsed: {parsed}")
                components = ProxyParser.extract_components(test)
                if components:
                    protocol, host, port, user, password = components
                    print(f"   Protocol: {protocol}")
                    print(f"   Host: {host}")
                    print(f"   Port: {port}")
                    if user:
                        print(f"   User: {user}")
                        print(f"   Pass: {password}")
            else:
                print(f"   ❌ Failed to parse")


if __name__ == "__main__":
    ProxyParser.test_formats()
