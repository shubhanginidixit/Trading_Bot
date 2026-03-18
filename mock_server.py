#!/usr/bin/env python3
"""
mock_server.py — Local mock of the Binance USDT-M Futures REST API.

Mimics the exact endpoints and response format used by the trading bot
so you can generate real log files without needing a Binance account.

Usage:
    # Terminal 1 — start the mock server
    python mock_server.py

    # Terminal 2 — run the bot against it
    export BINANCE_API_KEY=api_key

    export BINANCE_API_SECRET=mock_secret
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99000
    python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000
"""

import random
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# ── Simulated market prices ──────────────────────────────────────────────────
MOCK_PRICES = {
    "BTCUSDT":  97432.50,
    "ETHUSDT":   3541.20,
    "BNBUSDT":    612.80,
    "SOLUSDT":    185.40,
    "XRPUSDT":      0.62,
}

def _get_price(symbol: str) -> float:
    base = MOCK_PRICES.get(symbol, 100.0)
    # Add small random fluctuation to make it realistic
    return round(base * random.uniform(0.9995, 1.0005), 2)

def _order_id() -> int:
    return random.randint(4_000_000_000, 5_000_000_000)

def _client_order_id() -> str:
    return f"mock_{int(time.time() * 1000)}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.route("/fapi/v1/order", methods=["POST"])
def place_order():
    """Simulate POST /fapi/v1/order"""
    symbol     = request.form.get("symbol", "BTCUSDT").upper()
    side       = request.form.get("side", "BUY").upper()
    order_type = request.form.get("type", "MARKET").upper()
    qty        = request.form.get("quantity", "0.001")
    price      = request.form.get("price", "0")
    stop_price = request.form.get("stopPrice", "0")
    tif        = request.form.get("timeInForce", "GTC")

    now = int(time.time() * 1000)
    avg_price = str(_get_price(symbol)) if order_type == "MARKET" else "0.00000"
    executed  = qty if order_type == "MARKET" else "0"
    status    = "FILLED" if order_type == "MARKET" else "NEW"

    response = {
        "orderId":        _order_id(),
        "clientOrderId":  _client_order_id(),
        "symbol":         symbol,
        "side":           side,
        "type":           order_type,
        "status":         status,
        "origQty":        qty,
        "executedQty":    executed,
        "cumQty":         executed,
        "cumQuote":       str(round(float(executed) * float(avg_price or 0), 4)),
        "avgPrice":       avg_price,
        "price":          price,
        "stopPrice":      stop_price,
        "timeInForce":    tif,
        "reduceOnly":     False,
        "closePosition":  False,
        "positionSide":   "BOTH",
        "workingType":    "CONTRACT_PRICE",
        "origType":       order_type,
        "updateTime":     now,
    }
    return jsonify(response), 200


@app.route("/fapi/v1/order", methods=["GET"])
def get_order():
    """Simulate GET /fapi/v1/order"""
    symbol   = request.args.get("symbol", "BTCUSDT")
    order_id = request.args.get("orderId", _order_id())
    return jsonify({
        "orderId":     order_id,
        "symbol":      symbol,
        "status":      "NEW",
        "origQty":     "0.001",
        "executedQty": "0",
        "type":        "LIMIT",
        "side":        "BUY",
        "updateTime":  int(time.time() * 1000),
    }), 200


@app.route("/fapi/v1/order", methods=["DELETE"])
def cancel_order():
    """Simulate DELETE /fapi/v1/order"""
    symbol   = request.args.get("symbol", "BTCUSDT")
    order_id = request.args.get("orderId", _order_id())
    return jsonify({
        "orderId": order_id,
        "symbol":  symbol,
        "status":  "CANCELED",
        "updateTime": int(time.time() * 1000),
    }), 200


@app.route("/fapi/v1/exchangeInfo", methods=["GET"])
def exchange_info():
    """Simulate GET /fapi/v1/exchangeInfo"""
    return jsonify({
        "timezone":   "UTC",
        "serverTime": int(time.time() * 1000),
        "symbols": [
            {"symbol": s, "status": "TRADING", "baseAsset": s.replace("USDT", ""), "quoteAsset": "USDT"}
            for s in MOCK_PRICES
        ],
    }), 200


@app.route("/fapi/v2/account", methods=["GET"])
def account():
    """Simulate GET /fapi/v2/account"""
    return jsonify({
        "totalWalletBalance":     "10000.00",
        "totalUnrealizedProfit":  "0.00",
        "totalMarginBalance":     "10000.00",
        "availableBalance":       "10000.00",
        "assets": [{"asset": "USDT", "walletBalance": "10000.00", "availableBalance": "10000.00"}],
    }), 200


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Binance Futures Mock Server — running on port 8000")
    print("="*55)
    print("\n  Endpoints ready:")
    print("    POST   /fapi/v1/order  — place order")
    print("    GET    /fapi/v1/order  — get order")
    print("    DELETE /fapi/v1/order  — cancel order")
    print("    GET    /fapi/v1/exchangeInfo")
    print("    GET    /fapi/v2/account")
    print("\n  In a NEW terminal, run the bot like this:")
    print("    export BINANCE_API_KEY=mock_key")
    print("    export BINANCE_API_SECRET=mock_secret")
    print("    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001")
    print("    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99000")
    print("\n  Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=8000, debug=False)
