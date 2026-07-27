"""import asyncio
import os
from camoufox.async_api import AsyncCamoufox

from checkout import buyTickets
import scan_loop
from unused import reserveTickets

# --------------------------------------------------------------------
# The 'Get Tickets' flow, made it very robust
# --------------------------------------------------------------------

def _get_account_codes():
    configured_codes = os.getenv("ACCOUNT_CODES")
    if configured_codes:
        return [code.strip() for code in configured_codes.split(",") if code.strip()]

    codes = []
    index = 1
    while True:
        email = os.getenv(f"ACCE{index}")
        password = os.getenv(f"ACCP{index}")

        if email is None and password is None:
            break

        if email is None or password is None:
            raise ValueError(f"ACCE{index} and ACCP{index} must both be set when using numbered account slots")

        codes.append(str(index))
        index += 1

    if not codes:
        raise ValueError("No account credentials were found. Set ACCOUNT_CODES or ACCE1/ACCP1 pairs in the environment")

    return codes


async def _run_ticket_flow(browser, url, account_code):
    page = await createPage(browser)

    try:
        for i in range(3):
            try:
                await login.login(page, account_code)
                output.info(f"login successful for account {account_code}")
                break
            except Exception as exc:
                if i < 2:
                    output.info(f"Login failed for account {account_code} on attempt {i + 1}, retrying: {exc}")
                else:
                    output.info(f"Login failed for account {account_code} after {i + 1} attempts")
                    return False

        for i in range(3):
            try:
                await reserveTickets.reserve(page, url)
                output.info(f"reservation successful for account {account_code}")
                break
            except Exception as exc:
                if i < 2:
                    output.info(f"Reservation failed for account {account_code} on attempt {i + 1}, retrying: {exc}")
                else:
                    output.info(f"Reservation failed for account {account_code} after {i + 1} attempts")
                    return False

        for i in range(20):
            try:
                await buyTickets.buy(page)
                output.info(f"buy successful for account {account_code}")
                return True
            except Exception as exc:
                if (i % 5) != 0:
                    output.info(f"Buy failed for account {account_code} on attempt {i + 1}, retrying in 5 seconds: {exc}")
                    await asyncio.sleep(5)
                else:
                    output.info(f"Buy failed for account {account_code} on attempt {i + 1}, retrying in 20 seconds: {exc}")
                    await asyncio.sleep(20)

        return False
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def getTickets(page, url, queue):
    browser = page.context.browser
    account_codes = _get_account_codes()

    output.info(f"Starting {len(account_codes)} parallel ticket flow(s)")

    results = await asyncio.gather(
        *[_run_ticket_flow(browser, url, account_code) for account_code in account_codes],
        return_exceptions=True,
    )

    successes = sum(1 for result in results if result is True)
    failures = len(results) - successes
    output.info(f"Parallel ticket flows finished: {successes} succeeded, {failures} failed")

# --------------------------------------------------------------------
# Ticket Checking Heartbeat - checks FIXR website repeatedly for tickets,
# and if it finds any it alerts the engine. 5 minute heartbeat.
# --------------------------------------------------------------------

async def ticketSearch(page, queue):
    i = 0
    while True:
        await asyncio.sleep(3)

        try:
            there = await scan_loop.check(page)

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
    asyncio.run(runTests())"""