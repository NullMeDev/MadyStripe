"""
Debug Shopify Payment Form Structure
Inspects actual payment forms to find correct selectors
"""

import sys
sys.path.insert(0, '.')

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

def inspect_payment_form(store_url, variant_id):
    """Inspect payment form structure"""
    
    print(f"\n{'='*70}")
    print(f"INSPECTING: {store_url}")
    print(f"{'='*70}\n")
    
    # Initialize browser
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Navigate to checkout
        checkout_url = f"https://{store_url}/cart/{variant_id}:1"
        print(f"1. Navigating to: {checkout_url}")
        driver.get(checkout_url)
        time.sleep(3)
        
        # Click checkout if needed
        try:
            checkout_btn = driver.find_element(By.NAME, 'checkout')
            checkout_btn.click()
            print(f"2. Clicked checkout button")
            time.sleep(3)
        except:
            print(f"2. Already on checkout or no button needed")
        
        # Fill email
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
            email_field.send_keys('test@example.com')
            print(f"3. Filled email")
            time.sleep(1)
        except:
            print(f"3. Could not fill email")
        
        # Fill shipping
        try:
            first_name = driver.find_element(By.NAME, 'firstName')
            first_name.send_keys('John')
            
            last_name = driver.find_element(By.NAME, 'lastName')
            last_name.send_keys('Doe')
            
            address = driver.find_element(By.NAME, 'address1')
            address.send_keys('123 Main St')
            
            city = driver.find_element(By.NAME, 'city')
            city.send_keys('New York')
            
            zip_code = driver.find_element(By.NAME, 'postalCode')
            zip_code.send_keys('10001')
            
            print(f"4. Filled shipping address")
            time.sleep(1)
        except:
            print(f"4. Could not fill shipping")
        
        # Continue to payment
        try:
            continue_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            continue_btn.click()
            print(f"5. Clicked continue to payment")
            time.sleep(5)  # Wait for payment form to load
        except:
            print(f"5. Could not click continue")
        
        # Now inspect the page
        print(f"\n{'='*70}")
        print(f"PAGE INSPECTION")
        print(f"{'='*70}\n")
        
        # Get current URL
        print(f"Current URL: {driver.current_url}\n")
        
        # Find all iframes
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"Found {len(iframes)} iframes")
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src')
                name = iframe.get_attribute('name')
                id_attr = iframe.get_attribute('id')
                print(f"  Iframe {i+1}:")
                print(f"    src: {src}")
                print(f"    name: {name}")
                print(f"    id: {id_attr}")
            except:
                pass
        print()
        
        # Find all input fields
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"Found {len(inputs)} input fields in main page:")
        for i, inp in enumerate(inputs[:20]):  # Limit to first 20
            try:
                name = inp.get_attribute('name')
                id_attr = inp.get_attribute('id')
                placeholder = inp.get_attribute('placeholder')
                input_type = inp.get_attribute('type')
                autocomplete = inp.get_attribute('autocomplete')
                
                if any([name, id_attr, placeholder, autocomplete]):
                    print(f"  Input {i+1}:")
                    if name: print(f"    name: {name}")
                    if id_attr: print(f"    id: {id_attr}")
                    if placeholder: print(f"    placeholder: {placeholder}")
                    if input_type: print(f"    type: {input_type}")
                    if autocomplete: print(f"    autocomplete: {autocomplete}")
            except:
                pass
        print()
        
        # Check each iframe
        for i, iframe in enumerate(iframes):
            try:
                print(f"Checking iframe {i+1}...")
                driver.switch_to.frame(iframe)
                
                iframe_inputs = driver.find_elements(By.TAG_NAME, 'input')
                print(f"  Found {len(iframe_inputs)} inputs in iframe {i+1}:")
                
                for j, inp in enumerate(iframe_inputs[:10]):
                    try:
                        name = inp.get_attribute('name')
                        id_attr = inp.get_attribute('id')
                        placeholder = inp.get_attribute('placeholder')
                        input_type = inp.get_attribute('type')
                        
                        if any([name, id_attr, placeholder]):
                            print(f"    Input {j+1}:")
                            if name: print(f"      name: {name}")
                            if id_attr: print(f"      id: {id_attr}")
                            if placeholder: print(f"      placeholder: {placeholder}")
                            if input_type: print(f"      type: {input_type}")
                    except:
                        pass
                
                driver.switch_to.default_content()
                print()
            except:
                driver.switch_to.default_content()
        
        # Save page source for analysis
        with open(f'/tmp/shopify_checkout_{store_url.replace(".", "_")}.html', 'w') as f:
            f.write(driver.page_source)
        print(f"Page source saved to /tmp/shopify_checkout_{store_url.replace('.', '_')}.html")
        
        # Keep browser open for manual inspection
        print(f"\n{'='*70}")
        print(f"Browser will stay open for 30 seconds for manual inspection...")
        print(f"{'='*70}\n")
        time.sleep(30)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    # Test stores from our database
    test_stores = [
        ('sifrinerias.myshopify.com', 31135),
        ('khosto.myshopify.com', 37358),
    ]
    
    for store_url, variant_id in test_stores:
        try:
            inspect_payment_form(store_url, variant_id)
        except Exception as e:
            print(f"Error inspecting {store_url}: {e}")
        
        print(f"\n{'='*70}\n")
