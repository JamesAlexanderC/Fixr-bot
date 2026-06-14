# ----------------------------------------------------
''' 
Async version of reserveTickets
'''
# ----------------------------------------------------

import os
from dotenv import load_dotenv

async def reserve(page, url):
    load_dotenv()

    number = os.getenv('TICKET_NUMBER')

    # STEP 1
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_load_state('networkidle')

    # STEP 2
    buttons = page.locator("button[data-disabled='false']")
    num_buttons = await buttons.count()

    # This reserve ticket flow only reserves one ticket per account - tries a specified number ticket, then reverts to cycling to first unprotected ticket
    try:
        before_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

        # STEP 4
        print(number)
        button = buttons.nth(int(number)-1)
        print('test')
        await button.click(timeout = 3000)

        # STEP 5
        after_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

        # STEP 6
        if after_fields > before_fields:
            await button.click()
            raise Exception("Requested ticket locked with promo code - switching to first found ticket")
    except:
        print("SHOULD PRINT")
        for i in range(num_buttons):
            before_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

            # STEP 4
            button = buttons.nth(i)
            await button.click()

            # STEP 5
            after_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

            # STEP 6
            if after_fields == before_fields:
                break


    # STEP 7
    await page.locator("button", has_text='Reserve').first.click()

    # WAIT FOR IDLE NETWORK
    await page.wait_for_load_state('networkidle')

    # RETURN
    return page
