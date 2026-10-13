import json
import subprocess
import sys
from pathlib import Path

import joblib
import pytest

from windup_gate.cli import main
from windup_gate.data import load_splits
from windup_gate.evaluation import evaluate
from windup_gate.specialists.intent import IntentClassifier, ModelError
from windup_gate.training import train

DATA = Path(__file__).resolve().parents[1] / "data" / "demo"


@pytest.fixture
def artifact(tmp_path):
    output = tmp_path / "intent.joblib"
    train(DATA, output)
    return output


def test_training_and_loading_round_trip(artifact):
    model = IntentClassifier.load(artifact)
    prediction = model.predict("Przetłumacz wiadomość na angielski")
    assert prediction.label == "translate"
    assert sum(prediction.scores.values()) == pytest.approx(1)
    assert prediction.model_version
    assert prediction.has_features
    assert model.metadata["train_count"] == len(load_splits(DATA)["train"])


def test_no_known_features_are_detected(artifact):
    result = IntentClassifier.load(artifact).predict("qxzvjk 987654321")
    assert not result.has_features


def test_evaluation_reports_counts_and_no_false_certainty(artifact):
    report = evaluate(DATA, artifact, split="validation")
    assert report["split"] == "validation"
    assert report["count"] == len(load_splits(DATA)["validation"])
    assert 0 <= report["macro_f1"] <= 1
    assert 0 <= report["coverage"] <= 1
    assert len(report["confusion_matrix"]) == 5
    assert "majority_accuracy" in report
    assert "synthetic" in report["data_sources"][0]


def test_zero_coverage_has_null_selective_accuracy(artifact):
    report = evaluate(DATA, artifact, min_score=1.0)
    assert report["accepted_count"] == 0
    assert report["accepted_accuracy"] is None


def test_loader_rejects_missing_and_invalid_models(tmp_path):
    with pytest.raises(ModelError):
        IntentClassifier.load(tmp_path / "missing.joblib")
    invalid = tmp_path / "bad.joblib"
    invalid.write_bytes(b"not a model")
    with pytest.raises(ModelError):
        IntentClassifier.load(invalid)
    joblib.dump({"schema_version": 99}, invalid)
    with pytest.raises(ModelError):
        IntentClassifier.load(invalid)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "windup_gate", *map(str, args)], text=True, capture_output=True
    )


def test_cli_train_analyze_and_evaluate_in_new_process(tmp_path):
    model = tmp_path / "intent.joblib"
    result = run_cli("train", "--data", DATA, "--output", model)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["train_count"] > 0
    result = run_cli("analyze", "Przetłumacz wiadomość na angielski", "--model", model)
    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)
    assert decision["prediction"]["label"] == "translate"
    assert decision["completed"] is False
    report_file = tmp_path / "report.json"
    result = run_cli("evaluate", "--data", DATA, "--model", model, "--output", report_file)
    assert result.returncode == 0, result.stderr
    assert json.loads(report_file.read_text())["split"] == "validation"


def test_cli_missing_model_returns_fallback_and_stderr(tmp_path):
    result = run_cli("analyze", "Pomóż mi z kodem", "--model", tmp_path / "missing.joblib")
    assert result.returncode == 0
    assert json.loads(result.stdout)["reason"] == "intent_model_unavailable"
    assert "model" in result.stderr.lower()


def test_cli_bad_data_and_bad_threshold_exit_nonzero(tmp_path):
    result = run_cli("train", "--data", tmp_path)
    assert result.returncode != 0
    assert "error" in result.stderr.lower()
    result = run_cli("analyze", "text", "--min-score", "nan")
    assert result.returncode != 0


def test_cli_json_and_errors_in_process(artifact, tmp_path, capsys):
    assert main(["analyze", "Przetłumacz ten list", "--model", str(artifact)]) == 0
    assert json.loads(capsys.readouterr().out)["prediction"]["label"] == "translate"
    report_file = tmp_path / "report.json"
    assert (
        main(
            [
                "evaluate",
                "--data",
                str(DATA),
                "--model",
                str(artifact),
                "--output",
                str(report_file),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == json.loads(report_file.read_text())
    assert main(["analyze", "text", "--model", str(tmp_path / "absent")]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["route"] == "fallback"
    assert "unavailable" in output.err
    assert main(["train", "--data", str(tmp_path)]) == 2
    assert "error" in capsys.readouterr().err


def test_cli_train_metadata_in_process(tmp_path, capsys):
    assert main(["train", "--data", str(DATA), "--output", str(tmp_path / "intent.joblib")]) == 0
    assert json.loads(capsys.readouterr().out)["train_count"] == 60


def test_training_never_overwrites_an_existing_artifact(artifact):
    before = artifact.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        train(DATA, artifact)
    assert artifact.read_bytes() == before


@pytest.mark.parametrize(
    "mutation",
    [
        "metadata",
        "version",
        "model_version",
        "labels",
        "vectorizer",
        "classifier",
    ],
)
def test_invalid_artifact_structure_is_rejected(artifact, mutation):
    payload = joblib.load(artifact)
    if mutation == "metadata":
        payload["metadata"] = None
    elif mutation == "version":
        payload["metadata"]["sklearn_version"] = "0.0.0"
    elif mutation == "model_version":
        del payload["metadata"]["model_version"]
    elif mutation == "labels":
        payload["pipeline"].named_steps["classifier"].classes_[0] = "unknown"
    elif mutation == "vectorizer":
        payload["pipeline"].steps[0] = ("unexpected", payload["pipeline"].steps[0][1])
    elif mutation == "classifier":
        payload["pipeline"].steps[-1] = ("unexpected", payload["pipeline"].steps[-1][1])
    joblib.dump(payload, artifact)
    with pytest.raises(ModelError):
        IntentClassifier.load(artifact)


def test_invalid_evaluation_split_is_rejected(artifact):
    with pytest.raises(ValueError):
        evaluate(DATA, artifact, split="train")


def test_training_features_do_not_include_held_out_tokens(tmp_path):
    from test_data import write_splits

    def change(split, rows):
        for row in rows:
            row["text"] += f" unique{split}word"

    directory = write_splits(tmp_path, change=change)
    model_path = tmp_path / "intent.joblib"
    train(directory, model_path)
    vocabulary = IntentClassifier.load(model_path).pipeline.named_steps["tfidf"].vocabulary_
    assert "uniquetrainword" in vocabulary
    assert "uniquevalidationword" not in vocabulary
    assert "uniquetestword" not in vocabulary
