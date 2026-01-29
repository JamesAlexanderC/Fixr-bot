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
    camoufox_kwargs = {"disable_coop": True, "window": (1280, 720), "i_know_what_im_doing": True, "geoip": True, "headless": True}
    if proxy is not None:
        camoufox_kwargs["proxy"] = proxy
    
    with Camoufox(**camoufox_kwargs) as browser:
        page = browser.new_page()
        
        # Try connect to fixr, error occurs here, network is either unreachable, libraries are no longer valid, or fixr layout has been changed rendering this script useless
        try:
            page.goto("https://fixr.co/login")
            print("Connected to fixr")
        except:
            raise Exception(
                "ERROR: could not connect to internet / this script is depreciated"
            )

        # keep track of errors to allow for sensible reconnection attempts
        error_count = 0

        # login loop, retries up to 5 times before prompting user to check email and password
        while error_count <= 5:
            try:
                page.wait_for_selector('input[type="email"]')
                page.fill('input[type="email"]', email)

                page.click('button:has-text("Continue")')

                page.wait_for_selector('input[type="password"]')
                page.fill('input[type="password"]', password)

                page.click('button:has-text("Sign in")')

                page.wait_for_load_state("networkidle")

                print("Succesfully logged into fixr with provided account")
                break
            except:
                print("Could not log in - retrying")
                error_count += 1
        
        if error_count > 5:
            raise Exception(
                f"ERROR: could not login in with provided details ensure fixr account (email:{email}, password:{password}) exists"
            )
        
        # reserve loop, more lenient number of reconnection attempts as more failure points during reservation process - if fails just restarts process
        while error_count <= 10:
            try:
                # This loop handles expected refreshing of fixr events page to try find match for event identifier
                while True:
                    # slight delay between connection requests to improve durability and prevent detection from fixr
                    time.sleep(2.5)
                    
                    # this flow finds the specified event on the timepiece page
                    CT = time.ctime(time.time())
                    print(f"Page refreshed at {CT}")
                    page.goto(f"{organiserURL}")
                    element = page.locator(f'a:has-text("{eventPartialID}")')
                    if element.count() == 0:
                        pass
                    else:
                        element.click()
                        element = page.locator('span:has-text("Tickets")').click()
                        break
                
                # loop to get tickets
                while True:
                    # find ticket elements
                    page.wait_for_selector('div[data-testid^="ticket-list-item-"]')
                    tickets = page.locator('div[data-testid^="ticket-list-item-"]')
                    
                    # check there are tickets on the page, else restart loop
                    count = tickets.count()
                    if count == 0:
                        break

                    ticketsFound = 0
                    ticketsReleased = False
                    for i in range(count):
                        # iterate over each ticket
                        t = tickets.nth(i)
                        text = t.inner_text().lower()
                        
                        # skip if sold out
                        if 'sold out' in text:
                            continue
                        
                        # otherwise we have a target ticket element
                        else: ticketsFound += 1
                        
                        # click button to add ticket to basket
                        btn = t.locator('button:not([data-disabled="true"])').first
                        if btn.count() > 0:
                            btn.click()
                            ticketsReleased = True
                        
                        # If there is a promo code, we click off the ticket
                        promo_input = page.locator('input[autocomplete="off"][spellcheck="false"]').first
                        if promo_input.count() > 0 and promo_input.is_visible():
                            btn = t.locator('button:not([data-disabled="true"])').first.click()


                    # if tickets have all sold out / were never available
                    # if ticketsFound == 0: return False commented out to allow running further in advance 20.01.2026

                    if ticketsReleased == True:
                        break

                # reserve tickets
                page.locator('button:has-text("Reserve")').click()

                page.wait_for_load_state("networkidle")

                print("Tickets succesfully reserved")
                break
            
            except:
                error_count += 1
        
        if error_count > 10:
            print("Connection error - restarting browser")
            break
        
        # checkout loop, pretty simple but does expose some automation components so slightly more volatile than the other 2
        while error_count <= 10:
            page.locator('input[name="ticket-protection"][value="no"]').check()
    
            radios = page.locator('input[type="radio"][id$="-radio-no"]')
            for i in range(radios.count()):
                radios.nth(i).check()

            page.locator('button:has-text("Continue")').click()
            
            stripe_iframe_element = page.wait_for_selector(
                "iframe[src*='stripe']",
                timeout=15000
            )

            stripe_frame = stripe_iframe_element.content_frame()
            assert stripe_frame is not None, "Stripe iframe not resolved"

            # Wait for inputs inside iframe
            stripe_frame.wait_for_selector("#Field-numberInput")
            stripe_frame.wait_for_selector("#Field-expiryInput")
            stripe_frame.wait_for_selector("#Field-cvcInput")
            stripe_frame.wait_for_selector("#Field-postalCodeInput")

            # Fill inputs (DOM-level)
            stripe_frame.fill("#Field-numberInput", CARDNO)
            stripe_frame.fill("#Field-expiryInput", EXPIRY)
            stripe_frame.fill("#Field-cvcInput", CVC)
            stripe_frame.fill("#Field-postalCodeInput", POSTCODE)
            
            pay_button = page.locator('button:has-text("Pay now")')
            pay_button.click()

            time.sleep(10)

            page.screenshot(path="page.png")