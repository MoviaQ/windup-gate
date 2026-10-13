"""Lazy adapter for the user's existing MoviaQ/windup-language-recog model.

The trusted upstream repository must be on PYTHONPATH. Nothing is downloaded,
copied or trained here; upstream predict_details owns the acceptance policy.
"""

import hashlib
import importlib
import math
import pickle
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

from windup_gate.types import LanguagePrediction


class LanguageModelError(ValueError):
    """Missing runtime/weights, incompatible model, or failed inference."""


class LanguageInputError(ValueError):
    """Input cannot be analyzed without losing text or inventing evidence."""


def _identity(text: str) -> str:
    return text


class WindupLanguageSpecialist:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self._detector: Any = None
        self._normalize: Callable[[str], str] = _identity
        self._model_version = ""

    def _load(self) -> None:
        if self._detector is not None:
            return
        if not self.model_path.is_file():
            raise LanguageModelError(f"Language weights not found: {self.model_path}")
        try:
            module = importlib.import_module("language_detector")
            detector = module.LanguageDetector(self.model_path)
            options = detector.encoding_options
            if options.get("preprocessing", "none") == "ticket_v2":
                normalize = importlib.import_module("ticket_text").normalize_ticket_text
            elif options.get("preprocessing", "none") == "none":
                normalize = _identity
            else:
                raise LanguageModelError("Unsupported upstream preprocessing")
            limit = options.get("max_length", 2000)
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                raise LanguageModelError("Invalid upstream text length limit")
            digest = hashlib.sha256()
            with self.model_path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        except ImportError as exc:
            raise LanguageModelError(
                "Install uv sync --extra language and add the trusted "
                f"windup-language-recog repository to PYTHONPATH: {exc}"
            ) from exc
        except (
            OSError,
            ValueError,
            RuntimeError,
            KeyError,
            AttributeError,
            TypeError,
            pickle.UnpicklingError,
        ) as exc:
            raise LanguageModelError(f"Cannot load language model: {exc}") from exc
        self._normalize = normalize
        self._model_version = f"windup-language-recog-sha256-{digest.hexdigest()}"
        self._detector = detector

    def predict(self, text: str) -> LanguagePrediction:
        self._load()
        limit = self._detector.encoding_options.get("max_length", 2000)
        # Upstream slices after cleanup, NFC and lowercasing. Refuse a slice
        # rather than silently deciding on a different text than the request.
        if len(text) > limit:
            raise LanguageInputError("language_input_too_long")
        normalized = unicodedata.normalize("NFC", self._normalize(text)).lower().strip()
        if len(normalized) > limit:
            raise LanguageInputError("language_input_too_long")
        if sum(char.isalpha() for char in normalized) < 2:
            raise LanguageInputError("insufficient_language_text")
        try:
            details = self._detector.predict_details(text)
            language = details["language"]
            best = details["best_language"]
            confidence = details["confidence"]
            margin = details["margin"]
            uncertain = details["uncertain"]
            calibrated = details["calibrated"]
            if not isinstance(uncertain, bool) or not isinstance(calibrated, bool):
                raise LanguageModelError("Invalid uncertainty/calibration flags from upstream")
            for score in (confidence, margin):
                if (
                    isinstance(score, bool)
                    or not isinstance(score, (int, float))
                    or not math.isfinite(score)
                    or not 0 <= score <= 1
                ):
                    raise LanguageModelError("Invalid language score from upstream")
            if best not in self._detector.languages or language != ("und" if uncertain else best):
                raise LanguageModelError("Inconsistent language result from upstream")
        except (RuntimeError, KeyError, TypeError, AttributeError, ValueError) as exc:
            raise LanguageModelError(f"Language inference failed: {exc}") from exc
        return LanguagePrediction(
            language,
            best,
            float(confidence),
            float(margin),
            uncertain,
            calibrated,
            self._model_version,
            "upstream_calibrated_probability" if calibrated else "uncalibrated_probability",
        )
