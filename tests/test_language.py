import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from windup_gate.cli import main
from windup_gate.gate import Gate
from windup_gate.specialists.language import (
    LanguageInputError,
    LanguageModelError,
    WindupLanguageSpecialist,
)
from windup_gate.types import LanguagePrediction, Prediction, Request


class Intent:
    def __init__(self, label="detect_language", score=0.95):
        self.label = label
        self.score = score

    def predict(self, text):
        return Prediction(self.label, self.score, 0.9, "intent-fixture", {self.label: self.score})


class Language:
    def __init__(self, *, uncertain=False, calibrated=True):
        self.calls = []
        self.uncertain = uncertain
        self.calibrated = calibrated

    def predict(self, text):
        self.calls.append(text)
        return LanguagePrediction(
            "und" if self.uncertain else "pl",
            "pl",
            0.99,
            0.9,
            self.uncertain,
            self.calibrated,
            "language-fixture",
        )


def test_gate_executes_language_task_on_target_only():
    language = Language()
    request = Request("What language is this?", "  Nie mogę zalogować się do konta.  ")
    result = Gate(Intent(), language=language).analyze(request)
    assert result.route == "local"
    assert result.completed is True
    assert result.handler == "detect_language"
    assert result.result.language == "pl"
    assert result.prediction.model_version == "intent-fixture"
    assert result.result.model_version == "language-fixture"
    assert result.request == request
    assert language.calls == [request.target_text]


@pytest.mark.parametrize(
    "intent,input_request",
    [
        (Intent("translate"), Request("translate", "Hello world")),
        (Intent(score=0.1), Request("language", "Hello world")),
        (Intent(), Request("language")),
        (Intent(), Request("language", "   ")),
    ],
)
def test_language_model_is_not_used_for_other_or_rejected_requests(intent, input_request):
    language = Language()
    assert Gate(intent, language=language).analyze(input_request).completed is False
    assert not language.calls


@pytest.mark.parametrize(
    "uncertain,calibrated,reason",
    [
        (True, True, "language_uncertain"),
        (False, False, "language_uncalibrated"),
    ],
)
def test_gate_preserves_upstream_abstention_and_requires_calibration(uncertain, calibrated, reason):
    language = Language(uncertain=uncertain, calibrated=calibrated)
    result = Gate(Intent(), language=language).analyze(Request("language", "Hello world"))
    assert result.route == "fallback"
    assert result.reason == reason
    assert result.completed is False
    assert result.result is None


def test_missing_weights_have_actionable_error_and_no_completed_result(tmp_path):
    language = WindupLanguageSpecialist(tmp_path / "missing.pt")
    result = Gate(Intent(), language=language).analyze(Request("language", "Hello world"))
    assert result.reason == "language_model_unavailable"
    assert result.error
    assert "missing.pt" in result.error
    assert result.completed is False


@pytest.fixture
def backend(tmp_path, monkeypatch):
    details = {
        "language": "pl",
        "best_language": "pl",
        "confidence": 0.99,
        "margin": 0.9,
        "uncertain": False,
        "calibrated": True,
    }
    calls = []

    class Backend:
        languages = ["pl", "en"]
        encoding_options = {"max_length": 2000, "preprocessing": "ticket_v2"}

        def __init__(self, model_path):
            calls.append(("load", str(model_path)))

        def predict_details(self, text):
            calls.append(("predict_details", text))
            return details

        def predict(self, text):
            pytest.fail("The adapter must not bypass upstream uncertainty")

    modules = {
        "language_detector": SimpleNamespace(LanguageDetector=Backend),
        "ticket_text": SimpleNamespace(normalize_ticket_text=lambda text: text),
    }
    real_import = importlib.import_module

    def import_backend(name, package=None):
        return modules[name] if name in modules else real_import(name, package)

    monkeypatch.setattr("windup_gate.specialists.language.importlib.import_module", import_backend)
    model = tmp_path / "model.pt"
    model.write_bytes(b"trusted-fixture-not-a-real-checkpoint")
    return WindupLanguageSpecialist(model), details, calls, modules


def test_adapter_loads_once_and_keeps_upstream_score(backend):
    specialist, _, calls, _ = backend
    assert calls == []
    result = specialist.predict("Polski tekst")
    specialist.predict("Kolejny tekst")
    assert [call[0] for call in calls] == ["load", "predict_details", "predict_details"]
    assert result.confidence == 0.99
    assert result.score_kind == "upstream_calibrated_probability"
    assert result.model_version.startswith("windup-language-recog-sha256-")


@pytest.mark.parametrize(
    "text,reason",
    [
        ("123 !!!", "insufficient_language_text"),
        ("a", "insufficient_language_text"),
        ("a" * 2001, "language_input_too_long"),
        ("İ" * 1500, "language_input_too_long"),
    ],
)
def test_adapter_rejects_invalid_or_truncated_input(backend, text, reason):
    specialist, _, calls, _ = backend
    with pytest.raises(LanguageInputError, match=reason):
        specialist.predict(text)
    assert all(call[0] != "predict_details" for call in calls)


def test_cleaned_metadata_does_not_become_a_language_result(backend):
    specialist, _, calls, modules = backend
    modules["ticket_text"].normalize_ticket_text = lambda text: ""
    with pytest.raises(LanguageInputError):
        specialist.predict("https://example.org")
    assert all(call[0] != "predict_details" for call in calls)


@pytest.mark.parametrize(
    "field,value",
    [
        ("confidence", float("nan")),
        ("margin", -0.1),
        ("confidence", 1.1),
        ("language", "unknown"),
        ("uncertain", "false"),
        ("calibrated", "yes"),
        ("language", "und"),
        ("best_language", "unknown"),
    ],
)
def test_adapter_rejects_invalid_upstream_details(backend, field, value):
    specialist, details, _, _ = backend
    details[field] = value
    with pytest.raises(LanguageModelError):
        specialist.predict("Polski tekst")


def test_upstream_und_is_not_replaced_with_best_language(backend):
    specialist, details, _, _ = backend
    details.update(language="und", uncertain=True)
    result = specialist.predict("wspólne słowo")
    assert result.language == "und"
    assert result.best_language == "pl"
    assert result.uncertain


def test_dependency_error_is_explicit(tmp_path, monkeypatch):
    model = tmp_path / "model.pt"
    model.write_bytes(b"fixture")

    def unavailable(name):
        raise ModuleNotFoundError("language_detector is not installed")

    monkeypatch.setattr("windup_gate.specialists.language.importlib.import_module", unavailable)
    with pytest.raises(LanguageModelError, match="PYTHONPATH"):
        WindupLanguageSpecialist(model).predict("Hello world")


@pytest.mark.parametrize(
    "failure", [ValueError("incompatible checkpoint"), RuntimeError("bad weights")]
)
def test_checkpoint_load_failure_becomes_explained_fallback(backend, monkeypatch, failure):
    specialist, _, _, modules = backend

    def fail(model_path):
        raise failure

    monkeypatch.setattr(modules["language_detector"], "LanguageDetector", fail)
    result = Gate(Intent(), language=specialist).analyze(Request("language", "Hello world"))
    assert result.reason == "language_model_unavailable"
    assert str(failure) in result.error
    assert result.completed is False


@pytest.mark.parametrize(
    "options",
    [
        {"max_length": 0},
        {"max_length": True},
        {"max_length": "2000"},
        {"preprocessing": "unknown"},
    ],
)
def test_unsupported_checkpoint_configuration_is_rejected(backend, options):
    specialist, _, _, modules = backend
    modules["language_detector"].LanguageDetector.encoding_options = options
    with pytest.raises(LanguageModelError):
        specialist.predict("Hello world")


def test_plain_text_checkpoint_uses_identity_preprocessing(backend):
    specialist, _, _, modules = backend
    modules["language_detector"].LanguageDetector.encoding_options = {"preprocessing": "none"}
    assert specialist.predict("Hello world").language == "pl"


def test_backend_inference_failure_becomes_explained_fallback(backend, monkeypatch):
    specialist, _, _, modules = backend

    def fail(self, text):
        raise RuntimeError("fixture inference error")

    monkeypatch.setattr(modules["language_detector"].LanguageDetector, "predict_details", fail)
    result = Gate(Intent(), language=specialist).analyze(Request("language", "Hello world"))
    assert result.reason == "language_model_unavailable"
    assert "fixture inference error" in result.error
    assert result.completed is False


def test_gate_rejects_target_too_long_without_running_specialist():
    language = Language()
    result = Gate(Intent(), language=language).analyze(Request("language", "a" * 20_001))
    assert result.reason == "target_too_long"
    assert not language.calls


def test_gate_preserves_input_rejection_reason(backend):
    specialist, _, _, _ = backend
    result = Gate(Intent(), language=specialist).analyze(Request("language", "123 !!!"))
    assert result.route == "fallback"
    assert result.reason == "insufficient_language_text"
    assert result.result is None


def test_cli_language_option_uses_adapter_and_returns_result(backend, monkeypatch, capsys):
    specialist, _, _, _ = backend
    monkeypatch.setattr("windup_gate.cli.IntentClassifier.load", lambda path: Intent())
    monkeypatch.setattr("windup_gate.cli.WindupLanguageSpecialist", lambda path: specialist)
    assert (
        main(
            [
                "analyze",
                "Jaki to język?",
                "--target-text",
                "Polski tekst",
                "--language-model",
                "model.pt",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["route"] == "local"
    assert output["result"]["language"] == "pl"


def test_cli_missing_language_model_reports_stderr(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("windup_gate.cli.IntentClassifier.load", lambda path: Intent())
    assert (
        main(
            [
                "analyze",
                "Jaki to język?",
                "--target-text",
                "Polski tekst",
                "--language-model",
                str(tmp_path / "missing.pt"),
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["route"] == "fallback"
    assert "missing.pt" in output.err


def test_real_windup_model_if_explicitly_requested():
    import os

    model_path = os.environ.get("WINDUP_LANGUAGE_TEST_MODEL")
    if not model_path:
        pytest.skip(
            "Set WINDUP_LANGUAGE_TEST_MODEL and PYTHONPATH for the offline integration test"
        )
    gate = Gate(Intent(), language=WindupLanguageSpecialist(Path(model_path)))
    for text, expected in [
        ("Nie mogę zalogować się do mojego konta po zmianie hasła.", "pl"),
        ("I cannot sign in to my account after changing my password.", "en"),
        ("Ich kann mich nach der Änderung meines Passworts nicht anmelden.", "de"),
    ]:
        decision = gate.analyze(Request("Jaki to język?", text))
        assert decision.route == "local", decision
        assert decision.result.language == expected
    assert gate.analyze(Request("Jaki to język?", "123 !!!")).route == "fallback"
