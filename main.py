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

# Setup logging with fallback for permission errors
handlers = [logging.StreamHandler(sys.stdout)]
try:
    # Try to create log file in current directory
    file_handler = logging.FileHandler('fixr_bot.log')
    handlers.append(file_handler)
except PermissionError:
    # If permission denied, try /tmp directory
    try:
        file_handler = logging.FileHandler('/tmp/fixr_bot.log')
        handlers.append(file_handler)
        print("Warning: Cannot write to current directory, logging to /tmp/fixr_bot.log")
    except Exception as e:
        print(f"Warning: Cannot create log file, logging to console only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

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
                page.goto("https://fixr.co/login", timeout=10000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                logger.info("Successfully connected to Fixr")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Fixr: {str(e)}")
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
                page.wait_for_selector('input[type="email"]', timeout=10000)
                page.fill('input[type="email"]', email)
                logger.debug("Email entered")

                page.click('button:has-text("Continue")')
                logger.debug("Clicked continue button")

                page.wait_for_selector('input[type="password"]', timeout=10000)
                page.fill('input[type="password"]', password)
                logger.debug("Password entered")

                page.click('button:has-text("Sign in")')
                logger.debug("Clicked sign in button")

                page.wait_for_load_state("networkidle", timeout=15000)
                logger.info("Successfully logged into Fixr")
                return True
            except Exception as e:
                logger.error(f"Login attempt failed: {str(e)}")
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
                    page.goto(f"{organiserURL}", timeout=10000)
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    
                    element = page.locator(f'a:has-text("{eventPartialID}")')
                    if element.count() > 0:
                        logger.info(f"Event found: {eventPartialID}")
                        element.click(timeout=10000)
                        page.locator('span:has-text("Tickets")').click(timeout=10000)
                        logger.info("Navigated to tickets page")
                        return True
                    else:
                        logger.debug(f"Event not found yet, will retry...")
                    
                    last_refresh = time.time()
                    
                except Exception as e:
                    logger.warning(f"Error during page refresh: {str(e)}")
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
                            page.wait_for_selector('div[data-testid^="ticket-list-item-"]', timeout=20000)
                            tickets = page.locator('div[data-testid^="ticket-list-item-"]')
                            
                            count = tickets.count()
                            logger.info(f"Found {count} ticket types on page")
                            
                            if count == 0:
                                logger.warning("No tickets found on page")
                                break

                            ticketsFound = 0
                            ticketsReleased = False
                            
                            for i in range(count):
                                try:
                                    t = tickets.nth(i)
                                    text = t.inner_text(timeout=10000).lower()
                                    
                                    if 'sold out' in text:
                                        logger.debug(f"Ticket {i+1} is sold out, skipping")
                                        continue
                                    
                                    ticketsFound += 1
                                    logger.info(f"Available ticket found: {i+1}")
                                    
                                    btn = t.locator('button:not([data-disabled="true"])').first
                                    if btn.count() > 0:
                                        btn.click(timeout=10000)
                                        ticketsReleased = True
                                        logger.info(f"Added ticket {i+1} to basket")
                                    
                                    # Handle promo code popup
                                    promo_input = page.locator('input[autocomplete="off"][spellcheck="false"]').first
                                    if promo_input.count() > 0 and promo_input.is_visible():
                                        logger.debug("Promo code required, skipping this ticket")
                                        t.locator('button:not([data-disabled="true"])').first.click(timeout=10000)
                                        
                                except Exception as e:
                                    logger.warning(f"Error processing ticket {i+1}: {str(e)}")
                                    continue

                            logger.info(f"Tickets found: {ticketsFound}, Tickets added: {ticketsReleased}")

                            if ticketsReleased:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Error during ticket selection: {str(e)}")
                            time.sleep(2)
                            continue
                    
                    # Reserve tickets
                    try:
                        logger.info("Attempting to reserve tickets...")
                        # Take screenshot before clicking reserve
                        page.screenshot(path="before_reserve.png")
                        logger.info("Screenshot saved: before_reserve.png")
                        
                        page.locator('button:has-text("Reserve")').click(timeout=15000)
                        page.wait_for_load_state("networkidle", timeout=25000)
                        logger.info("Tickets successfully reserved!")
                        
                        # Take screenshot after reservation
                        page.screenshot(path="after_reserve.png")
                        logger.info("Screenshot saved: after_reserve.png")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to reserve tickets: {str(e)}")
                        page.screenshot(path="reserve_error.png")
                        logger.info("Error screenshot saved: reserve_error.png")
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
                
                # Disable ticket protection
                logger.debug("Disabling ticket protection")
                page.locator('input[name="ticket-protection"][value="no"]').check(timeout=15000)
        
                # Uncheck all additional options
                radios = page.locator('input[type="radio"][id$="-radio-no"]')
                radio_count = radios.count()
                logger.debug(f"Found {radio_count} additional options to disable")
                for i in range(radio_count):
                    radios.nth(i).check(timeout=10000)

                logger.debug("Clicking continue to payment")
                page.locator('button:has-text("Continue")').click(timeout=15000)
                
                # Wait for Stripe iframe
                logger.info("Waiting for Stripe payment form...")
                stripe_iframe_element = page.wait_for_selector(
                    "iframe[src*='stripe']",
                    timeout=25000
                )

                stripe_frame = stripe_iframe_element.content_frame()
                if stripe_frame is None:
                    raise Exception("Stripe iframe not resolved")
                
                logger.debug("Stripe iframe loaded successfully")

                # Wait for all payment fields
                logger.debug("Waiting for payment fields...")
                stripe_frame.wait_for_selector("#Field-numberInput", timeout=20000)
                stripe_frame.wait_for_selector("#Field-expiryInput", timeout=20000)
                stripe_frame.wait_for_selector("#Field-cvcInput", timeout=20000)
                stripe_frame.wait_for_selector("#Field-postalCodeInput", timeout=20000)

                # Fill payment details
                logger.info("Filling payment details...")
                stripe_frame.fill("#Field-numberInput", CARDNO, timeout=15000)
                stripe_frame.fill("#Field-expiryInput", EXPIRY, timeout=15000)
                stripe_frame.fill("#Field-cvcInput", CVC, timeout=15000)
                stripe_frame.fill("#Field-postalCodeInput", POSTCODE, timeout=15000)
                logger.debug("Payment details filled")
                
                # Submit payment
                logger.info("Submitting payment...")
                pay_button = page.locator('button:has-text("Pay now")')
                pay_button.click(timeout=15000)

                # Wait for payment processing
                logger.info("Waiting for payment to process...")
                time.sleep(10)

                # Take screenshot for confirmation
                page.screenshot(path="page.png")
                logger.info("Payment submitted! Screenshot saved as page.png")
                return True
                
            except Exception as e:
                logger.error(f"Checkout failed: {str(e)}")
                page.screenshot(path="error.png")
                logger.info("Error screenshot saved as error.png")
                raise
        
        try:
            retry_with_timeout(max_retries=3, timeout=10)(complete_checkout)()
            logger.info("✓ Checkout completed successfully!")
        except Exception as e:
            logger.critical(f"Checkout failed after retries: {str(e)}")
            raise