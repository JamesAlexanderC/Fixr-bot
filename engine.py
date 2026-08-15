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
import os
import random
from time import sleep # Testing only, should not be used as is blocking

import scan_loop
import get_ticket
import login
import buy_ticket

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
for _handler in (logging.StreamHandler(), logging.FileHandler("logs/engine.log")):
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

inputQueue = asyncio.Queue()
outputQueue = asyncio.Queue()
stopEvent = asyncio.Event()

# global vars for holding camoufox info
scan_session: dict = {}
ticket_sessions: dict = {}
proxies_enabled: bool = True # FOR TESTING, SHLD DEFAULT TO FALSE



async def login_get_ticket(
        session_name,
        email,
        password,
        code,
        url,
):
    try:
        if proxies_enabled:
            try:
                if os.path.exists("proxies.json"):
                    # Here we use the format server:port:username:password
                    with open("proxies.json") as f:
                        proxies = json.load(f)
                    num_proxies = len(proxies)
                    proxy = proxies[random.randint(0, num_proxies-1)].split(":")
                else:
                    raise Exception("No proxies file")
                camoufox = AsyncCamoufox(
                    proxy={
                        "server": f"{proxy[0]}:{proxy[1]}",
                        "username": proxy[2],
                        "password": proxy[3]
                    },
                    geoip=True,
                )
                logger.debug("Proxies loaded successfully")
            except Exception as e:
                logger.error("Error loading proxies: %s", str(e), exc_info=True)
                raise Exception(f"Error loading proxies: {str(e)}") from e
        else:
            camoufox = AsyncCamoufox()
        browser = await camoufox.__aenter__()
        page = await browser.new_page()
        logger.debug("Camoufox started successfully")
    except Exception as e:
        logger.critical("Error starting Camoufox (this will be a pain to debug): %s, ABORTING", str(e), exc_info=True)
        raise Exception(f"Error starting Camoufox (this will be a pain to debug): {str(e)}, ABORTING")
    global ticket_sessions
    ticket_sessions[session_name]["camoufox"] = camoufox
    ticket_sessions[session_name]["browser"] = browser
    ticket_sessions[session_name]["page"] = page
    try:
        page = await login.run(
            page=page,
            email=email,
            password=password,
        )
        logger.debug("Logged in to account %s successfully", email)
    except Exception as e:
        logger.error("Error logging in on %s account: %s", email, str(e), exc_info=True)
        raise e
    try:
        page = await get_ticket.run(
            page=page,
            url=url,
            number=code
        )
        logger.debug("Reserved ticket for account %s successfully", email)
    except Exception as e:
        logger.error("Error getting ticket on %s account: %s", email, str(e), exc_info=True)
        raise e
    await inputQueue.put(f"buy-ticket|{session_name}")

async def clean_camoufox(session: dict):
    if not isinstance(session, dict):
        raise TypeError("'session' must be a dict")
    if not all([session.get("task"), session.get("camoufox")]):
        raise ValueError("Missing required fields: task, camoufox")
    try:
        session["task"].cancel()
        await session["camoufox"].__aexit__(
            None, 
            None, 
            None
        )
        session = {}
    except Exception as e:
        raise Exception(f"Error cancelling camoufox session: {str(e)}") from e

# --------------------------------------------------------------------
# Main Queue handler - takes messages from the queue,
# interprets them and executes them
# --------------------------------------------------------------------

async def queueHandler():
    global scan_session, inputQueue, ticket_sessions, proxies_enabled
    while not stopEvent.is_set():
        msg = await inputQueue.get()
        logger.info("Recieved message: %s", msg)

        if msg == "start-scan-loop":
            logger.info("Message recongised as 'start-scan-loop'")
            if scan_session != {}:
                logger.warning("Scan is already active, IGNORING")
                continue
            try:
                if os.path.exists("accounts.json"):
                    with open("accounts.json", "r") as f:
                        accounts = json.load(f)
                    if len(accounts) == 0:
                        logger.error("Error, no accounts to scan with, ABORTING")
                        continue
                    account = list(accounts.keys())[0]
                else:
                    with open("accounts.json", "w") as f:
                        json.dump({}, f)
                logger.debug("Accounts file loaded successfully")
            except Exception as e:
                logger.error("Error loading accounts: %s, ABORTING (hint: is there invalid JSON in 'accounts.json'?)", str(e), exc_info=True)
                continue
            try:
                if os.path.exists("event.json"):
                    with open("event.json", "r") as f:
                        event = json.load(f)
                    if not all([event.get("organiser_url"), event.get("ticket_keyword"), event.get("scan_interval")]):
                        logger.error("Error, incomplete event data, ABORTING")
                        continue
                    logger.debug("Event file loaded successfully")
                else:
                    raise Exception("No Event file")
            except Exception as e:
                logger.error("Error loading event: %s, ABORTING", str(e), exc_info=True)
                continue
            try:
                if proxies_enabled:
                    try:
                        if os.path.exists("proxies.json"):
                            # Here we use the format server:port:username:password
                            with open("proxies.json") as f:
                                proxies = json.load(f)
                            num_proxies = len(proxies)
                            proxy = proxies[random.randint(0, num_proxies-1)].split(":")
                            logger.debug(f"proxy host: {proxy[0]}, proxy port: {proxy[1]}")
                            logger.debug(f"proxy username: {proxy[2]}")
                            logger.debug(f"proxy password: {proxy[3]}")
                        else:
                            raise Exception("No proxies file")
                        camoufox = AsyncCamoufox(
                            proxy={
                                "server": f"{proxy[0]}:{proxy[1]}",
                                "username": proxy[2],
                                "password": proxy[3]
                            },
                            geoip=True,
                        )
                        logger.debug("Proxies loaded successfully")
                    except Exception as e:
                        logger.error("Error loading proxies: %s", str(e), exc_info=True)
                        raise Exception(f"Error loading proxies: {str(e)}") from e
                else:
                    camoufox = AsyncCamoufox()
                browser = await camoufox.__aenter__()
                page = await browser.new_page()
                logger.debug("Camoufox started successfully")
                await page.goto("https://google.com")
                sleep(10)
            except Exception as e:
                logger.critical("Error starting Camoufox (this will be a pain to debug): %s, ABORTING", str(e), exc_info=True)
                continue
            try:
                page = await login.run(
                    page=page, 
                    email=account, 
                    password=accounts[account]
                )
                logger.debug("Logged in successfully")
            except Exception as e:
                logger.error("Error during login: %s, ABORTING", str(e), exc_info=True)
                try: 
                    await camoufox.__aexit__()
                except Exception as e:
                    logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                finally:
                    continue
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
                scan_session = {"camoufox": camoufox, "browser": browser, "task": task}
                logger.debug("Created scan task successfully")
            except Exception as e:
                logger.error("Error creating scan task: %s, ABORTING", str(e), exc_info=True)
                try:
                    await clean_camoufox(scan_session)
                except Exception as e:
                    logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                finally:
                    continue

        elif msg == "stop-scan-loop":
            logger.info("Message is recognised as 'stop-scan-loop'")
            if scan_session == {}:
                logger.warning("Scan is not active, IGNORING")
                continue
            try:
                scan_session["task"].cancel()
                await scan_session["camoufox"].__aexit__(
                    None, 
                    None, 
                    None
                )
                logger.debug("Stopped scan task successfully")
            except Exception as e:
                logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                continue
            scan_session = {}

        elif msg.split("|")[0] == "get-tickets":
            logger.info("Message is recognised as 'get-tickets'")
            try: 
                scan_session["task"].cancel()
                await scan_session["camoufox"].__aexit__(
                    None, 
                    None, 
                    None
                )
                logger.debug("Coroutine and camoufox task stopped successfully")
            except Exception as e:
                logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                continue
            scan_session = {}
            try:
                with open("accounts.json") as f:
                    accounts = json.load(f)
                logger.debug("Accounts loaded successfully")
            except Exception as e:
                logger.error("Error loading accounts: %s, ABORTING", str(e), exc_info=True)
                continue
            for account in accounts.keys():
                try:
                    session_name = str(uuid.uuid4())
                    # code is currently hardcoded and not very well named, will rework at some point to be ticket keyword but until then will be this
                    task = asyncio.create_task(
                        login_get_ticket(
                            session_name=session_name,
                            email=account, 
                            password=accounts[account],
                            code=1,
                            url=msg.split("|")[1],
                        )
                    )
                    # This relies on running before the coroutine above, which is nondeterministic (could cause problems in future)
                    ticket_sessions[session_name] = {"task": task}
                    logger.info("Created get ticket task for %s successfully", account)
                except Exception as e:
                    logger.error("Error creating ticket task for %s: %s, ABORTING", account, str(e), exc_info=True)
                    try:
                        await clean_camoufox(ticket_sessions[session_name])
                    except Exception as e:
                        logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                    finally:
                        continue

        elif msg.split("|")[0] == "buy-ticket":
            logger.info("Message is recognised as 'buy-tickets'")
            try:
                camoufox = ticket_sessions[msg.split("|")[1]]["camoufox"]
                page = ticket_sessions[msg.split("|")[1]]["page"]
                logger.debug("Message parsed successully: %s", msg.split("|"))
            except Exception as e:
                logger.error("Error parsing 'buy-tickets' message: %s, ABORTING", str(e), exc_info=True)
                continue
            try:
                with open("card.json", "r") as f:
                    card = json.load(f)
                if not all([card.get("cardNumber"), card.get("cardExpiry"), card.get("cardCvc"), card.get("cardPostcode")]):
                    logger.error("Error, incomplete card data, ABORTING")
                    continue
                logger.debug("Card loaded successfully")
            except Exception as e:
                logger.error("Error loading card: %s, ABORTING", str(e), exc_info=True)
                continue
            try:
                await buy_ticket.buy(
                    page=page,
                    cnumber=card.get("cardNumber"),
                    expiry=card.get("cardExpiry"),
                    cvc=card.get("cardCvc"),
                    postal=card.get("cardPostcode"),
                )
                logger.info("Ticket purchase completed successfully")
            except Exception as e:
                logger.error("Error during ticket purchase: %s, ABORTING", str(e), exc_info=True)
                try:
                    await clean_camoufox(ticket_sessions[msg.split("|")[1]])
                except Exception as e:
                    logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                finally:
                    continue
            try:
                ticket_sessions[msg.split("|")[1]]["task"].cancel()
                await ticket_sessions[msg.split("|")[1]]["camoufox"].__aexit__(
                    None,
                    None,
                    None,
                )
            except Exception as e:
                logger.critical("Failed to stop coroutine and Camoufox instance: %s, ABORTING", str(e), exc_info=True)
                continue

        else:
            logger.warning("No known action for message: %s, IGNORING", msg)
            continue