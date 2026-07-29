"""
engine.py as of 26/07/2026

### This file contains orchestration logic for the browser, it creates async tasks based on messages in the input queue, the messages it takes are defined below:

start-scan-loop
stop-scan-loop
get-tickets|{url}
got-ticket|{session_name}

"""

import json
import uuid
import asyncio
from camoufox.async_api import AsyncCamoufox

import scan_loop
import get_ticket
import login

inputQueue = asyncio.Queue()
outputQueue = asyncio.Queue()
stopEvent = asyncio.Event()

# global vars for holding camoufox info
scan_session = None
ticket_sessions = {}


async def login_get_ticket(
        session_name,
        email,
        password,
        code,
        url,
):

    camoufox = AsyncCamoufox(disable_coop=True, i_know_what_im_doing=True)
    browser = await camoufox.__aenter__()
    page = await browser.new_page()

    ticket_sessions[session_name]["camoufox"] = camoufox
    ticket_sessions[session_name]["browser"] = browser
    ticket_sessions[session_name]["page"] = page
    
    page = await login.run(
        page=page,
        email=email,
        password=password,
    )

    page = await get_ticket.run(
        page=page,
        url=url,
        number=code
    )

    await inputQueue.put(f"buy-ticket|{session_name}")

def log(msg):
    with open("engine.log", "a") as f:
        f.write("\n")
        f.write(str(msg))

# --------------------------------------------------------------------
# Main Queue handler - basically takes messages from the queue,
# interprets them and executes them
# --------------------------------------------------------------------

async def queueHandler():
    global scan_session, inputQueue, ticket_sessions

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

            try:
                page = await login.run(
                    page=page, 
                    email=account, 
                    password=accounts[account]
                )
            except:
                log("login error")

            log("login completed")

            try:
                task = asyncio.create_task(
                    scan_loop.run(
                        page=page,
                        url=event["organiser_url"],
                        ticket_keyword=event["ticket_keyword"],
                        interval=int(event["scan_interval"]),
                        inputQueue=inputQueue,
                    )
                )
            except:
                log("task failed to be made")

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

        if msg.split("|")[0] == "get-tickets":

            scan_session["task"].cancel()

            await scan_session["camoufox"].__aexit__(
                None, 
                None, 
                None
            )

            scan_session = None

            with open("accounts.json") as f:
                accounts = json.load(f)

            for account in accounts.keys():

                session_name = str(uuid.uuid4())

                task = asyncio.create_task(
                    login_get_ticket(
                        session_name=session_name,
                        email=account, 
                        password=accounts[account],
                        code=1,
                        url=msg.split("|")[1],
                    )
                )

                ticket_sessions[session_name]= {"task": task}

        if msg.split("|")[0] == "buy-ticket":

            camoufox = ticket_sessions[msg.split("|")[1]]["camoufox"]
            page = ticket_sessions[msg.split("|")[1]]["page"]

            try:
                from checkout import buy_tickets

                with open("card.json", "r") as f:
                    card = json.load(f)

                await buy_tickets.run(
                    session_name=msg.split("|")[1],
                    page=page,
                    cnumber=card["cnumber"],
                    expiry=card["expiry"],
                    cvc=card["cvc"],
                    postal=card["postal"],
                    inputQueue=inputQueue,
                )

            except:

                url = ticket_sessions[msg.split("|")[1]]["page"].url

                ticket_sessions[msg.split("|")[1]].cancel()

                ticket_sessions[msg.split("|")[1]]["camoufox"].__aexit__(
                    None,
                    None,
                    None,
                )

                # Sedn notification with url to email/whatsapp/discord/telegram



# TESTING
if __name__ == "__main__":
    pass
