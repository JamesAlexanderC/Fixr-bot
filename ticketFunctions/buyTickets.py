# ----------------------------------------------------
''' 
Async version of buyTickets
'''
# ----------------------------------------------------

import os
from asyncio import sleep
from dotenv import load_dotenv


async def buy(page):
    load_dotenv()

    cnumber = os.getenv('CARD_NUMBER')
    expiry = os.getenv('CARD_EXPIRY')
    cvc = os.getenv('CARD_CVC')
    postal = os.getenv('CARD_POSTCODE')

    if cnumber is None or expiry is None or cvc is None or postal is None:
        raise ValueError('CARD_NUMBER, CARD_EXPIRY, CARD_CVC, and CARD_POSTCODE must be set in the environment')

    # STEP 1
    await page.locator('#ticket-protection-no').check()

    # STEP 2
    await page.locator("input[value='no']").nth(1).check()

    # STEP 3
    await page.get_by_role("button", name="Continue", exact=True).click()

    # STEP 4
    await page.wait_for_load_state(state='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    # STEP 5 Most unreliable part is knowing how long it takes for fields to load - have to guess
    while True:

        # STEP 6
        frames = page.locator('iframe')

        success = False

        # STEP 7
        for i in range(await frames.count()):
            frame = page.frame_locator('iframe').nth(i)
            try:
                await frame.locator('#payment-numberInput').fill(cnumber, timeout=2000)
                await frame.locator('#payment-expiryInput').fill(expiry, timeout=2000)
                await frame.locator('#payment-cvcInput').fill(cvc, timeout=2000)
                await frame.locator('#payment-postalCodeInput').fill(postal, timeout=2000)
                success = True
                break
            except Exception:
                print(f'frame {i} has no matching ids')
                continue
        
        if success: break

    # STEP 8
    await page.get_by_role("button", name="Pay now", exact=True).click()

    return page