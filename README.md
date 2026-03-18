# Binance Futures Testnet – Trading Bot

A clean, well-structured Python CLI tool for placing **MARKET**, **LIMIT**, and **STOP_MARKET** orders on the Binance USDT-M Futures Testnet.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # HMAC-signed Binance REST client
│   ├── orders.py          # Order placement + response formatting
│   ├── validators.py      # Input validation
│   └── logging_config.py  # File + console logger
├── cli.py                 # CLI entry point (argparse)
├── mock_server.py         # Local Binance API mock for testing
├── logs/                  # Generated log files
├── requirements.txt
└── README.md
```

---

## Features

- Place **MARKET**, **LIMIT**, and **STOP_MARKET** orders
- Supports both **BUY** and **SELL** sides
- Full **CLI** with argparse — symbol, side, type, quantity, price, stop-price
- **Dry-run mode** — validate inputs without placing an order
- **Structured logging** — per-day log files, requests/responses/errors all captured, API signature redacted
- **Layered error handling** — validation errors, API errors, network failures all handled separately
- **Mock server** — local Flask server replicating the Binance API for testing without credentials

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set credentials

```bash
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret
```

---

## How to Run

### Against real Binance Futures Testnet

```bash
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99000

# Stop-Market SELL (bonus order type)
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000

# Dry-run (validate only, no order placed)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run
```

### Against local mock server (no credentials needed)

```bash
# Terminal 1 — start mock server
python mock_server.py

# Terminal 2 — run the bot
export BINANCE_API_KEY=mock_key
export BINANCE_API_SECRET=mock_secret
export BINANCE_BASE_URL=http://127.0.0.1:8000

python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99000
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000
```

---

## Sample Output

```
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
  Price      : —
  Stop Price : —
  Time/Force : GTC
──────────────────────────────────────────────────

📋 Order Request: BUY 0.001 BTCUSDT @ MARKET

──────────────────────────────────────────────────
✅ Order Placed Successfully
──────────────────────────────────────────────────
  Order ID      : 4201473756
  Client OID    : mock_1773855238295
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Avg Price     : 97425.79
  Time in Force : GTC
  Update Time   : 1773855238295
──────────────────────────────────────────────────
```

---

## CLI Reference

| Flag | Required | Description |
|---|---|---|
| `--symbol` / `-s` | Yes | Trading pair, e.g. `BTCUSDT` |
| `--side` | Yes | `BUY` or `SELL` |
| `--type` / `-t` | Yes | `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `--quantity` / `-q` | Yes | Order quantity in base asset units |
| `--price` / `-p` | LIMIT only | Limit price |
| `--stop-price` | STOP_MARKET only | Stop trigger price |
| `--tif` | Optional | `GTC` (default), `IOC`, `FOK` |
| `--api-key` | Optional | Testnet API key (default: `$BINANCE_API_KEY`) |
| `--api-secret` | Optional | Testnet API secret (default: `$BINANCE_API_SECRET`) |
| `--log-dir` | Optional | Log directory (default: `./logs`) |
| `--dry-run` | Optional | Validate inputs only, do not place order |

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Missing credentials |
| `2` | Validation error |
| `3` | Binance API error |
| `4` | Network error |
| `5` | Unexpected error |

---

## Logging

Log files are written to `./logs/trading_bot_YYYY-MM-DD.log`.

- `DEBUG` — full request params (signature redacted) and raw response bodies
- `INFO` — order submission and placement confirmations
- `WARNING` — validation failures
- `ERROR` — API errors and network failures

Console shows `WARNING` and above only.

---

## Note on Log Files

The Binance Futures Testnet (`testnet.binancefuture.com`) currently requires
KYC/identity verification to generate API credentials, which prevented direct
testnet access during development.

To work around this professionally, a local mock server (`mock_server.py`) was
built that replicates the exact Binance Futures API endpoints and response
format. All log files in `logs/` were generated from **real HTTP calls** made
by the bot against this mock server — same code path, same logging, same
error handling as production.

The bot requires **zero code changes** to work against the real testnet:

```bash
export BINANCE_API_KEY=your_real_testnet_key
export BINANCE_API_SECRET=your_real_testnet_secret
# BINANCE_BASE_URL defaults to https://testnet.binancefuture.com
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Assumptions

- Targets **USDT-M Futures** only — symbols must end in `USDT` (e.g. `BTCUSDT`)
- Position mode is assumed to be **One-Way** (no `positionSide` parameter)
- Minimum quantity/price precision is not enforced client-side — Binance returns clear errors if filters are violated
- Python 3.8 or later required
- No third-party Binance SDK used — all API calls use raw `requests` with HMAC-SHA256 signing

---

## Requirements

```
requests>=2.31.0
flask>=3.0.0
```
##Contributor
*Shubhangini Dixit
