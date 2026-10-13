"""Inference from an explicitly supplied, trusted local model artifact."""

import pickle
from pathlib import Path
from typing import Any

import joblib
import sklearn
from sklearn.pipeline import Pipeline

from windup_gate.types import LABELS, Prediction


class ModelError(ValueError):
    """A local model is absent, corrupt, or incompatible."""


class IntentClassifier:
    def __init__(self, pipeline: Pipeline, metadata: dict[str, Any]):
        self.pipeline = pipeline
        self.metadata = metadata

    @classmethod
    def load(cls, path: Path) -> "IntentClassifier":
        # joblib uses pickle: callers must only load artifacts they trust.
        try:
            artifact = joblib.load(path)
        except (
            OSError,
            ValueError,
            EOFError,
            KeyError,
            TypeError,
            AttributeError,
            ImportError,
            pickle.UnpicklingError,
        ) as exc:
            raise ModelError(f"Cannot load model {path}: {exc}") from exc
        if not isinstance(artifact, dict) or artifact.get("schema_version") != 1:
            raise ModelError(f"Unsupported model schema in {path}")
        metadata = artifact.get("metadata")
        pipeline = artifact.get("pipeline")
        if not isinstance(metadata, dict) or not isinstance(pipeline, Pipeline):
            raise ModelError(f"Invalid model payload in {path}")
        if metadata.get("sklearn_version") != sklearn.__version__:
            raise ModelError("scikit-learn version differs; retrain with the current environment")
        if not isinstance(metadata.get("model_version"), str):
            raise ModelError("Missing model version")
        try:
            labels = set(pipeline.classes_)
            vectorizer = pipeline.named_steps["tfidf"]
            features = vectorizer.transform(["validation"])
            pipeline.named_steps["classifier"].predict_proba(features)
        except (AttributeError, KeyError, ValueError) as exc:
            raise ModelError("Model pipeline is not fitted or has an invalid structure") from exc
        if labels != set(LABELS):
            raise ModelError("Model labels differ from the current taxonomy")
        return cls(pipeline, metadata)

    def predict(self, text: str) -> Prediction:
        features = self.pipeline.named_steps["tfidf"].transform([text])
        probabilities = self.pipeline.named_steps["classifier"].predict_proba(features)[0]
        scores = {
            str(label): float(score)
            for label, score in zip(self.pipeline.classes_, probabilities, strict=True)
        }
        ranked = sorted(scores, key=lambda label: scores[label], reverse=True)
        label = ranked[0]
        return Prediction(
            label=label,
            score=scores[label],
            margin=scores[label] - scores[ranked[1]],
            model_version=self.metadata["model_version"],
            scores=scores,
            has_features=bool(features.nnz),
        )
