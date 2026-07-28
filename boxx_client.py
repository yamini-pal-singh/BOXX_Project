"""
BOXX Chatbot Test API Client
=============================
Thin, well-typed wrapper around the BOXX test API.

Usage:
    from boxx_client import BOXXClient

    client = BOXXClient()
    session_id = client.create_session(language="en")
    resp = client.send_message(session_id, "I got a phishing SMS")
    print(resp["reply"])
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("boxx_client")

# Defaults — override with env vars BOXX_BASE_URL and BOXX_API_KEY
DEFAULT_BASE_URL = "https://boxxv2.shunyalabs.ai"
DEFAULT_API_KEY = "boxx-qa-e1ae28770694f29b7ebc2cab3743438a"

REQUEST_TIMEOUT = 45  # seconds — turns hitting LLM/graph can take 2–9s


class BOXXError(Exception):
    """Custom exception raised on non-2xx API responses or connection failures."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class BOXXClient:
    """Synchronous HTTP client for the BOXX Chatbot Test API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT,
    ):
        self.base_url = (base_url or os.environ.get("BOXX_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.environ.get("BOXX_API_KEY", DEFAULT_API_KEY)
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        })
        logger.info("BOXXClient initialised — base_url=%s", self.base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self._session.request(method, url, **kwargs)
        except requests.exceptions.Timeout:
            raise BOXXError(
                f"Request timed out after {self.timeout}s: {method} {path}"
            )
        except requests.exceptions.ConnectionError as exc:
            raise BOXXError(
                f"Connection failed — is the API reachable at {self.base_url}?\n{exc}"
            )

        # Log 4xx/5xx bodies for debugging
        if not resp.ok:
            body_preview = resp.text[:500] if resp.text else "(empty body)"
            logger.warning("API error %s %s -> %d: %s", method, path, resp.status_code, body_preview)
            raise BOXXError(
                f"API returned {resp.status_code} for {method} {path}",
                status_code=resp.status_code,
                response_body=resp.text[:2000],
            )

        data = resp.json()
        # The API wraps responses in {"status": "success", "data": {...}}
        # or {"status": "error", "message": "..."}
        if isinstance(data, dict) and data.get("status") == "error":
            msg = data.get("message", "Unknown API error")
            logger.warning("API business error %s %s: %s", method, path, msg)
            raise BOXXError(
                f"API error: {msg}",
                status_code=resp.status_code,
                response_body=resp.text[:2000],
            )
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """GET /api/test/health — returns True if the API is reachable."""
        try:
            resp = self._request("GET", "/api/test/health")
            data = resp.get("data", {})
            logger.info(
                "Health check OK — org=%s time=%s",
                data.get("organization_id"),
                data.get("time"),
            )
            return True
        except BOXXError as exc:
            logger.error("Health check FAILED: %s", exc)
            return False

    def create_session(
        self,
        language: str = "en",
        profile_name: str = "QA Bot",
        phone: str = "simulation",
        metadata: Optional[dict] = None,
    ) -> str:
        """POST /api/test/session — create isolated conversation, return session_id."""
        body = {
            "language": language,
            "profile_name": profile_name,
            "phone": phone,
            "metadata": metadata or {},
        }
        resp = self._request("POST", "/api/test/session", json=body)
        session_id = resp.get("data", {}).get("session_id")
        if not session_id:
            raise BOXXError("No session_id in create_session response", response_body=str(resp))
        logger.debug("Created session %s (lang=%s)", session_id, language)
        return session_id

    def send_message(
        self,
        session_id: str,
        message: Optional[str] = None,
        button_id: Optional[str] = None,
        button_title: Optional[str] = None,
    ) -> dict:
        """POST /api/test/session/{id}/message — send user turn, return bot reply dict.

        At least one of *message* or *button_id* must be provided.
        """
        if not message and not button_id:
            raise ValueError("Either 'message' or 'button_id' is required.")

        body: dict = {}
        if message is not None:
            body["message"] = message
        if button_id is not None:
            body["button_id"] = button_id
        if button_title is not None:
            body["button_title"] = button_title

        resp = self._request(
            "POST", f"/api/test/session/{session_id}/message", json=body
        )
        data = resp.get("data", {})
        reply_count = data.get("reply_count", 0)
        logger.debug(
            "Message sent to %s — reply_count=%d latency_ms=%s",
            session_id, reply_count, data.get("latency_ms"),
        )
        return data

    def agree_to_disclaimer(self, session_id: str) -> dict:
        """Convenience: tap the 'I Agree' button to pass the disclaimer."""
        return self.send_message(
            session_id,
            button_id="agree_disclaimer",
            button_title="I Agree",
        )

    def get_transcript(self, session_id: str) -> list:
        """GET /api/test/session/{id} — return full transcript list."""
        resp = self._request("GET", f"/api/test/session/{session_id}")
        return resp.get("data", [])

    def quick(self, message: str, language: str = "en") -> dict:
        """POST /api/test/quick — one-shot convenience, returns data with reply + session_id."""
        body = {"message": message, "language": language}
        resp = self._request("POST", "/api/test/quick", json=body)
        return resp.get("data", {})

    def get_session(self, session_id: str) -> dict:
        """GET /api/test/session/{id} — full session data (transcript + metadata)."""
        resp = self._request("GET", f"/api/test/session/{session_id}")
        return resp.get("data", {})
