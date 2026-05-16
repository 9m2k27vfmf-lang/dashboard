"""
WHOOP OAuth helper with token caching.
Run this once to authenticate — the token is saved locally so you
don't need to log in via the browser again.
"""

import os
import json
import secrets
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import requests

CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET")

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "read:cycles read:recovery read:sleep read:workout read:body_measurement"
TOKEN_FILE = Path(__file__).parent / ".whoop_token.json"


def _save_token(token_data: dict):
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    print(f"Token saved to {TOKEN_FILE}")


def _load_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def _refresh_token(refresh_token: str) -> dict | None:
    """Try to refresh an expired access token."""
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    response = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    if response.status_code == 200:
        data = response.json()
        _save_token(data)
        return data
    return None


def get_access_token() -> str:
    """Return a valid access token, refreshing or re-authenticating as needed."""
    cached = _load_token()

    # Try cached token first
    if cached:
        # Try to refresh if we have a refresh token
        if "refresh_token" in cached:
            refreshed = _refresh_token(cached["refresh_token"])
            if refreshed:
                return refreshed["access_token"]
        # Fall back to cached access token (may still be valid)
        if "access_token" in cached:
            return cached["access_token"]

    # Full browser-based OAuth flow
    if not CLIENT_ID or not CLIENT_SECRET:
        raise EnvironmentError(
            "Set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET environment variables."
        )

    _auth_code = None
    _done = False

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal _auth_code, _done
            if self.path.startswith("/callback"):
                params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                _auth_code = params.get("code", [None])[0]
                _done = True
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>WHOOP verbonden! Je kunt dit venster sluiten.</h2>")
            else:
                self.send_response(204)
                self.end_headers()

        def log_message(self, *args):
            pass

    state = secrets.token_urlsafe(16)
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    })

    print("Opening WHOOP login in your browser...")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    while not _done:
        server.handle_request()
    server.server_close()

    if not _auth_code:
        raise RuntimeError("No authorization code received.")

    response = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": _auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    })
    response.raise_for_status()
    data = response.json()
    _save_token(data)
    return data["access_token"]
