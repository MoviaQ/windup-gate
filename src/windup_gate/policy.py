"""Acceptance thresholds are policy, not learned certainty guarantees."""

import math
from dataclasses import dataclass

from windup_gate.types import LABELS, Prediction


@dataclass(frozen=True)
class Policy:
    min_score: float = 0.6
    min_margin: float = 0.15
    max_chars: int = 20_000

    def __post_init__(self) -> None:
        for name, value in (("min_score", self.min_score), ("min_margin", self.min_margin)):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite and between 0 and 1")
        if not isinstance(self.max_chars, int) or self.max_chars <= 0:
            raise ValueError("max_chars must be a positive integer")

    def rejection_reason(self, prediction: Prediction) -> str | None:
        if not prediction.has_features:
            return "no_known_features"
        if prediction.label not in LABELS or prediction.label == "other":
            return "unsupported_intent"
        if not math.isfinite(prediction.score) or prediction.score < self.min_score:
            return "low_confidence"
        if not math.isfinite(prediction.margin) or prediction.margin < self.min_margin:
            return "ambiguous_intent"
        return None
