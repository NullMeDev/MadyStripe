from telebot.async_telebot import AsyncTeleBot
from database import (
    add_shopify_site, remove_shopify_site, get_user_shopify_sites,
    add_proxy, remove_proxy, get_user_proxies, get_user, add_user
)

import aiohttp
import random
import asyncio
from collections import defaultdict
from cachetools import TTLCache
from utils import Utils, extract_between
from commands.base_command import BaseCommand, CommandType
from urllib.parse import urlparse
import re
import time

# Enhanced error handling and caching
product_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute cache
rate_limits = defaultdict(lambda: {'count': 0, 'reset_time': 0})

def extract_domain_name(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname.replace('www.', '')

async def check_rate_limit(domain):
    """Rate limiting to prevent API bans"""
    now = asyncio.get_event_loop().time()
    if now > rate_limits[domain]['reset_time']:
        rate_limits[domain] = {'count': 0, 'reset_time': now + 60}

    if rate_limits[domain]['count'] >= 30:  # 30 requests per minute
        return False

    rate_limits[domain]['count'] += 1
    return True

async def get_working_proxy():
    """Enhanced proxy rotation with fallback"""
    proxies = Utils.get_all_proxies()
    for proxy in proxies:
        try:
            # Test proxy before using
            async with aiohttp.ClientSession() as session:
                test_url = "http://httpbin.org/ip"
                async with session.get(test_url, proxy=proxy, timeout=5) as resp:
                    if resp.status == 200:
                        return proxy
        except:
            continue
    return None

async def fetchProducts_enhanced(domain, startPrice=0):
    """Enhanced fetchProducts with better error handling and caching"""
    if not domain:
        return False, "invalid_domain"

    # Check rate limit
    if not await check_rate_limit(domain):
        return False, "rate_limit_exceeded"

    # Check cache first
    cache_key = f"{domain}:{startPrice}"
    if cache_key in product_cache:
        return product_cache[cache_key]

    try:
        domain = "https://" + extract_domain_name(domain)
        if not domain or len(domain) < 8:
            return False, "invalid_domain"

        # Enhanced proxy handling
        proxy = await get_working_proxy()
        if not proxy:
            return False, "no_proxy"

        proxy_str = Utils.format_proxy(proxy)

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            connector=aiohttp.TCPConnector(limit=10)
        ) as session:
            try:
                async with session.get(
                    f"{domain}/products.json",
                    proxy=proxy_str,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as resp:
                    if resp.status != 200:
                        return False, f"http_error_{resp.status}"

                    text = await resp.text()
                    if "shopify" not in text.lower():
                        return False, "not_shopify"

                    result = (await resp.json())['products']
                    if not result:
                        return False, "no_products"

            except aiohttp.ClientError as e:
                return False, f"network_error: {str(e)}"
            except Exception as e:
                return False, f"json_error: {str(e)}"

        min_price = float('inf')
        min_product = None

        for product in result:
            if not product.get('variants'):
                continue

            for variant in product['variants']:
                if not variant.get('available', True):
                    continue

                try:
                    price = variant.get('price', '0')
                    if isinstance(price, str):
                        price = float(price.replace(',', ''))
                    else:
                        price = float(price)

                    if price < min_price and price >= startPrice:
                        min_price = price
                        min_product = {
                            'site': domain,
                            'price': f"{price:.2f}",
                            'variant_id': str(variant['id']),
                            'link': f"{domain}/products/{product['handle']}"
                        }

                except (ValueError, TypeError, AttributeError):
                    continue

        if min_product:
            # Cache successful result
            product_cache[cache_key] = min_product
            return min_product
        else:
            return False, "no_valid_products"

    except Exception as e:
        return False, f"unexpected_error: {str(e)}"

async def verify_shopify_url_enhanced(url, startPrice=0):
    """Enhanced URL verification with better error handling"""
    if not url:
        return False, "❌ Invalid URL"

    result = await fetchProducts_enhanced(url, startPrice)
    if isinstance(result, tuple):
        error_map = {
            "invalid_domain": "❌ Invalid domain",
            "no_proxy": "❌ No proxy available",
            "invalid_proxy_format": "❌ Invalid proxy format",
            "http_error_404": "❌ Site not found",
            "http_error_403": "❌ Access forbidden",
            "http_error_500": "❌ Server error",
            "not_shopify": "❌ Not a Shopify site",
            "no_products": "❌ No products found",
            "no_valid_products": "❌ No valid products found",
            "network_error": "❌ Network error",
            "json_error": "❌ Data parsing error",
            "rate_limit_exceeded": "❌ Rate limit exceeded",
        }
        return False, error_map.get(result[1], f"❌ Unknown error: {result[1]}")

    info = result
    if not info:
        return False, "❌ Invalid Shopify Site!"

    try:
        proxy = await get_working_proxy()
        if not proxy:
            return False, "❌ No proxy available"

        proxy_str = Utils.format_proxy(proxy)

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20),
            connector=aiohttp.TCPConnector(limit=5)
        ) as session:
            # Add to cart
            cart_response = await session.post(
                f"{info['site']}/cart/add.js",
                data={'id': info['variant_id']},
                proxy=proxy_str,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            if cart_response.status != 200:
                return False, "❌ Failed to add to cart"

            # Start checkout
            checkout_response = await session.post(
                f"{info['site']}/checkout/",
                proxy=proxy_str
            )
            checkout_url = str(checkout_response.url)

            if 'login' in checkout_url.lower():
                return False, "❌ Site requires login"

            # Get payment gateway info
            page_response = await session.get(
                checkout_url,
                proxy=proxy_str
            )
            text = await page_response.text()
            displayName = extract_between(text, 'extensibilityDisplayName":"', '&q')

            return True, {
                'url': info['site'],
                'variant_id': info['variant_id'],
                'price': info['price'],
                'checkout_url': checkout_url,
                'gateway': displayName or "Unknown"
            }

    except aiohttp.ClientError:
        return False, "❌ Connection error"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Keep original functions for backward compatibility
async def fetchProducts(domain, startPrice=0):
    return await fetchProducts_enhanced(domain, startPrice)

async def verify_shopify_url(url, startPrice=0):
    return await verify_shopify_url_enhanced(url, startPrice)

# Enhanced command registration with better error handling
async def register_resource_commands(bot: AsyncTeleBot):
    """Enhanced command registration with error handling"""

    @bot.message_handler(commands=['addsh'])
    async def add_shopify_command(message):
        try:
            user_id = message.from_user.id
            text = message.text.strip()

            if len(text.split()) < 2:
                await bot.reply_to(message, "❌ Usage: /addsh <shopify_url>")
                return

            url = text.split()[1]

            # Enhanced URL validation
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Verify URL before adding
            success, result = await verify_shopify_url_enhanced(url)

            if not success:
                await bot.reply_to(message, f"❌ Invalid Shopify store: {result}")
                return

            # Add to database
            if add_shopify_site(user_id, result['url']):
                response = (
                    f"✅ <b>Shopify Store Added!</b>\n\n"
                    f"🏪 Store: {result['url']}\n"
                    f"💰 Sample Price: ${result['price']}\n"
                    f"🔐 Gateway: {result['gateway']}\n\n"
                    f"Use /shopify to check cards on this store!"
                )
                await bot.reply_to(message, response, parse_mode='HTML')
            else:
                await bot.reply_to(message, "❌ Failed to add store (might already exist)")

        except Exception as e:
            await bot.reply_to(message, f"❌ Error adding store: {str(e)}")

    @bot.message_handler(commands=['shopify'])
    async def shopify_command(message):
        try:
            user_id = message.from_user.id
            sites = get_user_shopify_sites(user_id)

            if not sites:
                await bot.reply_to(message, "❌ No Shopify stores added. Use /addsh <url> to add one!")
                return

            response = "🏪 <b>Your Shopify Stores:</b>\n\n"
            for i, site in enumerate(sites, 1):
                response += f"{i}. {site}\n"

            response += "\n💳 Send a card to check on these stores!"
            await bot.reply_to(message, response, parse_mode='HTML')

        except Exception as e:
            await bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.message_handler(commands=['rmsh'])
    async def remove_shopify_command(message):
        try:
            user_id = message.from_user.id
            text = message.text.strip()

            if len(text.split()) < 2:
                await bot.reply_to(message, "❌ Usage: /rmsh <store_url>")
                return

            url = text.split()[1]
            if remove_shopify_site(user_id, url):
                await bot.reply_to(message, f"✅ Removed: {url}")
            else:
                await bot.reply_to(message, "❌ Store not found")

        except Exception as e:
            await bot.reply_to(message, f"❌ Error: {str(e)}")

    print("✅ Enhanced Shopify commands registered successfully")
