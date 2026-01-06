"""
Shopify Dynamic Price Gateways
Uses Smart Gateway system with real payment processing
NO STUB FUNCTIONS - All payments are real!

Features:
- Automatic store selection from 9,597 validated stores
- Dynamic product finding at runtime
- Real GraphQL payment processing
- Automatic fallback on store failure
- Success rate tracking
"""

from typing import Tuple, Optional
from .shopify_smart_gateway import (
    ShopifyPennyGate,
    ShopifyFiveDollarGate,
    ShopifyTwentyDollarGate,
    ShopifyHundredDollarGate
)


class DynamicShopifyPennyGateway:
    """
    Dynamic $0.01 Shopify Gateway
    Automatically selects stores and products from database
    """
    
    def __init__(self):
        self.gateway = ShopifyPennyGate()
        self.name = "Shopify Dynamic Penny Gate"
        self.charge_amount = "$0.01-$1.00"
        self.description = "Dynamic penny test with 9,597 stores"
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Check card with automatic store/product selection
        
        Args:
            card: Card in format "NUMBER|MM|YY|CVC"
            proxy: Optional proxy (not yet implemented)
        
        Returns:
            (status, message, card_type)
        """
        return self.gateway.check(card, max_attempts=3)
    
    def get_stats(self):
        """Get gateway statistics"""
        return self.gateway.get_stats()


class DynamicShopifyFiveDollarGateway:
    """
    Dynamic $5 Shopify Gateway
    Automatically selects stores and products from database
    """
    
    def __init__(self):
        self.gateway = ShopifyFiveDollarGate()
        self.name = "Shopify Dynamic $5 Gate"
        self.charge_amount = "$3.00-$7.00"
        self.description = "Dynamic $5 test with 9,597 stores"
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """Check card with automatic store/product selection"""
        return self.gateway.check(card, max_attempts=3)
    
    def get_stats(self):
        """Get gateway statistics"""
        return self.gateway.get_stats()


class DynamicShopifyTwentyDollarGateway:
    """
    Dynamic $20 Shopify Gateway
    Automatically selects stores and products from database
    """
    
    def __init__(self):
        self.gateway = ShopifyTwentyDollarGate()
        self.name = "Shopify Dynamic $20 Gate"
        self.charge_amount = "$15.00-$25.00"
        self.description = "Dynamic $20 test with 9,597 stores"
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """Check card with automatic store/product selection"""
        return self.gateway.check(card, max_attempts=3)
    
    def get_stats(self):
        """Get gateway statistics"""
        return self.gateway.get_stats()


class DynamicShopifyHundredDollarGateway:
    """
    Dynamic $100 Shopify Gateway
    Automatically selects stores and products from database
    """
    
    def __init__(self):
        self.gateway = ShopifyHundredDollarGate()
        self.name = "Shopify Dynamic $100 Gate"
        self.charge_amount = "$80.00-$120.00"
        self.description = "Dynamic $100 test with 9,597 stores"
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """Check card with automatic store/product selection"""
        return self.gateway.check(card, max_attempts=3)
    
    def get_stats(self):
        """Get gateway statistics"""
        return self.gateway.get_stats()


# Convenience functions for easy access
def check_card_penny(card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
    """Check card with dynamic penny gate"""
    gateway = DynamicShopifyPennyGateway()
    return gateway.check(card, proxy)


def check_card_five(card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
    """Check card with dynamic $5 gate"""
    gateway = DynamicShopifyFiveDollarGateway()
    return gateway.check(card, proxy)


def check_card_twenty(card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
    """Check card with dynamic $20 gate"""
    gateway = DynamicShopifyTwentyDollarGateway()
    return gateway.check(card, proxy)


def check_card_hundred(card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
    """Check card with dynamic $100 gate"""
    gateway = DynamicShopifyHundredDollarGateway()
    return gateway.check(card, proxy)


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY DYNAMIC PRICE GATEWAYS")
    print("="*70)
    print("\n✨ Features:")
    print("  • Automatic store selection from 9,597 validated stores")
    print("  • Dynamic product finding at runtime")
    print("  • Real GraphQL payment processing (NO STUBS!)")
    print("  • Automatic fallback on store failure")
    print("  • Success rate tracking")
    
    print("\n💰 Available Gates:")
    
    gates = [
        DynamicShopifyPennyGateway(),
        DynamicShopifyFiveDollarGateway(),
        DynamicShopifyTwentyDollarGateway(),
        DynamicShopifyHundredDollarGateway(),
    ]
    
    for gate in gates:
        print(f"\n  {gate.name}")
        print(f"    Amount: {gate.charge_amount}")
        print(f"    Description: {gate.description}")
    
    print("\n" + "="*70)
    print("⚠️  WARNING: These gates process REAL payments!")
    print("Only use with test cards or cards you own.")
    print("="*70)
