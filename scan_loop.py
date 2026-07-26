"""
Scan loop
"""

import asyncio

def log(msg):
    with open("scan.log", "a") as f:
        f.write("\n")
        f.write(str(msg))

async def run(
    page, 
    url,
    ticket_keyword,
    interval,
):

    count = 0

    while True:

        count += 1

        # WAIT
        await asyncio.sleep(interval)

        log(f"Starting loop {count}")

        # STEP 1
        try:
            await page.goto(url)
        except Exception as error:
            log(f"error going to url {url}")
            log(error)
            raise error

        # STEP 2
        try:
            await page.wait_for_load_state('load')
        except Exception as error:
            log("error waiting ofr load state load")
            log(error)
            raise error

        # STEP 3
        try:
            tickets = page.get_by_text(ticket_keyword).first
        except Exception as error:
            log(f"error whilst counting tickets by keyword {ticket_keyword}")
            log(error)
            raise error

        # STEP 4
        if await tickets.count() == 0:
            continue

        # STEP 5
        try:
            await tickets.click()
        except Exception as error:
            log("error clicking found ticket")
            log(error)
            raise error

        # STEP 6
        try:
            await page.wait_for_load_state('networkidle')
        except Exception as error:
            log("error waiting for network state networkidle")
            log(error)
            raise error

        # STEP 7
        try:
            ticketButton = page.get_by_text('Tickets', exact=True).first
        except Exception as error:
            log("error finding tickets button")
            log(error)
            raise error

        # STEP 8
        if await ticketButton.count() == 0:
            continue

        # STEP 9
        try:
            await ticketButton.click()
        except Exception as error:
            log("error clicking tickes button")
            log(error)
            raise error

        # STEP 10
        return page.url