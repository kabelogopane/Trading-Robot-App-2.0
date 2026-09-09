"""Objective hypothetical-entry qualification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    structure: Any,
    displacement: Any | None = None,
    liquidity_swept: bool = False,
    invalidation_buffer: float = 0.0,
    *,
    structure_classification: str | None = None,
    displacement_confirmed: bool | None = None,
    buffer: float | None = None,
) -> EntrySignal:
    """Qualify a simulated entry using time-model state plus confirmation.

    Accepts the structured market-state objects used by the backtest engine.
    No broker or real-money order is created by this function.
    """
    direction = direction.lower()
    if direction not in {"bullish", "bearish"}:
        return EntrySignal(False, "neutral", None, None, "No directional bias")

    if structure_classification is not None:
        structure_value = structure_classification
    elif isinstance(structure, str):
        structure_value = structure
    else:
        structure_value = getattr(structure, "classification", "neutral")

    if structure_value != direction:
        return EntrySignal(False, direction, None, None, "Structure does not agree")

    if displacement_confirmed is not None:
        displacement_value = displacement_confirmed
    elif displacement is None:
        displacement_value = False
    elif isinstance(displacement, bool):
        displacement_value = displacement
    else:
        displacement_value = bool(getattr(displacement, "confirmed", False)) and (
            getattr(displacement, "direction", direction) == direction
        )

    if not displacement_value:
        return EntrySignal(False, direction, None, None, "Displacement not confirmed")
    if not liquidity_swept:
        return EntrySignal(False, direction, None, None, "Liquidity reaction not observed")

    entry = float(current_price)
    effective_buffer = float(buffer if buffer is not None else invalidation_buffer)
    if direction == "bullish":
        invalidation = float(anchor_low) - effective_buffer
    else:
        invalidation = float(anchor_high) + effective_buffer

    if (direction == "bullish" and invalidation >= entry) or (
        direction == "bearish" and invalidation <= entry
    ):
        return EntrySignal(False, direction, None, None, "Invalid risk geometry")

    return EntrySignal(True, direction, entry, invalidation, "Objective confirmation met")
