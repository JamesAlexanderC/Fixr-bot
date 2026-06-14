# --------------------------------------------------------------------
# Engine File, defines backend behaviour when different things happen
# --------------------------------------------------------------------

import asyncio
from enum import Enum
from coroutines import *
from camoufox.async_api import AsyncCamoufox

import output

class State(str, Enum):
    IDLE = "idle"
    CREATING_ACCOUNT = "creating account"
    SEARCHING = "searching"
    LOGGING_IN = "logging in"
    RESERVING = "reserving"
    BUYING = "buying"
    COMPLETED = "completed"
    FAILED = "failed"

inputQueue = asyncio.Queue()
outputQueue = asyncio.Queue()
stopEvent = asyncio.Event()

INITIALISED = 0

# --------------------------------------------------------------------
# Helper functions for a lil more decomposition
# --------------------------------------------------------------------
async def initialise(state):
    output.info("Initialisation Requested")
    if INITIALISED == 0:
        state: State = State.IDLE
        output.info("Thread Initialised")
    else:
        output.info("Threed Initialisation Failed (ALready Initialised)")
    return state

async def startHeartbeat(page):
    output.info("Heartbeat Start requested")
    asyncio.create_task(ticketSearch(page, inputQueue)) 


# --------------------------------------------------------------------
# Main Queue handler - basically takes messages from the queue, 
# interprets them and executes them
# --------------------------------------------------------------------

async def queueHandler(state):
    async with AsyncCamoufox(disable_coop=True) as browser:
        while not stopEvent.is_set():
            msg = await inputQueue.get()
            output.info(f"got message: {msg}")

            if msg == "INITIALISE":
                state = await initialise(state)
                page = await createPage(browser)
                
            if msg == "DISPLAY_INFO":
                output.info(f'Thread State: {state}')

            if msg == "SHUTDOWN":
                pass
            
            if msg == "START_HEARTBEAT":
                await startHeartbeat(page)
            
            if msg.split("|")[0] == "TICKETS_FOUND":
                output.info("Getting tickets")
                asyncio.create_task(getTickets(page, msg.split("|")[1], inputQueue))

            

# TESTING
async def ticket_check_loop():
    async with AsyncCamoufox(
            geoip=True,
            i_know_what_im_doing=True,
            disable_coop=True
        ) as browser:
        pass

if __name__ == "__main__":
    asyncio.run(ticket_check_loop(State.IDLE))
