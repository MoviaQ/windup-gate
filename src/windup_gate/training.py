"""Train only on the train split; validation and test are never fitted."""

import platform
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from windup_gate.data import fingerprint, load_splits


def train(directory: Path, output: Path, *, seed: int = 42) -> dict[str, Any]:
    rows = load_splits(directory)["train"]
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            ("classifier", LogisticRegression(C=4.0, max_iter=1000, random_state=seed)),
        ]
    )
    pipeline.fit([row.text for row in rows], [row.label for row in rows])
    train_hash = fingerprint(rows)
    metadata = {
        "model_version": f"tfidf-logreg-v1-{train_hash[:12]}",
        "train_fingerprint": train_hash,
        "train_count": len(rows),
        "train_class_counts": dict(Counter(row.label for row in rows)),
        "majority_label": Counter(row.label for row in rows).most_common(1)[0][0],
        "data_sources": sorted({row.source for row in rows}),
        "seed": seed,
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "score_kind": "uncalibrated_probability",
        "config": {"ngram_range": [1, 2], "sublinear_tf": True, "C": 4.0},
    }
    output = Path(output)
    if output.exists():
        raise ValueError(f"Output already exists: {output}; choose a new model path")
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"schema_version": 1, "pipeline": pipeline, "metadata": metadata}, output)
    return metadata
