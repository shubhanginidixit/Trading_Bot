#!/usr/bin/env python3
"""
cli.py – Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market buy
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit sell
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500

# Stop-Market sell (bonus order type)
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000

# Use environment variables for credentials (recommended):
#   export BINANCE_API_KEY=your_key
#   export BINANCE_API_SECRET=your_secret
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

from bot.client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError
from bot.logging_config import setup_logger
from bot.orders import (
    format_response,
    place_limit_order,
    place_market_order,
    place_stop_market_order,
)
from bot.validators import validate_order_params

logger = setup_logger("cli")


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            ╔══════════════════════════════════════════════╗
            ║   Binance Futures Testnet – Trading Bot CLI  ║
            ╚══════════════════════════════════════════════╝

            Place MARKET, LIMIT, or STOP_MARKET orders on the
            Binance USDT-M Futures Testnet.

            Credentials are read from the environment variables:
              BINANCE_API_KEY    – your testnet API key
              BINANCE_API_SECRET – your testnet API secret

            Alternatively, use --api-key / --api-secret flags.
            """
        ),
    )

    # ── Credentials ──────────────────────────────────────────────────────────
    creds = parser.add_argument_group("credentials (env vars preferred)")
    creds.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY", ""),
        metavar="KEY",
        help="Testnet API key (default: $BINANCE_API_KEY)",
    )
    creds.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET", ""),
        metavar="SECRET",
        help="Testnet API secret (default: $BINANCE_API_SECRET)",
    )

    # ── Order parameters ──────────────────────────────────────────────────────
    order = parser.add_argument_group("order parameters")
    order.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT",
    )
    order.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    order.add_argument(
        "--type", "-t",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        metavar="TYPE",
        help="Order type: MARKET | LIMIT | STOP_MARKET",
    )
    order.add_argument(
        "--quantity", "-q",
        required=True,
        metavar="QTY",
        help="Order quantity in base asset units (e.g. 0.001 BTC)",
    )
    order.add_argument(
        "--price", "-p",
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT orders)",
    )
    order.add_argument(
        "--stop-price",
        default=None,
        metavar="STOP",
        help="Stop trigger price (required for STOP_MARKET orders)",
    )
    order.add_argument(
        "--tif",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        metavar="TIF",
        help="Time in force for LIMIT orders: GTC | IOC | FOK (default: GTC)",
    )

    # ── Misc ──────────────────────────────────────────────────────────────────
    misc = parser.add_argument_group("misc")
    misc.add_argument(
        "--log-dir",
        default="logs",
        metavar="DIR",
        help="Directory for log files (default: ./logs)",
    )
    misc.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the order summary without submitting",
    )

    return parser


# ── Validation helper ─────────────────────────────────────────────────────────


def validate_and_print(args: argparse.Namespace) -> dict:
    """
    Run validators and print a pre-flight summary.

    Returns:
        Normalised parameter dict from :func:`~bot.validators.validate_order_params`.

    Raises:
        SystemExit: On validation failure (prints an error and exits with code 2).
    """
    try:
        params = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        print(f"\n❌ Validation error: {exc}\n", file=sys.stderr)
        logger.warning("Validation failed: %s", exc)
        sys.exit(2)

    print(
        f"\n{'─'*50}\n"
        f"  Symbol     : {params['symbol']}\n"
        f"  Side       : {params['side']}\n"
        f"  Type       : {params['order_type']}\n"
        f"  Quantity   : {params['quantity']}\n"
        f"  Price      : {params['price'] or '—'}\n"
        f"  Stop Price : {params['stop_price'] or '—'}\n"
        f"  Time/Force : {args.tif}\n"
        f"{'─'*50}"
    )
    return params


# ── Order dispatch ────────────────────────────────────────────────────────────


def dispatch_order(
    client: BinanceFuturesClient,
    params: dict,
    tif: str,
) -> dict:
    """
    Route the validated *params* to the appropriate order function.

    Returns:
        Raw Binance response dict.
    """
    order_type = params["order_type"]

    if order_type == "MARKET":
        return place_market_order(
            client,
            symbol=params["symbol"],
            side=params["side"],
            quantity=params["quantity"],
        )
    elif order_type == "LIMIT":
        return place_limit_order(
            client,
            symbol=params["symbol"],
            side=params["side"],
            quantity=params["quantity"],
            price=params["price"],
            time_in_force=tif,
        )
    elif order_type == "STOP_MARKET":
        return place_stop_market_order(
            client,
            symbol=params["symbol"],
            side=params["side"],
            quantity=params["quantity"],
            stop_price=params["stop_price"],
        )
    else:
        raise ValueError(f"Unsupported order type: {order_type}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Credential check ──────────────────────────────────────────────────────
    if not args.api_key or not args.api_secret:
        print(
            "\n❌ API credentials not found.\n"
            "   Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "   or pass --api-key / --api-secret flags.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Validate inputs ───────────────────────────────────────────────────────
    params = validate_and_print(args)

    if args.dry_run:
        print("\n⚠️  Dry-run mode enabled – order NOT submitted.\n")
        logger.info("Dry-run: %s", params)
        sys.exit(0)

    # ── Build client ──────────────────────────────────────────────────────────
    try:
        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
            log_dir=args.log_dir,
        )
    except ValueError as exc:
        print(f"\n❌ Client initialisation error: {exc}\n", file=sys.stderr)
        sys.exit(1)

    # ── Place order ───────────────────────────────────────────────────────────
    try:
        response = dispatch_order(client, params, tif=args.tif)
    except BinanceAPIError as exc:
        print(f"\n❌ Binance API error: {exc}\n", file=sys.stderr)
        logger.error("Order failed (API): %s", exc)
        sys.exit(3)
    except BinanceNetworkError as exc:
        print(f"\n❌ Network error: {exc}\n", file=sys.stderr)
        logger.error("Order failed (network): %s", exc)
        sys.exit(4)
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Unexpected error: {exc}\n", file=sys.stderr)
        logger.exception("Unexpected error during order placement")
        sys.exit(5)

    # ── Print result ──────────────────────────────────────────────────────────
    print(format_response(response))


if __name__ == "__main__":
    main()
