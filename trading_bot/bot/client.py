"""
Low-level Binance Futures Testnet REST client.

Handles:
  * HMAC-SHA256 request signing
  * Timestamping
  * HTTP error → exception mapping
  * Structured logging of every request and response
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds

# ── Custom exceptions ────────────────────────────────────────────────────────


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx HTTP status or an error payload."""

    def __init__(self, status_code: int, code: int, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[HTTP {status_code}] Binance error {code}: {message}")


class BinanceNetworkError(Exception):
    """Raised on connection / timeout failures."""


# ── Client ───────────────────────────────────────────────────────────────────


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance USDT-M Futures REST API (testnet).

    Parameters
    ----------
    api_key:    Your testnet API key.
    api_secret: Your testnet API secret.
    base_url:   Override the default testnet URL (useful for tests).
    timeout:    HTTP request timeout in seconds.
    log_dir:    Directory where log files are written.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        log_dir: str = "logs",
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("Both api_key and api_secret must be provided.")

        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        self._logger = setup_logger("binance_client", log_dir=log_dir)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _sign(self, params: dict) -> dict:
        """Append ``timestamp`` and HMAC ``signature`` to *params*."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        signed: bool = True,
    ) -> Any:
        """
        Execute an HTTP request, log it, and return the parsed JSON body.

        Raises:
            BinanceAPIError:    On non-2xx responses or Binance error payloads.
            BinanceNetworkError: On connection / timeout failures.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self._base_url}{endpoint}"

        # Redact the signature in logs to avoid leaking credentials
        safe_params = {k: ("***" if k == "signature" else v) for k, v in params.items()}
        self._logger.debug("REQUEST  %s %s  params=%s", method, endpoint, safe_params)

        try:
            response = self._session.request(
                method,
                url,
                params=params if method == "GET" else None,
                data=params if method != "GET" else None,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout as exc:
            self._logger.error("TIMEOUT  %s %s", method, endpoint)
            raise BinanceNetworkError(f"Request timed out after {self._timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            self._logger.error("CONN_ERR %s %s  %s", method, endpoint, exc)
            raise BinanceNetworkError(f"Connection error: {exc}") from exc

        self._logger.debug(
            "RESPONSE %s %s  status=%s body=%s",
            method,
            endpoint,
            response.status_code,
            response.text[:500],  # truncate huge bodies
        )

        try:
            data = response.json()
        except ValueError:
            data = {"msg": response.text, "code": -1}

        if not response.ok:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            self._logger.error(
                "API_ERROR %s %s  http=%s binance_code=%s msg=%s",
                method,
                endpoint,
                response.status_code,
                code,
                msg,
            )
            raise BinanceAPIError(response.status_code, code, msg)

        return data

    # ── Public API methods ───────────────────────────────────────────────────

    def get_exchange_info(self) -> dict:
        """Return exchange metadata (symbols, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo", signed=False)

    def get_account(self) -> dict:
        """Return the authenticated account balance snapshot."""
        return self._request("GET", "/fapi/v2/account")

    def place_order(self, **kwargs) -> dict:
        """
        Place a new order.

        Keyword arguments are passed verbatim to the ``POST /fapi/v1/order``
        endpoint after signing.  The caller (``orders.py``) is responsible
        for providing correctly named Binance parameters.

        Returns:
            Parsed JSON response from Binance.
        """
        self._logger.info("PLACE_ORDER  params=%s", kwargs)
        result = self._request("POST", "/fapi/v1/order", params=kwargs)
        self._logger.info("ORDER_PLACED orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Fetch the current state of an existing order."""
        return self._request("GET", "/fapi/v1/order", params={"symbol": symbol, "orderId": order_id})

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by ID."""
        return self._request(
            "DELETE", "/fapi/v1/order", params={"symbol": symbol, "orderId": order_id}
        )
