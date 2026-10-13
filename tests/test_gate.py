import math

import pytest

from windup_gate.gate import Gate
from windup_gate.policy import Policy
from windup_gate.types import Prediction, Request


class StubIntent:
    def __init__(self, label="translate", score=0.9, margin=0.6, has_features=True):
        self.result = Prediction(label, score, margin, "fixture", {label: score}, has_features)
        self.calls = []

    def predict(self, text):
        self.calls.append(text)
        return self.result


def test_assist_preserves_original_request_and_does_not_execute_task():
    original = "  Przetłumacz: nie usuwaj niczego!\n  "
    intent = StubIntent()
    decision = Gate(intent).analyze(Request(original, target_text="Hello"))
    assert decision.route == "assist"
    assert decision.handler == "translate"
    assert decision.request.text == original
    assert decision.request.target_text == "Hello"
    assert decision.completed is False
    assert intent.calls == [original]


@pytest.mark.parametrize(
    "text,history,reason",
    [
        ("   ", False, "empty_input"),
        ("x" * 21, False, "input_too_long"),
        ("zrób to samo", True, "history_required"),
    ],
)
def test_invalid_inputs_bypass_classifier(text, history, reason):
    intent = StubIntent()
    decision = Gate(intent, Policy(max_chars=20)).analyze(Request(text, requires_history=history))
    assert decision.route == "fallback"
    assert decision.reason == reason
    assert not intent.calls


def test_missing_model_is_explicit_fallback():
    result = Gate(None).analyze(Request("Pomóż mi z kodem"))
    assert result.reason == "intent_model_unavailable"
    assert result.route == "fallback"


@pytest.mark.parametrize(
    "label,score,margin,features,reason",
    [
        ("other", 0.99, 0.98, True, "unsupported_intent"),
        ("translate", 0.3, 0.2, True, "low_confidence"),
        ("translate", 0.9, 0.01, True, "ambiguous_intent"),
        ("translate", 0.9, 0.8, False, "no_known_features"),
        ("made_up", 0.99, 0.98, True, "unsupported_intent"),
    ],
)
def test_policy_abstains(label, score, margin, features, reason):
    decision = Gate(StubIntent(label, score, margin, features)).analyze(Request("text"))
    assert decision.route == "fallback"
    assert decision.reason == reason
    assert decision.prediction is not None


def test_language_detection_requires_explicit_target_and_specialist():
    gate = Gate(StubIntent("detect_language"))
    assert gate.analyze(Request("Jaki to język?")).reason == "missing_target_text"
    result = gate.analyze(Request("Jaki to język?", target_text="Bonjour tout le monde"))
    assert result.reason == "language_specialist_unavailable"
    assert result.completed is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_score": -1},
        {"min_score": math.nan},
        {"min_score": math.inf},
        {"min_margin": 1.1},
        {"max_chars": 0},
    ],
)
def test_rejects_invalid_policy_configuration(kwargs):
    with pytest.raises(ValueError):
        Policy(**kwargs)


def test_score_threshold_boundary_is_inclusive():
    result = Gate(StubIntent(score=0.6, margin=0.15)).analyze(Request("text"))
    assert result.route == "assist"
