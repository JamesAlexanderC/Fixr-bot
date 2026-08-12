# ----------------------------------------------------
''' 
Async version of reserveTickets
'''
# ----------------------------------------------------

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
for _handler in (logging.StreamHandler(), logging.FileHandler("logs/get_ticket.log")):
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

async def run(
    page, 
    url, 
    number
):

    # STEP 1
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_load_state('networkidle')
    logger.debug("STEP 1")

    # STEP 2
    buttons = page.locator("button[data-disabled='false']")
    num_buttons = await buttons.count()
    logger.debug("STEP 2")

    # This reserve ticket flow only reserves one ticket per account - tries a specified number ticket ('code' - the badly named variable I need to rework), 
    # then reverts to cycling to first unprotected ticket
    try:
        before_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

        # STEP 4
        button = buttons.nth(int(number)-1)
        await button.click(timeout = 3000)
        logger.debug("STEP 4")

        # STEP 5
        after_fields = await page.locator('input:visible, select:visible, textarea:visible').count()
        logger.debug("STEP 5")

        # STEP 6
        if after_fields > before_fields:
            await button.click()
            raise Exception("Requested ticket locked with promo code - switching to first found ticket")
        logger.debug("STEP 6")
    except:
        for i in range(num_buttons):
            before_fields = await page.locator('input:visible, select:visible, textarea:visible').count()

            # STEP 7
            button = buttons.nth(i)
            await button.click()
            logger.debug("STEP 7")

            # STEP 8
            after_fields = await page.locator('input:visible, select:visible, textarea:visible').count()
            logger.debug("STEP 8")

            # STEP 9
            if after_fields == before_fields:
                break
            logger.debug("STEP 9")


    # STEP 10
    await page.locator("button", has_text='Reserve').first.click()
    logger.debug("STEP 10")

    # WAIT FOR IDLE NETWORK
    await page.wait_for_load_state('networkidle')

    # RETURN
    return page
