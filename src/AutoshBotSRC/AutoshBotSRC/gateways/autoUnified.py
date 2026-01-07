"""
AutoUnified Gateway - Unified Gateway Manager
Automatically selects the best gateway (Stripe or Shopify) with fallback
Command: /auto
"""

import aiohttp
import random
from commands.base_command import BaseCommand, CommandType
from .autoStripe import process_card as stripe_process
from .autoShopify_fixed import process_card as shopify_process, fetchProducts

# Gateway priority configuration
GATEWAY_CONFIG = {
    'stripe': {
        'name': 'Stripe (CC Foundation)',
        'priority': 1,  # Higher priority = tried first
        'requires_site': False,
        'requires_proxy': False,
        'charge_amount': '$1.00',
    },
    'shopify': {
        'name': 'Shopify',
        'priority': 2,
        'requires_site': True,
        'requires_proxy': True,
        'charge_amount': 'Variable',
    }
}


async def process_card(cc, mes, ano, cvv, site=None, proxies=None):
    """
    Process a card through the unified gateway system
    
    Strategy:
    1. If site is provided, try Shopify first
    2. If no site or Shopify fails, try Stripe
    3. Return the first successful result
    
    Args:
        cc: Card number
        mes: Expiry month (MM)
        ano: Expiry year (YY or YYYY)
        cvv: CVV code
        site: Optional ShopifySite object for Shopify
        proxies: Optional proxy list
    
    Returns:
        tuple: (success, message, gateway_name) or (success, message, gateway, amount, currency)
    """
    results = []
    gateway_used = "Unified"
    
    # Determine gateway order based on available resources
    if site and proxies:
        # Try Shopify first if site is configured
        gateways = ['shopify', 'stripe']
    else:
        # Default to Stripe (doesn't require site/proxy)
        gateways = ['stripe', 'shopify']
    
    for gateway in gateways:
        try:
            if gateway == 'stripe':
                print(f"[Unified] Trying Stripe gateway...")
                result = await stripe_process(cc, mes, ano, cvv, site, proxies)
                gateway_used = "Stripe"
                
            elif gateway == 'shopify':
                if not site:
                    print(f"[Unified] Skipping Shopify - no site configured")
                    continue
                if not proxies:
                    print(f"[Unified] Skipping Shopify - no proxies configured")
                    continue
                    
                print(f"[Unified] Trying Shopify gateway...")
                result = await shopify_process(cc, mes, ano, cvv, site, proxies)
                gateway_used = "Shopify"
            
            # Parse result
            if isinstance(result, tuple):
                success = result[0]
                message = result[1] if len(result) > 1 else "Unknown"
                
                # Check if this is a definitive result
                if success:
                    # Card is live - return immediately
                    if len(result) >= 5:
                        return result[0], result[1], f"{gateway_used} ({result[2]})", result[3], result[4]
                    elif len(result) >= 3:
                        return result[0], result[1], f"{gateway_used} ({result[2]})"
                    else:
                        return success, message, gateway_used
                
                # Check for definitive decline (not a gateway error)
                definitive_declines = [
                    'card declined', 'expired card', 'lost card', 'stolen card',
                    'do not honor', 'pickup card', 'restricted card', 'invalid account',
                    'incorrect number', '3d secure', 'action required'
                ]
                
                if any(decline in message.lower() for decline in definitive_declines):
                    # Definitive decline - no need to try other gateways
                    if len(result) >= 3:
                        return result[0], result[1], f"{gateway_used} ({result[2]})"
                    else:
                        return success, message, gateway_used
                
                # Store result for potential fallback
                results.append((gateway, result))
                
                # Check for gateway errors that warrant trying another gateway
                gateway_errors = [
                    'proxy', 'timeout', 'network', 'site error', 'captcha',
                    'rate limit', 'processing error', 'failed to get'
                ]
                
                if any(err in message.lower() for err in gateway_errors):
                    print(f"[Unified] {gateway_used} had gateway error, trying next...")
                    continue
                else:
                    # Non-gateway error decline - return it
                    if len(result) >= 3:
                        return result[0], result[1], f"{gateway_used} ({result[2]})"
                    else:
                        return success, message, gateway_used
                        
        except Exception as e:
            print(f"[Unified] {gateway} error: {str(e)}")
            results.append((gateway, (False, f"Error: {str(e)[:30]}")))
            continue
    
    # If we get here, all gateways failed or returned errors
    if results:
        # Return the last result
        last_gateway, last_result = results[-1]
        if isinstance(last_result, tuple):
            if len(last_result) >= 3:
                return last_result[0], last_result[1], f"Unified ({last_result[2]})"
            else:
                return last_result[0], last_result[1], f"Unified ({last_gateway})"
    
    return False, "All gateways failed", "Unified"


async def process_card_stripe_only(cc, mes, ano, cvv, site=None, proxies=None):
    """Process card through Stripe only"""
    return await stripe_process(cc, mes, ano, cvv, site, proxies)


async def process_card_shopify_only(cc, mes, ano, cvv, site=None, proxies=None):
    """Process card through Shopify only"""
    if not site:
        return False, "No Shopify site configured", "Shopify"
    if not proxies:
        return False, "No proxies configured", "Shopify"
    return await shopify_process(cc, mes, ano, cvv, site, proxies)


async def register_unified_gateway(bot):
    """Register the unified gateway command"""
    base_command = BaseCommand(
        bot=bot,
        name="Auto",
        cmd="auto",
        handler=process_card,
        cmd_type=CommandType.MASS,
        premium=False,
        amount='Auto',
        status=True
    )
    base_command.register_command()


async def register_stripe_only_gateway(bot):
    """Register Stripe-only gateway command"""
    base_command = BaseCommand(
        bot=bot,
        name="Stripe Only",
        cmd="stripe",
        handler=process_card_stripe_only,
        cmd_type=CommandType.CHARGE,
        premium=False,
        amount=1.00,
        amountType='$',
        status=True
    )
    base_command.register_command()


async def register_shopify_only_gateway(bot):
    """Register Shopify-only gateway command"""
    base_command = BaseCommand(
        bot=bot,
        name="Shopify Only",
        cmd="shop",
        handler=process_card_shopify_only,
        cmd_type=CommandType.MASS,
        premium=False,
        amount='Custom',
        status=True
    )
    base_command.register_command()
