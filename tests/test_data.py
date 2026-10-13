import json

import pytest

from windup_gate.data import DatasetError, load_splits


def write_splits(tmp_path, *, change=None):
    for split in ("train", "validation", "test"):
        rows = [
            {
                "id": f"{split}-{i}",
                "text": f"{split} example {i}",
                "label": label,
                "group_id": f"{split}-group-{i}",
                "source": "test-fixture",
            }
            for i, label in enumerate(
                ("detect_language", "translate", "summarize", "code_help", "other")
            )
        ]
        if change:
            change(split, rows)
        (tmp_path / f"{split}.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
        )
    return tmp_path


def test_load_splits_preserves_labels_and_provenance(tmp_path):
    splits = load_splits(write_splits(tmp_path))
    assert len(splits["train"]) == 5
    assert splits["test"][0].source == "test-fixture"


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "train-0"),
        ("group_id", "train-group-0"),
        ("text", "  TRAIN   example 0  "),
    ],
)
def test_rejects_leakage_between_splits(tmp_path, field, value):
    def change(split, rows):
        if split == "test":
            rows[0][field] = value

    with pytest.raises(DatasetError):
        load_splits(write_splits(tmp_path, change=change))


@pytest.mark.parametrize(
    "field,value", [("label", "invented"), ("text", ""), ("group_id", 7), ("source", None)]
)
def test_rejects_invalid_records(tmp_path, field, value):
    def change(split, rows):
        rows[0][field] = value

    with pytest.raises(DatasetError):
        load_splits(write_splits(tmp_path, change=change))


def test_rejects_missing_or_malformed_data(tmp_path):
    with pytest.raises(DatasetError):
        load_splits(tmp_path)
    write_splits(tmp_path)
    (tmp_path / "test.jsonl").write_text("not json", encoding="utf-8")
    with pytest.raises(DatasetError, match="test.jsonl"):
        load_splits(tmp_path)


def test_requires_all_classes_in_each_split(tmp_path):
    with pytest.raises(DatasetError):
        load_splits(write_splits(tmp_path, change=lambda split, rows: rows.pop()))
