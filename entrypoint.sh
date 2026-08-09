#!/bin/sh
set -e

# Camoufox launches a real (non-headless) browser by default, matching how
# this app is exercised in development on a desktop with a display. There is
# no physical display inside the container, so provide a virtual one.
#
# xvfb-run's own readiness handshake relies on delivering SIGUSR1 to its
# parent, which does not work reliably when that parent is PID 1 (this
# script, via `exec`), so Xvfb is started and polled for directly instead.
DISPLAY_NUM=99
export DISPLAY=":${DISPLAY_NUM}"

Xvfb "$DISPLAY" -screen 0 1280x1024x24 -nolisten tcp &
XVFB_PID=$!

tries=50
while [ ! -e "/tmp/.X11-unix/X${DISPLAY_NUM}" ]; do
    tries=$((tries - 1))
    if [ "$tries" -le 0 ]; then
        echo "entrypoint: Xvfb did not start in time" >&2
        exit 1
    fi
    if ! kill -0 "$XVFB_PID" 2>/dev/null; then
        echo "entrypoint: Xvfb exited unexpectedly" >&2
        exit 1
    fi
    sleep 0.2
done

exec "$@"
