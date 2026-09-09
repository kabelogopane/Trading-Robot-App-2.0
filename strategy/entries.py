"""Objective hypothetical-entry qualification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntrySignal:
    qualified: bool
    direction: str
    entry: float | None
    invalidation: float | None
    reason: str


def qualify_entry(
    direction: str,
    current_price: float,
    anchor_high: float,
    anchor_low: float,
    structure: str,
    displacement_confirmed: bool,
    liquidity_swept: bool,
    buffer: float = 0.0,
) -> EntrySignal:
    """Qualify a simulated entry using time-model state plus confirmation.

    The function requires directional agreement from structure, displacement,
    and a liquidity event. It never treats the anchor itself as a buy/sell
    instruction.
    """
    direction = direction.lower()
    if direction not in {"bullish", "bearish"}:
        return EntrySignal(False, "neutral", None, None, "No directional bias")
    if structure != direction:
        return EntrySignal(False, direction, None, None, "Structure does not agree")
    if not displacement_confirmed:
        return EntrySignal(False, direction, None, None, "Displacement not confirmed")
    if not liquidity_swept:
        return EntrySignal(False, direction, None, None, "Liquidity reaction not observed")

    entry = float(current_price)
    if direction == "bullish":
        invalidation = float(anchor_low) - buffer
    else:
        invalidation = float(anchor_high) + buffer

    if (direction == "bullish" and invalidation >= entry) or (direction == "bearish" and invalidation <= entry):
        return EntrySignal(False, direction, None, None, "Invalid risk geometry")

    return EntrySignal(True, direction, entry, invalidation, "Objective confirmation met")
