#!/usr/bin/env bash
# Dashboard launcher: refresh data, start local server, open in browser.
# Usage: ./start.sh

set -e
cd "$(dirname "$0")"

PORT=8765
URL="http://localhost:${PORT}/index.html"

# Load WHOOP credentials from ~/.zprofile if not already set
if [ -z "$WHOOP_CLIENT_ID" ] && [ -f "$HOME/.zprofile" ]; then
  source "$HOME/.zprofile"
fi

# Make sure venv exists
if [ ! -d ".venv" ]; then
  echo "Creating .venv..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet requests
fi

# Refresh data
echo "Refreshing data..."
.venv/bin/python fetch_data.py || echo "  (fetch failed — using last data.json)"

# Kill any old server on this port
lsof -ti :${PORT} | xargs kill -9 2>/dev/null || true

# Start server in the background
echo "Starting server on http://localhost:${PORT}/"
.venv/bin/python -m http.server ${PORT} > /tmp/dashboard_server.log 2>&1 &
SERVER_PID=$!
echo "  PID: $SERVER_PID  (kill with: kill $SERVER_PID)"

# Give server a moment to start, then open the browser
sleep 0.5
open "$URL"

echo ""
echo "Dashboard running at: $URL"
echo "Server log: /tmp/dashboard_server.log"
