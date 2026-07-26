"""
# API.py as of 26/07/2026

### This file contains the FastAPI server, and exposes the endpoints defined boloew:
- /edit-card: (POST) edits stored card with given details, returns 400 if details are incomplete, 400 if loop is active

- /accounts: (GET) lists all currently stored accounts
- /accounts: (POST) stores new acount with given details, returns 400 if email is already stored, 400 if loop is active

- /event: (GET) lists details about the currently stored event
- /event: (POST) edits event with given details, 400 if scan loop is active

- /start-scan (GET) starts the scanning loop, returns 400 if loop is active
- /stop-scan (GET) starts the scanning loop, returns 400 if loop was not active

There will be futher configuration and status endpoints added in future
"""

# External Imports
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json, aiofiles

# Internal Imports
from engine import inputQueue, stopEvent
import storage

# Setup FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Icon for static pages
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

# POST edit card
@app.post("/edit-card", status_code=201)
async def edit_card(card: dict):

    # IF LOOP IS ACTIVE RETURN 400 (DETAIL LOOP IS ACTIVE)

    if not all([card.get("cardNumber"), card.get("cardExpiry"), card.get("cardCvc"), card.get("cardPostcode")]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        async with aiofiles.open("card.json", "w") as f:
           await f.write(json.dumps(card))

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to store card") from error

    return {"status": "stored"}

# GET accounts
@app.get("/accounts")
async def get_accounts():
    try:
        async with aiofiles.open("accounts.json") as f:
            contents = await f.read()
            accounts = json.loads(contents)

    except FileNotFoundError:
        accounts = {}

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load accounts") from error

    return accounts

# POST accounts
@app.post("/accounts")
async def add_account(data: dict):

    # IF LOOP IS ACTIVE RETURN 400 (DETAIL LOOP IS ACTIVE)

    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        async with aiofiles.open("accounts.json") as f:
            contents = await f.read()
            accounts = json.loads(contents)

    except FileNotFoundError:
        accounts = {}

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load accounts") from error

    accounts[email] = password

    try:
        async with open("accounts.json", "w") as f:
            json.dump(accounts, f)
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to save accounts")
        
    return {email: password}

# GET event
@app.get("/event")
async def get_event():
    try:
        await storage.loadEvent()
    except FileNotFoundError:
        storage.event = {}
        with open("event.json", "w") as f:
            f.write("{}")
    return {"event": storage.event}

# POST event
@app.post("/event")
async def edit_event(data: dict):
    organiserUrl = data.get("organiserUrl")
    ticketKeyword = data.get("ticketKeyword")
    event_time_raw = data.get("time")
    if not all([organiserUrl, ticketKeyword, event_time_raw]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        event_time = int(event_time_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="time must be a positive integer")
    if event_time < 1:
        raise HTTPException(status_code=400, detail="time must be a positive integer")

    await storage.editEvent(organiserUrl, ticketKeyword, event_time)
    return {"status": "ok"}

# start scan
@app.get("/start-scan")
async def start_scan():
    pass

# stop scan
@app.get("/stop-scan")
async def stop_scan():
    pass