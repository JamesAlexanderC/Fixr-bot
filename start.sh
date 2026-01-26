#!/bin/bash
set -e

# Ensure pip-installed scripts are in PATH
export PATH="$PATH:/root/.local/bin"

# Must set DISPLAY_NUM
if [ -z "$DISPLAY_NUM" ]; then
  echo "ERROR: DISPLAY_NUM not set"
  exit 1
fi

export DISPLAY=:${DISPLAY_NUM}
echo "[+] Using display $DISPLAY"

# Start virtual display
Xvfb $DISPLAY -screen 0 1280x800x24 &
XVFB_PID=$!

# Wait until Xvfb is ready
for i in {1..10}; do
    xdpyinfo -display $DISPLAY >/dev/null 2>&1 && break
    echo "[+] Waiting for Xvfb to start..."
    sleep 1
done

# Start VNC server
x11vnc -display $DISPLAY -forever -nopw -shared &
echo "[+] VNC server started"

# Now run Camoufox fetch — Xvfb is guaranteed ready
echo "[+] Running Camoufox fetch"
python3 -m camoufox fetch

# Run Python script with positional arguments
echo "[+] Running Python script"
exec python3 /app/main.py "$@"





