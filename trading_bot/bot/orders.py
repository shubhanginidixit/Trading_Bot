"""
Order placement logic.

This layer translates validated, Pythonic order parameters into the exact
Binance REST payload and delegates the actual HTTP call to
:class:`~bot.client.BinanceFuturesClient`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger

logger = setup_logger("orders")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _fmt(value: Decimal) -> str:
    """
    Convert a :class:`~decimal.Decimal` to a plain string without trailing
    zeros (e.g. ``Decimal('0.001000')`` → ``'0.001'``).
    Binance rejects values like ``'0.001000'`` on some pairs.
    """
    return format(value.normalize(), "f")


def _build_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal],
    stop_price: Optional[Decimal],
) -> str:
    """Return a one-line human-readable summary of the order request."""
    parts = [f"{side} {_fmt(quantity)} {symbol} @ {order_type}"]
    if price is not None:
        parts.append(f"price={_fmt(price)}")
    if stop_price is not None:
        parts.append(f"stop={_fmt(stop_price)}")
    return " | ".join(parts)


# ── Public order functions ────────────────────────────────────────────────────


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> dict:
    """
    Submit a MARKET order.

    Args:
        client:   Authenticated :class:`~bot.client.BinanceFuturesClient`.
        symbol:   Trading pair, e.g. ``"BTCUSDT"``.
        side:     ``"BUY"`` or ``"SELL"``.
        quantity: Contract quantity (in base asset units).

    Returns:
        Raw Binance order response dict.
    """
    summary = _build_summary(symbol, side, "MARKET", quantity, None, None)
    logger.info("Submitting MARKET order: %s", summary)
    print(f"\n📋 Order Request: {summary}")

    response = client.place_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=_fmt(quantity),
    )
    logger.info("MARKET order response: %s", response)
    return response


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> dict:
    """
    Submit a LIMIT order.

    Args:
        client:        Authenticated client.
        symbol:        Trading pair.
        side:          ``"BUY"`` or ``"SELL"``.
        quantity:      Contract quantity.
        price:         Limit price.
        time_in_force: ``"GTC"`` (default), ``"IOC"``, or ``"FOK"``.

    Returns:
        Raw Binance order response dict.
    """
    summary = _build_summary(symbol, side, "LIMIT", quantity, price, None)
    logger.info("Submitting LIMIT order: %s", summary)
    print(f"\n📋 Order Request: {summary}")

    response = client.place_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=_fmt(quantity),
        price=_fmt(price),
        timeInForce=time_in_force,
    )
    logger.info("LIMIT order response: %s", response)
    return response


def place_stop_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> dict:
    """
    Submit a STOP_MARKET order (bonus order type).

    A market order is triggered when the mark price crosses *stop_price*.

    Args:
        client:     Authenticated client.
        symbol:     Trading pair.
        side:       ``"BUY"`` or ``"SELL"``.
        quantity:   Contract quantity.
        stop_price: Trigger price.

    Returns:
        Raw Binance order response dict.
    """
    summary = _build_summary(symbol, side, "STOP_MARKET", quantity, None, stop_price)
    logger.info("Submitting STOP_MARKET order: %s", summary)
    print(f"\n📋 Order Request: {summary}")

    response = client.place_order(
        symbol=symbol,
        side=side,
        type="STOP_MARKET",
        quantity=_fmt(quantity),
        stopPrice=_fmt(stop_price),
    )
    logger.info("STOP_MARKET order response: %s", response)
    return response


# ── Response formatter ────────────────────────────────────────────────────────


def format_response(response: dict) -> str:
    """
    Return a clean, multi-line string summarising the key fields of a
    Binance order response.
    """
    lines = [
        "─" * 50,
        "✅ Order Placed Successfully",
        "─" * 50,
        f"  Order ID      : {response.get('orderId', 'N/A')}",
        f"  Client OID    : {response.get('clientOrderId', 'N/A')}",
        f"  Symbol        : {response.get('symbol', 'N/A')}",
        f"  Side          : {response.get('side', 'N/A')}",
        f"  Type          : {response.get('type', 'N/A')}",
        f"  Status        : {response.get('status', 'N/A')}",
        f"  Quantity      : {response.get('origQty', 'N/A')}",
        f"  Executed Qty  : {response.get('executedQty', 'N/A')}",
        f"  Avg Price     : {response.get('avgPrice', 'N/A')}",
        f"  Price         : {response.get('price', 'N/A')}",
        f"  Stop Price    : {response.get('stopPrice', 'N/A')}",
        f"  Time in Force : {response.get('timeInForce', 'N/A')}",
        f"  Update Time   : {response.get('updateTime', 'N/A')}",
        "─" * 50,
    ]
    # Remove lines where value is empty string or '0' for cleaner output
    filtered = []
    for line in lines:
        if ": N/A" in line or ": 0" in line or line.endswith(": "):
            if line.startswith("─") or "Order ID" in line or "Symbol" in line or "Side" in line or "Status" in line:
                filtered.append(line)
            # silently drop truly empty optional fields
        else:
            filtered.append(line)
    return "\n".join(filtered)
