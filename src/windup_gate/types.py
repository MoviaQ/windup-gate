"""Small, serializable contracts shared by specialists and consumers."""

from dataclasses import dataclass
from typing import Literal, Protocol

LABELS = ("code_help", "detect_language", "other", "summarize", "translate")


@dataclass(frozen=True)
class Request:
    text: str
    target_text: str | None = None
    requires_history: bool = False


@dataclass(frozen=True)
class Prediction:
    label: str
    score: float
    margin: float
    model_version: str
    scores: dict[str, float]
    has_features: bool = True
    score_kind: str = "uncalibrated_probability"


class Specialist(Protocol):
    def predict(self, text: str) -> Prediction: ...


@dataclass(frozen=True)
class LanguagePrediction:
    language: str
    best_language: str
    confidence: float
    margin: float
    uncertain: bool
    calibrated: bool
    model_version: str
    score_kind: str = "upstream_calibrated_probability"


class LanguageSpecialist(Protocol):
    def predict(self, text: str) -> LanguagePrediction: ...


@dataclass(frozen=True)
class Decision:
    request: Request
    route: Literal["local", "assist", "fallback"]
    reason: str
    handler: str | None = None
    prediction: Prediction | None = None
    completed: bool = False
    result: LanguagePrediction | None = None
    error: str | None = None
