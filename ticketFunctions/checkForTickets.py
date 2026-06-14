# ----------------------------------------------------
''' 
Async version of checkForTickets
'''
# ----------------------------------------------------

import os

from dotenv import load_dotenv


async def check(page):
    load_dotenv()

    url = os.getenv('ORGANISER_URL')

    if url is None:
        raise ValueError('ORGANISER_URL must be set in the environment')

    # STEP 1
    await page.goto(url)

    # STEP 2
    await page.wait_for_load_state('load')

    # STEP 3
    tickets = page.get_by_text('Wednesday').first

    # STEP 4
    if await tickets.count() == 0:
        return False

    # STEP 5
    await tickets.click()

    # STEP 6
    await page.wait_for_load_state('networkidle')

    # STEP 7
    ticketButton = page.get_by_text('Tickets', exact=True).first

    # STEP 8
    if await ticketButton.count() == 0:
        return False

    # STEP 9
    await ticketButton.click()

    # STEP 10
    return page.url
