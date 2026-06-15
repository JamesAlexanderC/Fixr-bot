import asyncio
from camoufox.async_api import AsyncCamoufox
import json

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
# TESTING
# --------------------------------------------------------------------
async def runTests():
    async with AsyncCamoufox(
            geoip=True,
            i_know_what_im_doing=True,
            disable_coop=True
        ) as browser:
        page1 = await createPage(browser)
        await ticketSearch(page1, "test")

if __name__ == "__main__":
    asyncio.run(runTests())