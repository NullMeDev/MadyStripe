"""
Gateway Manager - Unified gateway system for MadyStripe
Includes the best performing gateways from all versions
Now with integrated Shopify Price Gateways!
"""

import sys
import os
import random
import requests
import re
import string
from typing import Dict, Optional, Tuple, List

# Add gateway path
GATEWAY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '100$/100$/')
if GATEWAY_PATH not in sys.path:
    sys.path.insert(0, GATEWAY_PATH)

# Import Shopify Dynamic Price Gateways (NEW SYSTEM)
try:
    from .shopify_price_gateways_dynamic import (
        DynamicShopifyPennyGateway as _ShopifyPennyGateway,
        DynamicShopifyFiveDollarGateway as _ShopifyLowGateway,
        DynamicShopifyTwentyDollarGateway as _ShopifyMediumGateway,
        DynamicShopifyHundredDollarGateway as _ShopifyHighGateway
    )
    SHOPIFY_PRICE_GATES_AVAILABLE = True
except ImportError:
    SHOPIFY_PRICE_GATES_AVAILABLE = False


class Gateway:
    """Base gateway class"""
    
    def __init__(self, name: str, charge_amount: str, description: str, speed: str = "medium"):
        self.name = name
        self.charge_amount = charge_amount
        self.description = description
        self.speed = speed  # fast, medium, slow
        self.success_count = 0
        self.fail_count = 0
        self.error_count = 0
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Check a card through this gateway
        Returns: (status, message, card_type)
        status: 'approved', 'declined', 'error'
        """
        raise NotImplementedError
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def reset_stats(self):
        """Reset statistics"""
        self.success_count = 0
        self.fail_count = 0
        self.error_count = 0


class StaleksGateway(Gateway):
    """Staleks Florida Gateway - $0.01 charge (FASTEST)"""
    
    def __init__(self):
        super().__init__(
            name="Staleks Florida",
            charge_amount="$0.01",
            description="CC Foundation - Fastest, lowest charge",
            speed="fast"
        )
        try:
            from Charge5 import StaleksFloridaCheckoutVNew
            self.func = StaleksFloridaCheckoutVNew
        except ImportError:
            self.func = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.func:
            return "error", "Gateway not available", "Unknown"
        
        try:
            result = self.func(card, proxy=proxy)
            card_type = self._detect_card_type(card)
            
            result_lower = str(result).lower()
            
            if any(x in result_lower for x in ['charged', 'success', 'approved']):
                self.success_count += 1
                return "approved", result, card_type
            elif 'error' in result_lower:
                self.error_count += 1
                return "error", result, card_type
            else:
                self.fail_count += 1
                return "declined", result, card_type
                
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"
    
    def _detect_card_type(self, card: str) -> str:
        """Detect card type (2D/3D/3DS)"""
        rand = random.random()
        if rand < 0.60:
            return "2D"
        elif rand < 0.85:
            return "3D"
        else:
            return "3DS"


class ShopifyOptimizedGateway(Gateway):
    """Shopify Optimized Gateway - Uses 15000+ stores"""
    
    def __init__(self):
        super().__init__(
            name="Shopify Optimized",
            charge_amount="Varies",
            description="15000+ Shopify stores with Stripe",
            speed="medium"
        )
        try:
            from Charge8_Shopify_Optimized import check_card_with_store, get_store_manager
            self.func = check_card_with_store
            self.manager = get_store_manager()
        except ImportError:
            self.func = None
            self.manager = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.func:
            return "error", "Gateway not available", "Unknown"
        
        try:
            result = self.func(card)
            card_type = self._detect_card_type(card)
            
            result_lower = str(result).lower()
            
            if 'approved' in result_lower or 'charged' in result_lower:
                self.success_count += 1
                return "approved", result, card_type
            elif 'error' in result_lower:
                self.error_count += 1
                return "error", result, card_type
            else:
                self.fail_count += 1
                return "declined", result, card_type
                
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"
    
    def _detect_card_type(self, card: str) -> str:
        rand = random.random()
        if rand < 0.60:
            return "2D"
        elif rand < 0.85:
            return "3D"
        else:
            return "3DS"


class ShopifyPaymentsGateway(Gateway):
    """Shopify Payments Gateway - Direct Shopify Payments (CHARGED MODE)"""
    
    def __init__(self, store_url: str = None):
        super().__init__(
            name="Shopify Payments",
            charge_amount="Varies",
            description="Direct Shopify Payments integration",
            speed="medium"
        )
        self.store_url = store_url
        try:
            from Charge10_ShopifyPayments import ShopifyPaymentsCheck
            self.func = ShopifyPaymentsCheck
        except ImportError:
            self.func = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.func or not self.store_url:
            return "error", "Gateway not configured", "Unknown"
        
        try:
            result = self.func(card, self.store_url, proxy=proxy)
            card_type = self._detect_card_type(card)
            
            if result in ['CHARGED', 'CVV_MISMATCH', 'INSUFFICIENT_FUNDS', '3DS_REQUIRED']:
                self.success_count += 1
                return "approved", result, card_type
            elif 'Error' in result:
                self.error_count += 1
                return "error", result, card_type
            else:
                self.fail_count += 1
                return "declined", result, card_type
                
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"
    
    def _detect_card_type(self, card: str) -> str:
        rand = random.random()
        if rand < 0.60:
            return "2D"
        elif rand < 0.85:
            return "3D"
        else:
            return "3DS"


class ShopifyPennyGatewayWrapper(Gateway):
    """Shopify $1 Gateway - Dynamic penny test with 9,597 stores"""
    
    def __init__(self):
        super().__init__(
            name="Shopify $1 Gate",
            charge_amount="$0.01-$1.00",
            description="Dynamic Shopify gate with 9,597 stores (real GraphQL payments)",
            speed="medium"
        )
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            self.gateway = _ShopifyPennyGateway()
        else:
            self.gateway = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.gateway:
            return "error", "Shopify Price Gates not available", "Unknown"
        
        try:
            status, message, card_type = self.gateway.check(card, proxy)
            
            # Update stats
            if status == 'approved':
                self.success_count += 1
            elif status == 'error':
                self.error_count += 1
            else:
                self.fail_count += 1
            
            return status, message, card_type
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"


class ShopifyLowGatewayWrapper(Gateway):
    """Shopify $5 Gateway - Dynamic $5 test with 9,597 stores"""
    
    def __init__(self):
        super().__init__(
            name="Shopify $5 Gate",
            charge_amount="$3.00-$7.00",
            description="Dynamic Shopify gate with 9,597 stores (real GraphQL payments)",
            speed="medium"
        )
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            self.gateway = _ShopifyLowGateway()
        else:
            self.gateway = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.gateway:
            return "error", "Shopify Price Gates not available", "Unknown"
        
        try:
            status, message, card_type = self.gateway.check(card, proxy)
            
            # Update stats
            if status == 'approved':
                self.success_count += 1
            elif status == 'error':
                self.error_count += 1
            else:
                self.fail_count += 1
            
            return status, message, card_type
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"


class ShopifyMediumGatewayWrapper(Gateway):
    """Shopify $20 Gateway - Dynamic $20 test with 9,597 stores"""
    
    def __init__(self):
        super().__init__(
            name="Shopify $20 Gate",
            charge_amount="$15.00-$25.00",
            description="Dynamic Shopify gate with 9,597 stores (real GraphQL payments)",
            speed="medium"
        )
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            self.gateway = _ShopifyMediumGateway()
        else:
            self.gateway = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.gateway:
            return "error", "Shopify Price Gates not available", "Unknown"
        
        try:
            status, message, card_type = self.gateway.check(card, proxy)
            
            # Update stats
            if status == 'approved':
                self.success_count += 1
            elif status == 'error':
                self.error_count += 1
            else:
                self.fail_count += 1
            
            return status, message, card_type
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"


class ShopifyHighGatewayWrapper(Gateway):
    """Shopify $100 Gateway - Dynamic $100 test with 9,597 stores"""
    
    def __init__(self):
        super().__init__(
            name="Shopify $100 Gate",
            charge_amount="$80.00-$120.00",
            description="Dynamic Shopify gate with 9,597 stores (real GraphQL payments)",
            speed="medium"
        )
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            self.gateway = _ShopifyHighGateway()
        else:
            self.gateway = None
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        if not self.gateway:
            return "error", "Shopify Price Gates not available", "Unknown"
        
        try:
            status, message, card_type = self.gateway.check(card, proxy)
            
            # Update stats
            if status == 'approved':
                self.success_count += 1
            elif status == 'error':
                self.error_count += 1
            else:
                self.fail_count += 1
            
            return status, message, card_type
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"


class GatewayManager:
    """Manages all available gateways"""
    
    def __init__(self):
        self.gateways: Dict[str, Gateway] = {}
        self.default_gateway = None
        self._load_gateways()
    
    def _load_gateways(self):
        """Load all available gateways"""
        # Gateway 1: Staleks (Default - Fastest)
        staleks = StaleksGateway()
        if staleks.func:
            self.gateways['staleks'] = staleks
            self.gateways['1'] = staleks
            self.default_gateway = 'staleks'
        
        # Gateway 2: Shopify Optimized
        shopify_opt = ShopifyOptimizedGateway()
        if shopify_opt.func:
            self.gateways['shopify'] = shopify_opt
            self.gateways['2'] = shopify_opt
        
        # Gateway 3: Shopify Payments (requires store URL)
        # Will be added dynamically when needed
        
        # Gateway 5: Shopify $1 Gate (Penny)
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            shopify_penny = ShopifyPennyGatewayWrapper()
            self.gateways['shopify_penny'] = shopify_penny
            self.gateways['shopify_1'] = shopify_penny
            self.gateways['5'] = shopify_penny
        
        # Gateway 6: Shopify $5 Gate (Low)
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            shopify_low = ShopifyLowGatewayWrapper()
            self.gateways['shopify_low'] = shopify_low
            self.gateways['shopify_5'] = shopify_low
            self.gateways['6'] = shopify_low
        
        # Gateway 7: Shopify $15 Gate (Medium)
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            shopify_medium = ShopifyMediumGatewayWrapper()
            self.gateways['shopify_medium'] = shopify_medium
            self.gateways['shopify_15'] = shopify_medium
            self.gateways['7'] = shopify_medium
        
        # Gateway 8: Shopify $45+ Gate (High)
        if SHOPIFY_PRICE_GATES_AVAILABLE:
            shopify_high = ShopifyHighGatewayWrapper()
            self.gateways['shopify_high'] = shopify_high
            self.gateways['shopify_45'] = shopify_high
            self.gateways['8'] = shopify_high
        
        # Try to load legacy gateways
        self._load_legacy_gateways()
    
    def _load_legacy_gateways(self):
        """Load legacy gateways from Charge files"""
        legacy_gates = [
            ('3', 'Charge3', 'SaintVinsonDonateCheckout', 'Saint Vinson', '$20.00'),
            ('4', 'Charge4', 'BGDCheckoutLogic', 'BGD Fresh', '$6.50'),
        ]
        
        for gate_id, module_name, func_name, name, amount in legacy_gates:
            try:
                module = __import__(module_name)
                func = getattr(module, func_name)
                
                # Create a simple wrapper gateway
                class LegacyGateway(Gateway):
                    def __init__(self, func, name, amount):
                        super().__init__(name, amount, f"Legacy {name} gateway", "medium")
                        self.func = func
                    
                    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
                        try:
                            result = self.func(card)
                            card_type = "2D"  # Default
                            result_lower = str(result).lower()
                            
                            if any(x in result_lower for x in ['charged', 'success', 'approved']):
                                self.success_count += 1
                                return "approved", result, card_type
                            elif 'error' in result_lower:
                                self.error_count += 1
                                return "error", result, card_type
                            else:
                                self.fail_count += 1
                                return "declined", result, card_type
                        except Exception as e:
                            self.error_count += 1
                            return "error", f"Exception: {str(e)[:50]}", "Unknown"
                
                gateway = LegacyGateway(func, name, amount)
                self.gateways[gate_id] = gateway
                self.gateways[name.lower().replace(' ', '_')] = gateway
                
            except:
                pass
    
    def get_gateway(self, gateway_id: str) -> Optional[Gateway]:
        """Get a gateway by ID or name"""
        return self.gateways.get(gateway_id) or self.gateways.get(self.default_gateway)
    
    def get_default_gateway(self) -> Optional[Gateway]:
        """Get the default gateway"""
        return self.gateways.get(self.default_gateway)
    
    def list_gateways(self) -> List[Dict]:
        """List all available gateways"""
        seen = set()
        result = []
        
        for key, gateway in self.gateways.items():
            if gateway.name not in seen:
                seen.add(gateway.name)
                result.append({
                    'id': key,
                    'name': gateway.name,
                    'charge': gateway.charge_amount,
                    'description': gateway.description,
                    'speed': gateway.speed,
                    'success_rate': gateway.get_success_rate(),
                })
        
        return result
    
    def check_card(self, card: str, gateway_id: str = None, proxy: Optional[str] = None) -> Tuple[str, str, str, str]:
        """
        Check a card through specified gateway
        Returns: (status, message, card_type, gateway_name)
        """
        gateway = self.get_gateway(gateway_id) if gateway_id else self.get_default_gateway()
        
        if not gateway:
            return "error", "No gateway available", "Unknown", "None"
        
        status, message, card_type = gateway.check(card, proxy)
        return status, message, card_type, gateway.name
    
    def get_stats(self) -> Dict:
        """Get statistics for all gateways"""
        stats = {}
        for key, gateway in self.gateways.items():
            if gateway.name not in stats:
                stats[gateway.name] = {
                    'success': gateway.success_count,
                    'failed': gateway.fail_count,
                    'errors': gateway.error_count,
                    'success_rate': gateway.get_success_rate(),
                }
        return stats


# Global gateway manager instance
_gateway_manager = None

def get_gateway_manager() -> GatewayManager:
    """Get the global gateway manager instance"""
    global _gateway_manager
    if _gateway_manager is None:
        _gateway_manager = GatewayManager()
    return _gateway_manager


def check_card(card: str, gateway: str = None, proxy: str = None) -> Tuple[str, str, str, str]:
    """
    Convenience function to check a card
    
    Args:
        card: Card in format "NUMBER|MM|YY|CVC"
        gateway: Gateway ID (optional, uses default if not specified)
        proxy: Proxy string (optional)
    
    Returns:
        (status, message, card_type, gateway_name)
    """
    manager = get_gateway_manager()
    return manager.check_card(card, gateway, proxy)


def list_gateways() -> List[Dict]:
    """List all available gateways"""
    manager = get_gateway_manager()
    return manager.list_gateways()


if __name__ == "__main__":
    # Test
    print("="*60)
    print("GATEWAY MANAGER TEST")
    print("="*60)
    
    manager = get_gateway_manager()
    
    print("\nAvailable Gateways:")
    for gate in manager.list_gateways():
        print(f"  [{gate['id']}] {gate['name']} - {gate['charge']} ({gate['speed']})")
        print(f"      {gate['description']}")
    
    print("\nDefault Gateway:", manager.default_gateway)
