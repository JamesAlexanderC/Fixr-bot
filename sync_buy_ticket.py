# ----------------------------------------------------
''' 
Sync version of buyTickets
'''
# ----------------------------------------------------

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
for _handler in (logging.StreamHandler(), logging.FileHandler("logs/buy_ticket.log")):
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)


def buy(
        page,
        cnumber,
        expiry,
        cvc,
        postal
    ):

    # STEP 1
    page.locator('#ticket-protection-no').check()
    logger.debug("STEP 1")

    # STEP 2
    page.locator("input[value='no']").nth(1).check()
    logger.debug("STEP 2")

    # STEP 3
    page.get_by_role("button", name="Continue", exact=True).click()
    logger.debug("STEP 3")

    # STEP 4
    page.wait_for_load_state(state='domcontentloaded')
    page.wait_for_load_state('networkidle')
    logger.debug("STEP 4")

    # STEP 5 Most unreliable part is knowing how long it takes for fields to load - have to loop until they appear with 
    # a timeout fast enough to be reasonable but slow enough not to trigger before input fields have loaded
    while True:

        # STEP 6
        frames = page.locator('iframe')
        logger.debug("STEP 6")

        success = False

        # STEP 7
        for i in range(frames.count()):
            frame = page.frame_locator('iframe').nth(i)
            try:
                frame.locator('#payment-numberInput').fill(cnumber, timeout=2000)
                frame.locator('#payment-expiryInput').fill(expiry, timeout=2000)
                frame.locator('#payment-cvcInput').fill(cvc, timeout=2000)
                frame.locator('#payment-postalCodeInput').fill(postal, timeout=2000)
                success = True
                break
            except Exception:
                logger.debug(f'STEP 7 : frame {i} has no matching ids')
                continue
        
        if success: break

    # STEP 8
    page.get_by_role("button", name="Pay now", exact=True).click()
    logger.debug("STEP 8")

    return page
