# Fixr Bot

Fixr Bot is an automation project for monitoring FIXR ticket pages and driving a browser through the ticket purchase flow.
It combines a small FastAPI control surface with an asynchronous browser engine built around Camoufox.

> Status: work in progress. The codebase is functional in parts, but several flows are still experimental and may change.

## What it does

At a high level, the bot is designed to:

- check a FIXR organiser page for ticket availability on a repeating heartbeat
- open a browser session and navigate through the login, reservation, and checkout flow
- expose a local web UI for starting, stopping, and sending commands to the bot
- store sensitive profile and payment details in environment variables rather than hard-coding them into the source

## Project structure

- `main.py` — starts both the engine and the API server
- `engine.py` — queue-driven state handling, browser lifecycle, and main ticket flow orchestration
- `api.py` — FastAPI routes used by the local control UI
- `coroutines.py` — reusable async helpers for searching, reserving, buying, and page management
- `ticketFunctions/` — step-by-step automation actions for each stage of the FIXR flow
- `static/` — lightweight web control panel served by the API
- `output.py` — simple logging helper
- `todos.txt` — working notes and rough planning

## Runtime architecture

The application is built around three layers:

1. **Control API**
   - FastAPI serves a small web page and exposes routes such as `/init`, `/start`, `/shutdown`, and `/custom`.

2. **Engine**
   - `engine.py` listens to messages from an async queue and coordinates browser actions.
   - It keeps the browser session alive, starts the ticket heartbeat, and reacts when tickets are found.

3. **Automation helpers**
   - Modules in `ticketFunctions/` contain the actual browser steps for login, reservation, and payment.
   - `coroutines.py` wraps these helpers into the higher-level search-and-buy flow.

## How the flow works

Typical intended flow:

1. Start the app.
2. Open the local control page.
3. Send an initialise command.
4. Start the heartbeat.
5. The bot repeatedly checks the organiser page.
6. When tickets appear, it moves through login, reservation, and checkout.

## Configuration

The bot expects environment variables for organiser and payment data.
Exact names may still evolve, but the current code references values such as:

- `ORGANISER_URL`
- `TICKET_NUMBER`
- `EMAIL` / `PASSWORD` or account-specific login variables
- `CARD_NUMBER`
- `CARD_EXPIRY`
- `CARD_CVC`
- `CARD_POSTCODE`
- profile fields such as first name, last name, date of birth, and phone number

There is also helper code that can persist values into a local `.env` file.

## Running the project

The app is started from `main.py`.
It launches:

- the async automation engine
- a FastAPI server on port `8000`

The local control page is served from the root route and uses the static files in `static/`.

## Current limitations

This project is still rough around the edges.
Known areas that are likely to change include:

- browser recovery and retry behaviour
- state management in the engine
- the exact message protocol between the API and the queue
- better handling for multiple accounts and purchases
- more reliable checkout timing and iframe detection
- clearer shutdown and cancellation semantics

## Future development goals

Planned next steps:

- [ ] add a proper configuration layer with validation
- [ ] replace ad hoc queue messages with typed commands or events
- [ ] improve the state machine so transitions are explicit and testable
- [ ] add structured logging instead of plain print-based output
- [ ] make browser refresh and retry logic more robust
- [ ] separate the ticket search, reservation, and payment flows into clearer modules
- [ ] add automated tests for the engine and helper flows
- [ ] improve the UI so it shows status, queue activity, and current state
- [ ] support multiple organiser pages and multiple accounts cleanly
- [ ] add safer secret management and reduce reliance on manual `.env` editing
- [ ] Include configurable and rotating proxies

## Scope

The intended scope of this project is automation around FIXR ticket monitoring and purchase flow orchestration.
It is not currently designed as a general-purpose ticketing platform or a polished end-user product.
The focus is on experimentation, recovery logic, and building a reliable internal workflow that can be improved over time.
