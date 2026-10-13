"""Evaluate intent acceptance separately from task completion."""

from pathlib import Path
from typing import Any

from sklearn.metrics import classification_report, confusion_matrix, f1_score

from windup_gate.data import fingerprint, load_splits
from windup_gate.policy import Policy
from windup_gate.specialists.intent import IntentClassifier
from windup_gate.types import LABELS


def evaluate(
    directory: Path,
    model_path: Path,
    *,
    split: str = "validation",
    min_score: float = 0.6,
    min_margin: float = 0.15,
) -> dict[str, Any]:
    if split not in ("validation", "test"):
        raise ValueError("Evaluation split must be validation or test")
    policy = Policy(min_score=min_score, min_margin=min_margin)
    rows = load_splits(directory)[split]
    model = IntentClassifier.load(model_path)
    predictions = [model.predict(row.text) for row in rows]
    accepted = [
        (row, prediction)
        for row, prediction in zip(rows, predictions, strict=True)
        if policy.rejection_reason(prediction) is None
    ]
    correct = sum(row.label == prediction.label for row, prediction in accepted)
    truth = [row.label for row in rows]
    guesses = [prediction.label for prediction in predictions]
    return {
        "scope": "intent classification only; not end-to-end task completion",
        "split": split,
        "count": len(rows),
        "data_sources": sorted({row.source for row in rows}),
        "split_fingerprint": fingerprint(rows),
        "model_metadata": model.metadata,
        "policy": {"min_score": min_score, "min_margin": min_margin},
        "labels": list(LABELS),
        "macro_f1": float(f1_score(truth, guesses, labels=list(LABELS), average="macro")),
        "classification_report": classification_report(
            truth,
            guesses,
            labels=list(LABELS),
            output_dict=True,
            # sklearn accepts numeric values here; its current annotation is narrower.
            zero_division=0,  # pyright: ignore[reportArgumentType]
        ),
        "confusion_matrix": confusion_matrix(truth, guesses, labels=list(LABELS)).tolist(),
        "majority_accuracy": sum(label == model.metadata["majority_label"] for label in truth)
        / len(rows),
        "accepted_count": len(accepted),
        "accepted_correct": correct,
        "coverage": len(accepted) / len(rows),
        "accepted_accuracy": correct / len(accepted) if accepted else None,
        "errors": [
            {
                "id": row.id,
                "expected": row.label,
                "predicted": prediction.label,
                "score": prediction.score,
                "accepted": policy.rejection_reason(prediction) is None,
            }
            for row, prediction in zip(rows, predictions, strict=True)
            if row.label != prediction.label
        ],
        "limitations": [
            "Scores are uncalibrated; thresholds are illustrative, not a safety guarantee.",
            "Synthetic examples cannot establish real-world accuracy or LLM cost savings.",
            "Accepted intent predictions do not imply that Gate has completed a task.",
        ],
    }
