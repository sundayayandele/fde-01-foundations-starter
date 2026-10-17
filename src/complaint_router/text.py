"""Text normalisation and tokenisation shared by every model.

One function, used at training and at serving time, so the two never drift apart.
"""

from __future__ import annotations

import re

# CFPB redactions: XXXX, XX/XX/XXXX, XX/XX/2026
_REDACTED = re.compile(r"\b[xX]{2,}(?:/(?:[xX]{2,}|\d{2,4}))*\b")
_MONEY = re.compile(r"\{\$[\d,]+(?:\.\d+)?\}|\$\s?[\d,]+(?:\.\d+)?")
_DIGITS = re.compile(r"\d+")
_SPACE = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9']+|[^\sa-z0-9]")


def normalise(text: str) -> str:
    """Lower-case, replace redactions, amounts and numbers with stable tokens, squeeze spaces.

    >>> normalise("I paid {$200.00} on XX/XX/2026 for card 1234")
    'i paid <amount> on <redacted> for card 0'
    """
    text = _REDACTED.sub(" <redacted> ", text)
    text = _MONEY.sub(" <amount> ", text)
    text = text.lower()
    text = _DIGITS.sub("0", text)
    return _SPACE.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    """Split normalised text into word and punctuation tokens (keeps <redacted>, <amount>)."""
    tokens: list[str] = []
    for part in normalise(text).split(" "):
        if part in {"<redacted>", "<amount>"}:
            tokens.append(part)
        elif part:
            tokens.extend(_TOKEN.findall(part))
    return tokens
