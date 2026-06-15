import asyncio
from camoufox.async_api import AsyncCamoufox

from ticketFunctions import checkForTickets, loginToAccount, reserveTickets, buyTickets
import output

# --------------------------------------------------------------------
# The 'Get Tickets' flow, made it very robust
# --------------------------------------------------------------------

async def getTickets(page, url, queue ):

    for i in range(3):
        try:
            await loginToAccount.login(page)
            output.info("login successful")
            break
        except:
            if i < 2:
                output.info(f"Login failed on attempt {i+1}, retrying")
            else:
                output.info(f"Login failed on attempt {i+1}, requesting browser refresh")
                await queue.put("REFRESH_BROWSER")
                return

    for i in range(3):
        try:
            await reserveTickets.reserve(page, url)
            output.info("reservation successful")
            break
        except:
            if i < 2:
                output.info(f"Reservation failed on attempt {i+1}, retrying")
            else:
                output.info(f"Reservation failed on attempt {i+1}, requesting browser refresh")
                await queue.put("REFRESH_BROWSER")
                return

    for i in range(20):
        try:
            await buyTickets.buy(page)
            output.info("buy successful")
            break
        except:
            if (i%5) != 0:
                output.info(f"Buy failed on attempt {i+1}, retrying with 5 second wait")
                await asyncio.sleep(5)
            else:
                output.info(f"Buy failed on attempt {i+1}, retrying with 20 second wait")
                await asyncio.sleep(20)

# --------------------------------------------------------------------
# Ticket Checking Heartbeat - checks FIXR website repeatedly for tickets,
# and if it finds any it alerts the engine. 5 minute heartbeat.
# --------------------------------------------------------------------

async def ticketSearch(page, queue):
    i = 0
    while True:
        await asyncio.sleep(3)

        try:
            there = await checkForTickets.check(page)

        except:
            output.info(f"search failed on attempt {i+1}, requesting browser refresh")
            await queue.put("REFRESH_BROWSER")
            there = False

        if there:
            await queue.put(f"TICKETS_FOUND|{there}")
            output.info(f"Found tickets: {there}")
            return

# --------------------------------------------------------------------
# Create and refresh page
# --------------------------------------------------------------------

async def createPage(browser):
    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    return page

async def refreshPage(page):
    output.info("Refreshing browser context")

    browser = page.context.browser
    
    try:
        if not page.is_closed():
            await page.close()
    except Exception:
        pass

    try:
        await page.context.close()
    except Exception:
        pass

    context = await browser.new_context(ignore_https_errors=True)
    new_page = await context.new_page()

    return new_page

# --------------------------------------------------------------------
# Store secrets
# --------------------------------------------------------------------

async def storeSecrets(
        email = None, 
        password = None, 
        fname = None,
        lname = None,
        dob = None,
        phone = None,
        cardNumber = None,
        cardExpiry = None,
        cardCvc = None,
        cardCountry = None,
        cardPostcode = None
        ):
    updates = {}

    if email is not None:
        updates["EMAIL"] = str(email)
    if password is not None:
        updates["PASSWORD"] = str(password)
    if fname is not None:
        updates["FIRST_NAME"] = str(fname)
    if lname is not None:
        updates["LAST_NAME"] = str(lname)
    if dob is not None:
        updates["DOB"] = str(dob)
    if phone is not None:
        updates["PHONE"] = str(phone)
    if cardNumber is not None:
        updates["CARD_NUMBER"] = str(cardNumber)
    if cardExpiry is not None:
        updates["CARD_EXPIRY"] = str(cardExpiry)
    if cardCvc is not None:
        updates["CARD_CVC"] = str(cardCvc)
    if cardCountry is not None:
        updates["CARD_COUNTRY"] = str(cardCountry)
    if cardPostcode is not None:
        updates["CARD_POSTCODE"] = str(cardPostcode)

    if len(updates) == 0:
        return False

    existing = {}

    try:
        with open('.env', 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if line == "" or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                existing[key] = value
    except FileNotFoundError:
        pass

    existing.update(updates)

    with open('.env', 'w') as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")

    return True

# --------------------------------------------------------------------
# TESTING
# --------------------------------------------------------------------
async def runTests():
    async with AsyncCamoufox(
            geoip=True,
            i_know_what_im_doing=True,
            disable_coop=True
        ) as browser:
        page = await createPage(browser)
        await storeSecrets(email = '17clarkeja@gmail.com')
        await ticketSearch(page, "test")

if __name__ == "__main__":
    asyncio.run(runTests())