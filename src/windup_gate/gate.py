"""Gate selects a route; assist and fallback never execute an LLM call."""

from windup_gate.policy import Policy
from windup_gate.specialists.language import LanguageInputError, LanguageModelError
from windup_gate.types import Decision, LanguageSpecialist, Request, Specialist


class Gate:
    def __init__(
        self,
        intent: Specialist | None,
        policy: Policy | None = None,
        *,
        language: LanguageSpecialist | None = None,
    ):
        self.intent = intent
        self.policy = policy or Policy()
        self.language = language

    def analyze(self, request: Request) -> Decision:
        if not request.text.strip():
            return Decision(request, "fallback", "empty_input")
        if len(request.text) > self.policy.max_chars:
            return Decision(request, "fallback", "input_too_long")
        if request.requires_history:
            return Decision(request, "fallback", "history_required")
        if self.intent is None:
            return Decision(request, "fallback", "intent_model_unavailable")

        prediction = self.intent.predict(request.text)
        reason = self.policy.rejection_reason(prediction)
        if reason:
            return Decision(request, "fallback", reason, prediction=prediction)
        if prediction.label == "detect_language":
            if not request.target_text or not request.target_text.strip():
                return Decision(request, "fallback", "missing_target_text", prediction=prediction)
            if self.language is None:
                return Decision(
                    request, "fallback", "language_specialist_unavailable", prediction=prediction
                )
            if len(request.target_text) > self.policy.max_chars:
                return Decision(request, "fallback", "target_too_long", prediction=prediction)
            try:
                result = self.language.predict(request.target_text)
            except LanguageInputError as exc:
                return Decision(request, "fallback", str(exc), prediction=prediction)
            except LanguageModelError as exc:
                return Decision(
                    request,
                    "fallback",
                    "language_model_unavailable",
                    prediction=prediction,
                    error=str(exc),
                )
            if not result.calibrated:
                return Decision(request, "fallback", "language_uncalibrated", prediction=prediction)
            if result.uncertain or result.language == "und":
                return Decision(request, "fallback", "language_uncertain", prediction=prediction)
            return Decision(
                request,
                "local",
                "language_identified",
                handler="detect_language",
                prediction=prediction,
                completed=True,
                result=result,
            )
        return Decision(
            request, "assist", "intent_accepted", handler=prediction.label, prediction=prediction
        )
