"""
engine.py as of 26/07/2026

### This file contains orchestration logic for the browser, it creates async tasks based on messages in the input queue, the messages it takes are defined below:

start-scan-loop
stop-scan-loop

"""

import json
import asyncio
from coroutines import *
from camoufox.async_api import AsyncCamoufox

import scan_loop
import login

inputQueue = asyncio.Queue()
outputQueue = asyncio.Queue()
stopEvent = asyncio.Event()

scan_session = None


def log(msg):
    with open("engine.log", "a") as f:
        f.write("\n")
        f.write(str(msg))

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

            try:
                with open("accounts.json") as f:
                    accounts = json.load(f)
            except Exception as error:
                log("error loading accounts.json")
                log(error)

            try:
                account = list(accounts.keys())[0]
            except IndexError:
                log("no accounts stored")
            except Exception as error:
                log("error finding first stored account")
                log(error)

            try:
                with open("event.json") as f:
                    event = json.load(f)
            except:
                log("error loading event.json")
                log(error)

            try:
                camoufox = AsyncCamoufox(disable_coop=True)
                browser = await camoufox.__aenter__()
                page = await browser.new_page()
            except Exception as error:
                log("error starting camoufox")
                log(error)

            try:
                page = await login.login(page=page, email=account, password=accounts[account])
            except Exception as error:
                log("error logging in")
                log(error)

            try:
                task = asyncio.create_task(
                    scan_loop.run(
                        page=page,
                        url=event["organiser_url"],
                        ticket_keyword=event["ticket_keyword"],
                        interval=int(event["scan_interval"])
                    )
                )
            except Exception as error:
                log("error during scan loop")
                log(error)

            scan_session = {"camoufox": camoufox, "browser": browser, "task": task}

        if msg == "stop-scan-loop":

            if scan_session == None:
                continue

            scan_session["task"].cancel()

            await scan_session["camoufox"].__aexit__(None, None, None)

            scan_session = None

    

# TESTING
if __name__ == "__main__":
    pass
