"""3-minute execution layer for the 45-minute time-anchor model.

The 45-minute model remains primary. This module only defines how a lower-
timeframe confirmation can be measured after the 09:45 anchor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Sequence

from .displacement import DisplacementResult, measure_displacement
from .liquidity import swept_high, swept_low
from .market_structure import StructureResult, classify_structure
from .time_windows import ensure_new_york

EXECUTION_TIMEFRAME = "3m"
MAIN_ANCHOR_TIME = time(9, 45)
PRE_ANCHOR_SETUP_TIME = time(8, 45)


@dataclass(frozen=True)
class ExecutionConfirmation:
    qualified: bool
    direction: str
    confirmation_time: datetime | None
    sweep_type: str | None
    displacement: DisplacementResult | None
    structure: StructureResult | None
    reason: str


def _ts(bar: dict) -> datetime:
    value = bar["timestamp"]
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)


def find_3m_confirmation(
    bars: Sequence[dict],
    *,
    anchor_time: time = MAIN_ANCHOR_TIME,
    reference_high: float | None = None,
    reference_low: float | None = None,
    lookback: int = 2,
    displacement_multiplier: float = 1.5,
    min_body_ratio: float = 0.6,
) -> ExecutionConfirmation:
    """Find the first objective 3-minute confirmation after the 09:45 anchor.

    For bullish confirmation, price must first sweep the reference low and
    then produce bullish displacement with bullish structure. Bearish
    confirmation is the mirror image. If no reference range is supplied,
    confirmation cannot qualify; this prevents the execution layer from
    inventing a liquidity level.
    """
    if not bars:
        return ExecutionConfirmation(False, "neutral", None, None, None, None, "No 3-minute bars")

    ordered = sorted(bars, key=_ts)
    anchor = next((b for b in ordered if _ts(b).time().replace(second=0, microsecond=0) == anchor_time), None)
    if anchor is None:
        return ExecutionConfirmation(False, "neutral", None, None, None, None, "09:45 anchor not present")

    post = [b for b in ordered if _ts(b) > _ts(anchor)]
    history: list[dict] = []
    swept_low_flag = False
    swept_high_flag = False

    for bar in post:
        if reference_low is not None and swept_low(bar, reference_low):
            swept_low_flag = True
        if reference_high is not None and swept_high(bar, reference_high):
            swept_high_flag = True

        displacement = measure_displacement(
            bar,
            history,
            multiplier=displacement_multiplier,
            min_body_ratio=min_body_ratio,
        )
        structure_history = history + [bar]
        structure = classify_structure(structure_history, lookback=lookback)

        if swept_low_flag and displacement.confirmed and displacement.direction == "bullish" and structure.classification == "bullish":
            return ExecutionConfirmation(
                True, "bullish", _ts(bar), "sell_side", displacement, structure,
                "09:45 anchor + sell-side sweep + bullish displacement + structure",
            )
        if swept_high_flag and displacement.confirmed and displacement.direction == "bearish" and structure.classification == "bearish":
            return ExecutionConfirmation(
                True, "bearish", _ts(bar), "buy_side", displacement, structure,
                "09:45 anchor + buy-side sweep + bearish displacement + structure",
            )

        history.append(bar)

    return ExecutionConfirmation(False, "neutral", None, None, None, None, "No objective 3-minute confirmation")
