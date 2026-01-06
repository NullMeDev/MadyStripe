"""
MadyStripe Core Module
Unified card checking system with multiple gateways
Now with Shopify Price Gateways integrated!
"""

__version__ = "3.1.0"
__author__ = "@MissNullMe"

# Import main components
from .gateways import (
    Gateway,
    GatewayManager,
    get_gateway_manager,
    check_card,
    list_gateways,
    StaleksGateway,
    ShopifyOptimizedGateway,
    ShopifyPennyGatewayWrapper,
    ShopifyLowGatewayWrapper,
    ShopifyMediumGatewayWrapper,
    ShopifyHighGatewayWrapper,
)

from .checker import (
    CardChecker,
    CardResult,
    CheckerStats,
    validate_card_format,
    load_cards_from_file,
    save_results,
)

# Import Shopify price gateways directly
try:
    from .shopify_price_gateways import (
        ShopifyPennyGateway,
        ShopifyLowGateway,
        ShopifyMediumGateway,
        ShopifyHighGateway,
        check_card_penny,
        check_card_low,
        check_card_medium,
        check_card_high,
    )
    SHOPIFY_GATES_AVAILABLE = True
except ImportError:
    SHOPIFY_GATES_AVAILABLE = False

__all__ = [
    # Gateway classes
    'Gateway',
    'GatewayManager',
    'get_gateway_manager',
    'check_card',
    'list_gateways',
    'StaleksGateway',
    'ShopifyOptimizedGateway',
    'ShopifyPennyGatewayWrapper',
    'ShopifyLowGatewayWrapper',
    'ShopifyMediumGatewayWrapper',
    'ShopifyHighGatewayWrapper',
    
    # Checker classes
    'CardChecker',
    'CardResult',
    'CheckerStats',
    'validate_card_format',
    'load_cards_from_file',
    'save_results',
    
    # Shopify price gateways (if available)
    'SHOPIFY_GATES_AVAILABLE',
]

if SHOPIFY_GATES_AVAILABLE:
    __all__.extend([
        'ShopifyPennyGateway',
        'ShopifyLowGateway',
        'ShopifyMediumGateway',
        'ShopifyHighGateway',
        'check_card_penny',
        'check_card_low',
        'check_card_medium',
        'check_card_high',
    ])
