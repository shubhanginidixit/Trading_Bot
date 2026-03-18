# Binance Futures Testnet – Trading Bot

A clean, well-structured Python CLI tool for placing **MARKET**, **LIMIT**, and **STOP_MARKET** orders on the [Binance USDT-M Futures Testnet](https://testnet.binancefuture.com).

---

## Features

| Feature | Details |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| Sides | `BUY` / `SELL` |
| CLI | `argparse` with `--dry-run`, `--tif`, `--log-dir` flags |
| Validation | Symbol, side, type, quantity, price, stop-price with clear error messages |
| Logging | Per-day log files in `./logs/`; requests, responses, and errors all captured |
| Error handling | Distinguishes API errors, network failures, and validation failures with different exit codes |
| Structure | Separated into `client.py`, `orders.py`, `validators.py`, `logging_config.py`, `cli.py` |

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
├── logs/                  # Auto-created log files
│   └── trading_bot_YYYY-MM-DD.log
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Visit <https://testnet.binancefuture.com>
2. Sign in with your GitHub account
3. Click **API Key** → copy your key and secret

### 2. Install Dependencies

```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### 3. Set Credentials

**Recommended (environment variables):**

```bash
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret
```

**Or pass them as flags** (less secure, appears in shell history):

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## Usage

### General syntax

```
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT|STOP_MARKET \
              --quantity QTY [--price PRICE] [--stop-price STOP] [--tif GTC|IOC|FOK]
```

### Examples

**Market BUY – 0.001 BTC:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Limit SELL – 0.001 BTC at $99,500:**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 99500
```

**Stop-Market SELL – triggers at $95,000 (bonus order type):**
```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 95000
```

**Dry-run (validate only, no order submitted):**
```bash
python cli.py --symbol ETHUSDT --side BUY --type LIMIT --quantity 0.01 --price 3500 --dry-run
```

**Custom log directory:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --log-dir /tmp/bot_logs
```

### Sample output

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
  Order ID      : 4751823901
  Client OID    : web_FzX9kQpTlM2Nv8aH
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Quantity      : 0.001
  Executed Qty  : 0.001
  Avg Price     : 97432.5
──────────────────────────────────────────────────
```

---

## CLI Reference

| Flag | Required | Description |
|---|---|---|
| `--symbol` / `-s` | ✅ | Trading pair (must end in `USDT`, e.g. `BTCUSDT`) |
| `--side` | ✅ | `BUY` or `SELL` |
| `--type` / `-t` | ✅ | `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `--quantity` / `-q` | ✅ | Order quantity in base asset units |
| `--price` / `-p` | LIMIT only | Limit price |
| `--stop-price` | STOP_MARKET only | Stop trigger price |
| `--tif` | Optional | Time in force: `GTC` (default), `IOC`, `FOK` |
| `--api-key` | Optional* | Testnet API key (`$BINANCE_API_KEY`) |
| `--api-secret` | Optional* | Testnet API secret (`$BINANCE_API_SECRET`) |
| `--log-dir` | Optional | Log directory (default: `./logs`) |
| `--dry-run` | Optional | Validate inputs only, do not place order |

*Loaded automatically from environment variables if not passed as flags.

---

## Logging

Log files are written to `./logs/trading_bot_YYYY-MM-DD.log`.

Each file captures:
- `DEBUG` – full request params (signature redacted) and raw response bodies
- `INFO` – order submission and placement confirmations
- `WARNING` – validation failures
- `ERROR` – API errors and network failures

Console output shows `WARNING` and above only (keeping it clean during normal use).

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Missing credentials |
| `2` | Validation error |
| `3` | Binance API error |
| `4` | Network / connection error |
| `5` | Unexpected error |

---

## Assumptions

- Targets the **USDT-M Futures Testnet** only (`https://testnet.binancefuture.com`).
- Symbols must end in `USDT` (e.g. `BTCUSDT`, `ETHUSDT`). Coin-M futures are not supported.
- Position mode is assumed to be **One-Way** (no `positionSide` parameter sent). If your account uses Hedge Mode, add `--position-side LONG|SHORT` (currently not implemented).
- Minimum quantity and price precision are not enforced client-side; Binance returns a clear error if filters are violated.
- Python 3.8 or later is required.

---

## Running Tests (optional)

```bash
# Quick dry-run smoke test – no credentials needed beyond validation
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run \
              --api-key dummy --api-secret dummy
```

---

## Requirements

```
requests>=2.31.0
```

No third-party Binance library is used; all API calls are made directly via `requests` with HMAC-SHA256 signing.
