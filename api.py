"""
# API.py as of 26/07/2026

### This file contains the FastAPI server, and exposes the endpoints defined bolow:
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
from engine import inputQueue, scan_session

# Setup FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Icon for static pages
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

# Interace
@app.get("/dashboard")
async def control_dash():
    return FileResponse("static/dashboard.html")

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
@app.post("/accounts", status_code=201)
async def add_account(data: dict):

    if scan_session != None:
        raise HTTPException(status_code=400, detail="Scan loop in progress")

    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        with open("accounts.json") as f:
            accounts = json.load(f)

    except FileNotFoundError:
        accounts = {}

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load accounts") from error

    accounts[email] = password

    try:
        with open("accounts.json", "w") as f:
            json.dump(accounts, f)
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to save accounts")
        
    return {email: password}

# GET event
@app.get("/event")
async def get_event():

    try:
        with open("event.json", "r") as f:
            event = json.load(f)

    except FileNotFoundError:
        event = {
            "organiser_url": "",
            "ticket_keyword": "",
            "scan_interval": "5"
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load event") from error

    return event

# POST event
@app.post("/event", status_code=201)
async def edit_event(data: dict):

    if not all([data.get("organiser_url"), data.get("ticket_keyword"), data.get("scan_interval")]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        with open("event.json", "w") as f:
            json.dump(data, f)

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load event") from error
    
    return data

# start scan
@app.get("/start-scan")
async def start_scan():
    await inputQueue.put("start-scan-loop")

# stop scan
@app.get("/stop-scan")
async def stop_scan():
    await inputQueue.put("stop-scan-loop")

@app.post("/get-ticket")
async def get_ticket(data: dict):
    await inputQueue.put(f"get-ticket|{data["url"]}")