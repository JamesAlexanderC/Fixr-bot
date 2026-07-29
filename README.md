# Fixr-Bot by James Clarke

This is a comprehensive and reliable open solution to reserving a tickets on the https://fixr.co website on multiple accounts

Development paused until further notice due to time constraints, still hoping to produce 1.0 by September

## Usage

This bot will not automate checkout, simply reserve a ticket for a selected event and send a configurable push notifaction upon reservation

Obviously this bot will need to be always-on, a docker image is the intended final ditributable form, which will be easily run and expose a configuration interface

## Architecture

### Engine

This program is driven by `engine.py` which runs the mainloop responsible for creating, running and managing async browser instances. An async Queue is used tosend commands to the engine, which executes them in a safe async manner.

### API

To interact with this queue at runtime, an API is exposed with gunicorn/FastAPI exposing a number of endpoints that can be used to configure the event and accounts storage, start and stop the `scan_loop.py` and also to manually start the `get_ticket` coroutine, however this is developmental and may be removed.

### Browser

Camoufox is used to generate browser instances and inject unique undetectable fingerprints with attched geoip data for future proxy integration. Camoufox is a wrapper around the more mainstream playwright, meaning I can run multiple instances asynchronously. However there is a limit to async in python that is hit very quickly with playwright (around 4-5 browsers before it becomes more or less sequential) to overcome this multiple engines can be run containerised, I also plan to look into the possibility of concurrent browser sessions to make use of threading.

## Development Roadmap

- Add proxy support
- Add push notifications (probably supporting easiest platforms first - nfty, telegram, discord then SMS later down the line)
- Change to concurrent sessions (if possible)
- containerise for beta release 0.1
    - add robust logging
    - decide on virtual display
    - create dockerfile and test
    - implement healthchecks, autohealing and easy restarting
    - release

## Release 1.0 planned for 09/2026