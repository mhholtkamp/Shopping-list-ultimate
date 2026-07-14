"""Barcode normalization and validation."""

from __future__ import annotations

from dataclasses import dataclass


class InvalidBarcode(ValueError):
    """Raised when a barcode is malformed."""


@dataclass(frozen=True, slots=True)
class Barcode:
    """A normalized retail barcode."""

    value: str
    format: str


def _valid_mod10(value: str) -> bool:
    digits = [int(char) for char in value]
    total = sum(digit * (3 if (len(digits) - index) % 2 == 0 else 1) for index, digit in enumerate(digits[:-1]))
    return (10 - total % 10) % 10 == digits[-1]


def expand_upce(value: str) -> str:
    """Expand a UPC-E code (number systems 0/1) to UPC-A."""
    if len(value) == 8:
        number_system, body, check = value[0], value[1:7], value[7]
    elif len(value) == 7:
        number_system, body, check = "0", value[:6], value[6]
    else:
        raise InvalidBarcode("UPC-E must contain 7 or 8 digits")
    if number_system not in {"0", "1"}:
        raise InvalidBarcode("Unsupported UPC-E number system")
    last = body[-1]
    if last in "012":
        manufacturer = body[:2] + last + "00"
        product = "00" + body[2:5]
    elif last == "3":
        manufacturer = body[:3] + "00"
        product = "000" + body[3:5]
    elif last == "4":
        manufacturer = body[:4] + "0"
        product = "0000" + body[4]
    else:
        manufacturer = body[:5]
        product = "0000" + last
    return number_system + manufacturer + product + check


def validate_barcode(raw: str | int) -> Barcode:
    """Normalize and validate EAN-8, UPC-E, UPC-A, or EAN-13."""
    value = str(raw).strip().replace(" ", "")
    if not value.isdigit():
        raise InvalidBarcode("Barcode may only contain digits")
    formats = {8: "EAN-8", 12: "UPC-A", 13: "EAN-13"}
    if len(value) == 8 and not _valid_mod10(value):
        try:
            expanded = expand_upce(value)
        except InvalidBarcode as err:
            raise InvalidBarcode("Invalid barcode check digit") from err
        if not _valid_mod10(expanded):
            raise InvalidBarcode("Invalid barcode check digit")
        return Barcode(value, "UPC-E")
    if len(value) not in formats or not _valid_mod10(value):
        raise InvalidBarcode("Invalid barcode check digit or length")
    return Barcode(value, formats[len(value)])
