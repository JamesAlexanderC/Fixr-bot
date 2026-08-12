"""
Scan loop
"""

import asyncio
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
for _handler in (logging.StreamHandler(), logging.FileHandler("logs/scan_loop.log")):
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

async def run(
    page, 
    url,
    ticket_keyword,
    interval,
    inputQueue,
):

    count = 0

    while True:

        count += 1

        # WAIT
        await asyncio.sleep(interval)
        logger.debug(f"STARTING SCAN: {count}")


        # STEP 1
        await page.goto(url)
        logger.debug("STEP 1")

        # STEP 2
        await page.wait_for_load_state('load')
        logger.debug("STEP 2")

        # STEP 3
        tickets = page.get_by_text(ticket_keyword).first
        logger.debug("STEP 3")

        # STEP 4
        if await tickets.count() == 0:
            continue
        logger.debug("STEP 4")

        # STEP 5
        await tickets.click()
        logger.debug("STEP 5")

        # STEP 6
        await page.wait_for_load_state('networkidle')
        logger.debug("STEP 6")

        # STEP 7
        ticketButton = page.get_by_text('Tickets', exact=True).first
        logger.debug("STEP 7")


        # STEP 8
        if await ticketButton.count() == 0:
            continue
        logger.debug("STEP 8")

        # STEP 9
        await ticketButton.click()
        logger.debug("STEP 9")

        # STEP 10
        await inputQueue.put(f"get-tickets|{page.url}")
        logger.debug("STEP 10")