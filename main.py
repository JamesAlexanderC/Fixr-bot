# This is a hardened version of the fixr ticket buying script.
# It never quits due to timeouts or errors; instead, it logs issues and restarts the browser/reconnects indefinitely.
# Takes the following arguments: email, password, eventPartialID, (optional) proxy (in form "IP:username:password")
# With these values specified correctly this script will work fully locally to buy all tickets from the specified event that don't require promo codes
# Hardened for reliability - runs forever until success or manual stop.

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
import logging
from camoufox.sync_api import Camoufox
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Getting arguments - validity checking
parser = argparse.ArgumentParser(description="Hardened Fixr ticket buying script")
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
proxy = args.proxy if args.proxy else False
organiserURL = args.organiserURL
test = args.test

if test:
    CARDNO = "0000 0000 0000 0000"
    EXPIRY = "00/00"
    CVC = "000"
    POSTCODE = "AA00 0AA"

# Parsing proxy for correct Camoufox format (Assumes a specific proxy format)
if proxy != False:
    try:
        split_proxy = proxy.split(":")

        proxy = {
            "server": f"{split_proxy[0]}:{split_proxy[1]}",
            "username": split_proxy[2],
            "password": split_proxy[3]
            }
    except Exception as e:
        logging.error(f"Proxy parsing failed: {e}")
        sys.exit(1)

# Increased timeouts for reliability
PAGE_LOAD_TIMEOUT = 300000  # 5 minutes
SELECTOR_TIMEOUT = 60000    # 1 minute
STRIPE_TIMEOUT = 300000     # 5 minutes

# Start of main loop - runs forever, restarting on any error
attempt = 0
while True:
    attempt += 1
    logging.info(f"Starting attempt {attempt}")

    try:
        # opens Camoufox browser instance with specific set of variables for use case including previously specified proxy
        with Camoufox(disable_coop=True, window=(1280, 720), i_know_what_im_doing=True, geoip=True) as browser:
            page = browser.new_page()

            # Try connect to fixr
            try:
                page.goto("https://fixr.co/login")
                page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT)
                logging.info("Connected to fixr")
            except Exception as e:
                logging.error(f"Failed to connect to fixr: {e} - restarting")
                time.sleep(10)
                continue

            # login loop - infinite retries
            while True:
                try:
                    page.wait_for_selector('input[type="email"]', timeout=SELECTOR_TIMEOUT)
                    page.fill('input[type="email"]', email)

                    page.click('button:has-text("Continue")')

                    page.wait_for_selector('input[type="password"]', timeout=SELECTOR_TIMEOUT)
                    page.fill('input[type="password"]', password)

                    page.click('button:has-text("Sign in")')

                    page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT)

                    logging.info("Successfully logged into fixr")
                    break
                except Exception as e:
                    logging.warning(f"Login failed: {e} - retrying in 5s")
                    time.sleep(5)

            # reserve loop - infinite retries
            while True:
                try:
                    # This loop handles expected refreshing of fixr events page to try find match for event identifier
                    refresh_count = 0
                    while True:
                        refresh_count += 1
                        # slight delay between connection requests to improve durability and prevent detection from fixr
                        time.sleep(2.5)

                        # this flow finds the specified event on the timepiece page
                        logging.info(f"Page refresh attempt {refresh_count}")
                        page.goto(f"{organiserURL}")
                        page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT)
                        element = page.locator(f'a:has-text("{eventPartialID}")')
                        if element.count() == 0:
                            continue
                        else:
                            element.click()
                            page.locator('span:has-text("Tickets")').click()
                            break

                    # loop to get tickets
                    while True:
                        # find ticket elements
                        page.wait_for_selector('div[data-testid^="ticket-list-item-"]', timeout=SELECTOR_TIMEOUT)
                        tickets = page.locator('div[data-testid^="ticket-list-item-"]')

                        # check there are tickets on the page, else restart loop
                        count = tickets.count()
                        if count == 0:
                            time.sleep(1)
                            continue

                        ticketsFound = 0
                        ticketsReleased = False
                        for i in range(0, 5):
                            try:
                                # iterate over each ticket
                                t = tickets.nth(i)
                                text = t.inner_text().lower()

                                # skip if sold out
                                if 'sold out' in text:
                                    continue

                                # otherwise we have a target ticket element
                                ticketsFound += 1

                                # click button to add ticket to basket
                                btn = t.locator('button:not([data-disabled="true"])').first
                                if btn.count() > 0:
                                    btn.click()
                                    ticketsReleased = True

                                # If there is a promo code, we click off the ticket
                                promo_input = page.locator('input[autocomplete="off"][spellcheck="false"]').first
                                if promo_input.count() > 0 and promo_input.is_visible():
                                    btn.locator('button:not([data-disabled="true"])').first.click()
                            except Exception as e:
                                logging.warning(f"Ticket processing error: {e}")
                                break

                        if ticketsReleased:
                            break

                    # Check if any tickets were actually added before attempting to reserve
                    if not ticketsReleased:
                        logging.warning("No available tickets found - retrying")
                        time.sleep(5)
                        continue

                    # reserve tickets
                    page.locator('button:has-text("Reserve")').click()

                    page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT)

                    logging.info("Tickets successfully reserved")
                    break

                except Exception as e:
                    logging.error(f"Reservation failed: {e} - restarting reservation")
                    time.sleep(10)

            # checkout loop - infinite retries
            while True:
                try:
                    page.locator('input[name="ticket-protection"][value="no"]').check()

                    radios = page.locator('input[type="radio"][id$="-radio-no"]')
                    for i in range(radios.count()):
                        radios.nth(i).check()

                    page.locator('button:has-text("Continue")').click()

                    stripe_iframe_element = page.wait_for_selector(
                        "iframe[src*='stripe']",
                        timeout=STRIPE_TIMEOUT
                    )

                    stripe_frame = stripe_iframe_element.content_frame()
                    if stripe_frame is None:
                        raise Exception("Stripe iframe not resolved")

                    # Wait for inputs inside iframe
                    stripe_frame.wait_for_selector("#Field-numberInput", timeout=SELECTOR_TIMEOUT)
                    stripe_frame.wait_for_selector("#Field-expiryInput", timeout=SELECTOR_TIMEOUT)
                    stripe_frame.wait_for_selector("#Field-cvcInput", timeout=SELECTOR_TIMEOUT)
                    stripe_frame.wait_for_selector("#Field-postalCodeInput", timeout=SELECTOR_TIMEOUT)

                    # Fill inputs (DOM-level)
                    stripe_frame.fill("#Field-numberInput", CARDNO)
                    stripe_frame.fill("#Field-expiryInput", EXPIRY)
                    stripe_frame.fill("#Field-cvcInput", CVC)
                    stripe_frame.fill("#Field-postalCodeInput", POSTCODE)

                    pay_button = page.locator('button:has-text("Pay now")')
                    pay_button.click()

                    time.sleep(120)

                    page.screenshot(path=f"screenshot_attempt_{attempt}.png")

                    logging.info("Payment process completed - check screenshot for result")
                    # On success, exit the script
                    sys.exit(0)

                except Exception as e:
                    logging.error(f"Checkout failed: {e} - retrying checkout")
                    time.sleep(10)

    except Exception as e:
        logging.error(f"Browser session failed: {e} - restarting browser")
        time.sleep(15)