"""
engine.py as of 26/07/2026

### This file contains orchestration logic for the browser, it creates async tasks based on messages in the input queue, the messages it takes are defined below:

start-scan-loop
stop-scan-loop
get-ticket|{URL}

"""

import json
import asyncio
from coroutines import *
from camoufox.async_api import AsyncCamoufox

import scan_loop
import get_ticket
import login

inputQueue = asyncio.Queue()
outputQueue = asyncio.Queue()
stopEvent = asyncio.Event()

scan_session = None
reserve_sessions = []


async def login_get_ticket(
        page,
        email,
        password,
        code,
        url,
):
    page = await login.run(
        page=page,
        email=email,
        password=password,
    )

    page = await get_ticket.run(
        page=page,
        url=url,
        number=code,
    )

    return page

# --------------------------------------------------------------------
# Main Queue handler - basically takes messages from the queue,
# interprets them and executes them
# --------------------------------------------------------------------

async def queueHandler():
    global scan_session

    while not stopEvent.is_set():

        msg = await inputQueue.get()

        if msg == "start-scan-loop":

            if scan_session != None:
                continue

            with open("accounts.json") as f:
                accounts = json.load(f)

            account = list(accounts.keys())[0]

            with open("event.json") as f:
                event = json.load(f)
 
            camoufox = AsyncCamoufox()
            browser = await camoufox.__aenter__()
            page = await browser.new_page()

            page = await login.run(
                page=page, 
                email=account, 
                password=accounts[account]
            )

            task = asyncio.create_task(
                scan_loop.run(
                    page=page,
                    url=event["organiser_url"],
                    ticket_keyword=event["ticket_keyword"],
                    interval=int(event["scan_interval"])
                )
            )

            scan_session = {"camoufox": camoufox, "browser": browser, "task": task}

        if msg == "stop-scan-loop":

            if scan_session == None:
                continue

            scan_session["task"].cancel()

            await scan_session["camoufox"].__aexit__(
                None, 
                None, 
                None
            )

            scan_session = None

        if msg.split("|")[0] == "get-ticket":

            global reserve_sessions

            with open("accounts.json") as f:
                accounts = json.load(f)

            for account in accounts.keys():

                camoufox = AsyncCamoufox(disable_coop=True, i_know_what_im_doing=True)
                browser = await camoufox.__aenter__()
                page = await browser.new_page()

                task = asyncio.create_task(
                    login_get_ticket(
                        page=page, 
                        email=account, 
                        password=accounts[account],
                        code=1,
                        url=msg.split("|")[1]
                    )
                )

                reserve_sessions.append({"camoufox": camoufox, "browser": browser, page: "page", "task": task})

        if msg.split("|")[0] == "got-ticket":
            pass



# TESTING
if __name__ == "__main__":
    pass
