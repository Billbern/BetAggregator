"""Sequential slip-code generation.

Betting bookmakers issue share codes with an alphabet of digits 1-9 and
uppercase A-Z, omitting ``0``, ``I`` and ``O`` (to avoid 0/O and 1/I
confusion). Codes advance like an odometer over that alphabet:

    AZ  ->  B1
    ZZ  ->  111
    A1  ->  A2

The original implementation used a hand-rolled circular linked list and
crashed with an IndexError on wrap-around inputs such as ``Z`` or ``ZZ``.
This module replaces it with an explicit, well-tested increment.
"""

from __future__ import annotations

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
FIRST = ALPHABET[0]
LAST = ALPHABET[-1]


class SlipGeneratorError(ValueError):
    """Raised when a code contains characters outside the slip alphabet."""


def _validate(code: str) -> None:
    invalid = set(code) - set(ALPHABET)
    if invalid:
        raise SlipGeneratorError(f"code {code!r} contains invalid characters {sorted(invalid)}")


def next_code(code: str) -> str:
    """Return the code immediately following ``code``."""
    if not code:
        return FIRST
    _validate(code)
    chars = list(code)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] == LAST:
            chars[i] = FIRST
            i -= 1
            continue
        chars[i] = ALPHABET[ALPHABET.index(chars[i]) + 1]
        return "".join(chars)
    # Every digit wrapped: grow the code by one digit (e.g. ZZ -> 111).
    return FIRST + "".join(chars)


def generate_slips(start: str, n: int) -> list[str]:
    """Return ``n`` consecutive codes beginning at ``start``."""
    if n <= 0:
        return []
    codes = [start]
    for _ in range(n - 1):
        codes.append(next_code(codes[-1]))
    return codes


class SlipGenerator:
    """Backwards-compatible wrapper around :func:`generate_slips`."""

    def __init__(self) -> None:
        pass  # kept for API stability; the class is now stateless

    def generateSlip(self, slip: str, n: int) -> list[str]:
        return generate_slips(slip, n)
