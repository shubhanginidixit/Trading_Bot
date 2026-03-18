"""
Validators for all user-supplied order parameters.

Each function raises :class:`ValueError` with a human-readable message on
failure so that the CLI layer can surface the problem cleanly.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

# Common Binance USDT-M futures symbols (non-exhaustive – used for a quick
# sanity check; the API will reject anything truly invalid).
_COMMON_QUOTE = "USDT"


# ── Public validators ────────────────────────────────────────────────────────


def validate_symbol(symbol: str) -> str:
    """
    Normalise *symbol* to upper-case and verify it looks like a valid
    Binance USDT-M futures pair (e.g. ``BTCUSDT``).

    Raises:
        ValueError: If the symbol is empty or does not end with a known
                    quote currency.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol must not be empty.")
    if not symbol.endswith(_COMMON_QUOTE):
        raise ValueError(
            f"Symbol '{symbol}' does not end with '{_COMMON_QUOTE}'. "
            f"This bot targets USDT-M futures only (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """
    Normalise *side* and confirm it is either ``BUY`` or ``SELL``.

    Raises:
        ValueError: If the value is not a supported side.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Normalise *order_type* and verify it is supported.

    Raises:
        ValueError: If the order type is not supported.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """
    Parse *quantity* into a :class:`decimal.Decimal` and verify it is
    strictly positive.

    Raises:
        ValueError: If the value cannot be parsed or is not positive.
    """
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}': not a number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero (got {qty}).")
    return qty


def validate_price(price: Optional[str | float], *, required: bool = False) -> Optional[Decimal]:
    """
    Parse *price* into a :class:`decimal.Decimal` and verify it is
    strictly positive.

    Args:
        price:    The raw price value (may be ``None`` for MARKET orders).
        required: When ``True``, a ``None`` price raises :class:`ValueError`.

    Raises:
        ValueError: If required and price is ``None``, or if the value is
                    not a positive number.
    """
    if price is None or str(price).strip() == "":
        if required:
            raise ValueError("Price is required for this order type.")
        return None
    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}': not a number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero (got {p}).")
    return p


def validate_stop_price(
    stop_price: Optional[str | float], *, required: bool = False
) -> Optional[Decimal]:
    """
    Parse and validate a stop-trigger price.

    Delegates to :func:`validate_price` with a clearer error label.
    """
    try:
        return validate_price(stop_price, required=required)
    except ValueError as exc:
        raise ValueError(str(exc).replace("Price", "Stop price")) from exc


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
) -> dict:
    """
    Run all validators and return a clean, normalised parameter dictionary.

    Raises:
        ValueError: On the first validation error encountered.
    """
    order_type = validate_order_type(order_type)

    price_required = order_type == "LIMIT"
    stop_price_required = order_type == "STOP_MARKET"

    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": order_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, required=price_required),
        "stop_price": validate_stop_price(stop_price, required=stop_price_required),
    }
