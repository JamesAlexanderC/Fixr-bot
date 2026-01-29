# This is a relatively simple fixr flow for logging in, reserving and buying a defined selection of tickets - takes the following arguments:
# email, password, eventPartialID, (optional) proxy (in form "IP:username:password") 
# With these values specified correctly this script will work fully locally to buy all tickets from the specified event that don't require promo codes
# for ease this scrip is hardcoded for timepiece events, but this can be changed
# future development will see the use of an external API I am developing to allow for the proper fetching of known promo codes, and fine grain remote control at runtime



# for use with a custom card, a companion file of the following structure should be created in the same directory with the name 'cardDetails.py'
"""
CARDNO = "0000 0000 0000 0000"
EXPIRY = "00/00"
CVC = "000"                                    
POSTCODE = "AA00 0AA" 
"""

# Defining card details from companion file
try:
    # import cardDetails
    CARDNO = "4165 4903 7432 6789"
    EXPIRY = "06/30"
    CVC = "322"                                    
    POSTCODE = "YO23 3UR"
except:
    raise Exception(
        "Card details not defined properly, please specify them as instructed"
    )

# precursary requirements defined in requirements.txt
import sys
import time
from camoufox.sync_api import Camoufox
import argparse
import logging
from datetime import datetime
from functools import wraps
import os

# Create log directory for screenshots and logs
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging with fallback for permission errors
handlers = [logging.StreamHandler(sys.stdout)]
try:
    # Try to create log file in log directory
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'fixr_bot.log'))
    handlers.append(file_handler)
except PermissionError:
    # If permission denied, try /tmp directory
    try:
        file_handler = logging.FileHandler('/tmp/fixr_bot.log')
        handlers.append(file_handler)
        print("Warning: Cannot write to log directory, logging to /tmp/fixr_bot.log")
    except Exception as e:
        print(f"Warning: Cannot create log file, logging to console only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Helper function for timestamped screenshots
def save_screenshot(page, name, description=""):
    """Save a screenshot with timestamp in the log directory"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(LOG_DIR, f"{timestamp}_{name}.png")
    try:
        page.screenshot(path=filename)
        logger.info(f"Screenshot saved: {filename} {description}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save screenshot {filename}: {str(e)}")
        return None

# Retry decorator with exponential backoff
def retry_with_timeout(max_retries=3, timeout=10, backoff_factor=2):
    """
    Decorator to retry operations with timeout and exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = kwargs.get('operation_name', func.__name__)
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting {operation_name} (attempt {attempt + 1}/{max_retries})")
                    result = func(*args, **kwargs)
                    logger.info(f"{operation_name} completed successfully")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    
                    if attempt < max_retries - 1:
                        sleep_time = backoff_factor ** attempt
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"{operation_name} failed after {max_retries} attempts")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

# Getting arguments - validity checking
parser = argparse.ArgumentParser(description="Fixr ticket buying script")
parser.add_argument('--email', required=True, help='Email for login')
parser.add_argument('--password', required=True, help='Password for login')
parser.add_argument('--eventPartialID', required=True, help='Event partial identifier')
parser.add_argument('--proxy', help='Proxy in format IP:port:username:password')
parser.add_argument('--organiserURL', help='URL of the organiser')
parser.add_argument('--test', action='store_true', help='Test mode flag')

args = parser.parse_args()

email = args.email
password = args.password
eventPartialID = args.eventPartialID
proxy = args.proxy if args.proxy else None
organiserURL = args.organiserURL
test = args.test

if test:
    CARDNO = "0000 0000 0000 0000"
    EXPIRY = "00/00"
    CVC = "000"                                    
    POSTCODE = "AA00 0AA"

# Parsing proxy for correct Camoufox format (Assumes a specific proxy format)
if proxy is not None:
    try:
        split_proxy = proxy.split(":")

        proxy = {
            "server": f"{split_proxy[0]}:{split_proxy[1]}",
            "username": split_proxy[2],
            "password": split_proxy[3]
            }
    except:
        raise Exception(
            "Proxy is not in expected format of 'IP:Username:Password'"
        )

# Start of main loop outside of browser instance to allow reconnection and restart in case of initial failure
while True:
    
    # opens Camoufox browser instance with specific set of variables for use case including previously specified proxy
    camoufox_kwargs = {"disable_coop": True, "window": (1280, 720), "i_know_what_im_doing": True, "geoip": True, "headless": False}
    if proxy is not None:
        camoufox_kwargs["proxy"] = proxy
    
    with Camoufox(**camoufox_kwargs) as browser:
        page = browser.new_page()
        
        # Try connect to fixr with retry logic
        def connect_to_fixr():
            try:
                logger.info("Attempting to connect to Fixr login page...")
                page.goto("https://fixr.co/login", timeout=20000)
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                save_screenshot(page, "01_connected_to_fixr", "- Successfully loaded Fixr login page")
                logger.info("Successfully connected to Fixr")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Fixr: {str(e)}")
                save_screenshot(page, "error_connection_failed", f"- Connection error: {str(e)}")
                raise Exception(f"Could not connect to Fixr - {str(e)}")
        
        try:
            retry_with_timeout(max_retries=5, timeout=10)(connect_to_fixr)()
        except Exception as e:
            logger.critical(f"Failed to establish initial connection after multiple retries: {str(e)}")
            raise Exception("ERROR: Could not connect to internet / this script may be deprecated")

        # Login with improved error handling
        def perform_login():
            try:
                logger.info("Starting login process...")
                page.wait_for_selector('input[type="email"]', timeout=20000)
                page.fill('input[type="email"]', email)
                logger.debug("Email entered")

                page.click('button:has-text("Continue")')
                page.wait_for_load_state("networkidle", timeout=30000)
                logger.debug("Clicked continue button")

                page.wait_for_selector('input[type="password"]', timeout=20000)
                page.fill('input[type="password"]', password)
                logger.debug("Password entered")

                page.click('button:has-text("Sign in")')
                page.wait_for_load_state("networkidle", timeout=35000)
                logger.debug("Clicked sign in button")

                save_screenshot(page, "04_logged_in", "- Successfully logged in")
                logger.info("Successfully logged into Fixr")
                return True
            except Exception as e:
                logger.error(f"Login attempt failed: {str(e)}")
                save_screenshot(page, "error_login_failed", f"- Login error: {str(e)}")
                raise
        
        try:
            retry_with_timeout(max_retries=5, timeout=10)(perform_login)()
        except Exception as e:
            logger.critical(f"Login failed after multiple attempts with email: {email}")
            raise Exception(f"ERROR: Could not login with provided credentials - {str(e)}")
        
        # Event finding and reservation with improved error handling
        def find_and_navigate_to_event():
            """Find the event with timeout protection - allows longer waits for ticket drops"""
            start_time = time.time()
            last_refresh = 0
            max_wait_before_reconnect = 30  # 5 minutes without finding event triggers reconnect
            
            while True:
                current_time = time.time()
                
                # Check if we've been searching too long without success
                if current_time - start_time > max_wait_before_reconnect:
                    logger.warning(f"No event found after {max_wait_before_reconnect}s, may need to reconnect")
                    raise Exception("Event search timeout - consider reconnecting")
                
                # Rate limit refreshes
                if current_time - last_refresh < 2.5:
                    time.sleep(2.5 - (current_time - last_refresh))
                
                try:
                    CT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"Refreshing organiser page at {CT}")
                    page.goto(f"{organiserURL}", timeout=20000)
                    page.wait_for_load_state("domcontentloaded", timeout=20000)
                    
                    element = page.locator(f'a:has-text("{eventPartialID}")')
                    if element.count() > 0:
                        logger.info(f"Event found: {eventPartialID}")
                        save_screenshot(page, "05_event_found", f"- Event '{eventPartialID}' located")
                        element.click(timeout=20000)
                        page.wait_for_load_state("networkidle", timeout=30000)
                        logger.debug("Event page loaded")
                        
                        page.locator('span:has-text("Tickets")').click(timeout=20000)
                        page.wait_for_load_state("networkidle", timeout=30000)
                        save_screenshot(page, "06_tickets_page", "- Navigated to tickets page")
                        logger.info("Navigated to tickets page")
                        return True
                    else:
                        logger.debug(f"Event not found yet, will retry...")
                    
                    last_refresh = time.time()
                    
                except Exception as e:
                    logger.warning(f"Error during page refresh: {str(e)}")
                    save_screenshot(page, "error_page_refresh", f"- Refresh error: {str(e)}")
                    # Don't raise here, just continue the loop
                    time.sleep(2)
                    last_refresh = time.time()
        
        reservation_attempts = 0
        max_reservation_attempts = 10
        
        while reservation_attempts <= max_reservation_attempts:
            try:
                find_and_navigate_to_event()
                
                # Loop to get tickets with timeout protection
                def select_and_reserve_tickets():
                    start_time = time.time()
                    max_ticket_wait = 60  # Wait up to 60 seconds for tickets to appear/become available
                    
                    while True:
                        if time.time() - start_time > max_ticket_wait:
                            logger.warning("Ticket selection taking too long, may need to refresh")
                            raise Exception("Ticket selection timeout")
                        
                        try:
                            # find ticket elements with timeout
                            page.wait_for_selector('div[data-testid^="ticket-list-item-"]', timeout=30000)
                            tickets = page.locator('div[data-testid^="ticket-list-item-"]')
                            
                            count = tickets.count()
                            logger.info(f"Found {count} ticket types on page")
                            save_screenshot(page, "07_ticket_list", f"- Found {count} ticket types")
                            
                            if count == 0:
                                logger.warning("No tickets found on page")
                                save_screenshot(page, "error_no_tickets", "- No tickets available")
                                break

                            ticketsFound = 0
                            ticketsReleased = False
                            
                            for i in range(count):
                                try:
                                    t = tickets.nth(i)
                                    text = t.inner_text(timeout=15000).lower()
                                    
                                    if 'sold out' in text:
                                        logger.debug(f"Ticket {i+1} is sold out, skipping")
                                        continue
                                    
                                    ticketsFound += 1
                                    logger.info(f"Available ticket found: {i+1}")
                                    
                                    btn = t.locator('button:not([data-disabled="true"])').first
                                    if btn.count() > 0:
                                        btn.click(timeout=20000)
                                        page.wait_for_load_state("networkidle", timeout=25000)
                                        ticketsReleased = True
                                        save_screenshot(page, f"08_ticket_{i+1}_added", f"- Added ticket {i+1} to basket")
                                        logger.info(f"Added ticket {i+1} to basket")
                                    
                                    # Handle promo code popup
                                    promo_input = page.locator('input[autocomplete="off"][spellcheck="false"]').first
                                    if promo_input.count() > 0 and promo_input.is_visible():
                                        logger.debug("Promo code required, skipping this ticket")
                                        save_screenshot(page, f"info_promo_required_{i+1}", "- Promo code required")
                                        t.locator('button:not([data-disabled="true"])').first.click(timeout=20000)
                                        page.wait_for_load_state("networkidle", timeout=25000)
                                        
                                except Exception as e:
                                    logger.warning(f"Error processing ticket {i+1}: {str(e)}")
                                    save_screenshot(page, f"error_ticket_{i+1}_processing", f"- Error with ticket {i+1}: {str(e)}")
                                    continue

                            logger.info(f"Tickets found: {ticketsFound}, Tickets added: {ticketsReleased}")

                            if ticketsReleased:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Error during ticket selection: {str(e)}")
                            save_screenshot(page, "error_ticket_selection", f"- Ticket selection error: {str(e)}")
                            time.sleep(2)
                            continue
                    
                    # Reserve tickets
                    try:
                        logger.info("Attempting to reserve tickets...")
                        # Take screenshot before clicking reserve
                        save_screenshot(page, "09_before_reserve", "- Before clicking Reserve button")
                        
                        page.locator('button:has-text("Reserve")').click(timeout=25000)
                        page.wait_for_load_state("networkidle", timeout=35000)
                        logger.info("Tickets successfully reserved!")
                        
                        # Take screenshot after reservation
                        save_screenshot(page, "10_after_reserve", "- Tickets reserved successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to reserve tickets: {str(e)}")
                        save_screenshot(page, "error_reserve_failed", f"- Reserve error: {str(e)}")
                        raise
                
                select_and_reserve_tickets()
                break
            
            except Exception as e:
                reservation_attempts += 1
                logger.error(f"Reservation attempt {reservation_attempts} failed: {str(e)}")
                
                if reservation_attempts > max_reservation_attempts:
                    logger.critical("Max reservation attempts reached, restarting browser")
                    break
                
                time.sleep(2)
        
        # Checkout process with improved error handling
        def complete_checkout():
            try:
                logger.info("Starting checkout process...")
                save_screenshot(page, "11_checkout_start", "- Starting checkout")
                
                # Scroll to top to ensure all elements are visible
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                # Disable ticket protection with retry
                logger.debug("Disabling ticket protection")
                try:
                    protection_input = page.locator('input[name="ticket-protection"][value="no"]')
                    protection_input.scroll_into_view_if_needed(timeout=15000)
                    protection_input.check(timeout=30000)
                except Exception as e:
                    logger.warning(f"Could not find ticket protection option: {str(e)}")
                    save_screenshot(page, "info_no_protection_option", "- No ticket protection option found")
        
                # Scroll down to find radio buttons
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
                
                # Uncheck all additional options with better error handling
                radios = page.locator('input[type="radio"][id$="-radio-no"]')
                radio_count = radios.count()
                logger.debug(f"Found {radio_count} additional options to disable")
                for i in range(radio_count):
                    try:
                        radio = radios.nth(i)
                        radio.scroll_into_view_if_needed(timeout=15000)
                        radio.check(timeout=25000)
                        time.sleep(0.3)  # Small delay between radio selections
                    except Exception as e:
                        logger.warning(f"Could not check radio {i+1}: {str(e)}")

                save_screenshot(page, "12_options_disabled", "- Options configured")
                
                # Scroll to continue button
                continue_btn = page.locator('button:has-text("Continue")')
                continue_btn.scroll_into_view_if_needed(timeout=15000)
                save_screenshot(page, "12b_before_continue", "- Before clicking continue")
                
                logger.debug("Clicking continue to payment")
                continue_btn.click(timeout=30000)
                
                # Wait for page to load
                page.wait_for_load_state("networkidle", timeout=40000)
                time.sleep(2)
                save_screenshot(page, "12c_after_continue", "- After clicking continue")
                
                # Wait for Stripe iframe with scrolling
                logger.info("Waiting for Stripe payment form...")
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(2)
                
                # Wait for iframe to appear
                stripe_iframe_element = page.wait_for_selector(
                    "iframe[src*='stripe']",
                    timeout=40000
                )
                logger.debug("Stripe iframe element found")
                time.sleep(2)  # Give iframe time to initialize

                stripe_frame = stripe_iframe_element.content_frame()
                if stripe_frame is None:
                    save_screenshot(page, "error_stripe_iframe_missing", "- Stripe iframe not found")
                    raise Exception("Stripe iframe not resolved")
                
                # Wait for the iframe to fully load its content
                logger.debug("Waiting for iframe content to load...")
                try:
                    # Try to wait for any element to appear in the iframe as a sign it's loaded
                    stripe_frame.wait_for_selector("body", timeout=10000)
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Could not confirm iframe body loaded: {str(e)}")
                
                save_screenshot(page, "13_stripe_loaded", "- Stripe payment form loaded")
                logger.debug("Stripe iframe loaded successfully")

                # Wait for all payment fields with increased timeouts and better error handling
                logger.debug("Waiting for payment fields...")
                
                # Try to find the fields with more specific waiting
                try:
                    logger.debug("Looking for card number input...")
                    stripe_frame.wait_for_selector("#Field-numberInput", timeout=40000, state="visible")
                    logger.debug("Card number input found")
                    
                    logger.debug("Looking for expiry input...")
                    stripe_frame.wait_for_selector("#Field-expiryInput", timeout=40000, state="visible")
                    logger.debug("Expiry input found")
                    
                    logger.debug("Looking for CVC input...")
                    stripe_frame.wait_for_selector("#Field-cvcInput", timeout=40000, state="visible")
                    logger.debug("CVC input found")
                    
                    logger.debug("Looking for postcode input...")
                    stripe_frame.wait_for_selector("#Field-postalCodeInput", timeout=40000, state="visible")
                    logger.debug("Postcode input found")
                except Exception as e:
                    logger.error(f"Failed to find payment fields: {str(e)}")
                    # Get iframe HTML for debugging
                    try:
                        iframe_html = stripe_frame.content()
                        logger.debug(f"Iframe HTML length: {len(iframe_html)} characters")
                        # Save iframe source for debugging
                        with open("log/stripe_iframe_debug.html", "w") as f:
                            f.write(iframe_html)
                        logger.info("Saved iframe HTML to log/stripe_iframe_debug.html")
                    except Exception as debug_e:
                        logger.error(f"Could not get iframe HTML: {str(debug_e)}")
                    raise
                
                logger.info("All payment fields found")
                time.sleep(1)

                # Fill payment details with increased timeouts
                logger.info("Filling payment details...")
                stripe_frame.fill("#Field-numberInput", CARDNO, timeout=30000)
                logger.debug("Card number filled")
                time.sleep(0.5)
                
                stripe_frame.fill("#Field-expiryInput", EXPIRY, timeout=30000)
                logger.debug("Expiry filled")
                time.sleep(0.5)
                
                stripe_frame.fill("#Field-cvcInput", CVC, timeout=30000)
                logger.debug("CVC filled")
                time.sleep(0.5)
                
                stripe_frame.fill("#Field-postalCodeInput", POSTCODE, timeout=30000)
                logger.debug("Postcode filled")
                time.sleep(1)
                
                save_screenshot(page, "14_payment_filled", "- Payment details entered")
                logger.debug("Payment details filled")
                
                # Scroll to pay button
                pay_button = page.locator('button:has-text("Pay now")')
                pay_button.scroll_into_view_if_needed(timeout=15000)
                save_screenshot(page, "14b_before_pay", "- Before clicking Pay now")
                
                # Submit payment
                logger.info("Submitting payment...")
                pay_button.click(timeout=30000)
                
                # Wait for payment processing
                logger.info("Waiting for payment to process...")
                page.wait_for_load_state("networkidle", timeout=40000)
                time.sleep(10)

                # Take screenshot for confirmation
                save_screenshot(page, "15_payment_submitted", "- Payment submitted")
                logger.info("Payment submitted!")
                return True
                
            except Exception as e:
                logger.error(f"Checkout failed: {str(e)}")
                save_screenshot(page, "error_checkout_failed", f"- Checkout error: {str(e)}")
                raise
        
        try:
            retry_with_timeout(max_retries=3, timeout=10)(complete_checkout)()
            logger.info("✓ Checkout completed successfully!")
        except Exception as e:
            logger.critical(f"Checkout failed after retries: {str(e)}")
            raise