"""Read fixed JSONL splits and reject obvious data leakage before learning."""

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from windup_gate.types import LABELS

SPLITS = ("train", "validation", "test")


class DatasetError(ValueError):
    """The dataset is missing, invalid, or leaks between splits."""


@dataclass(frozen=True)
class Example:
    id: str
    text: str
    label: str
    group_id: str
    source: str


def normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def load_splits(directory: Path) -> dict[str, list[Example]]:
    directory = Path(directory)
    result: dict[str, list[Example]] = {}
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    group_splits: dict[str, str] = {}
    for split in SPLITS:
        path = directory / f"{split}.jsonl"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise DatasetError(f"Cannot read {path}: {exc}") from exc
        rows: list[Example] = []
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            location = f"{path}:{number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetError(f"Invalid JSON at {location}") from exc
            fields = ("id", "text", "label", "group_id", "source")
            if not isinstance(record, dict) or any(
                not isinstance(record.get(key), str) or not record[key].strip() for key in fields
            ):
                raise DatasetError(f"Expected nonempty string fields {fields} at {location}")
            row = Example(**{key: record[key] for key in fields})
            if row.label not in LABELS:
                raise DatasetError(f"Unknown label {row.label!r} at {location}")
            text_key = normalized_text(row.text)
            if row.id in seen_ids or text_key in seen_texts:
                raise DatasetError(f"Duplicate ID or text at {location}")
            if row.group_id in group_splits and group_splits[row.group_id] != split:
                raise DatasetError(f"Group {row.group_id!r} leaks between splits at {location}")
            seen_ids.add(row.id)
            seen_texts.add(text_key)
            group_splits[row.group_id] = split
            rows.append(row)
        if {row.label for row in rows} != set(LABELS):
            raise DatasetError(f"{path} must contain all labels: {LABELS}")
        result[split] = rows
    return result


def fingerprint(rows: list[Example]) -> str:
    """Hash exactly the ordered examples consumed by training."""
    payload = [[row.id, row.text, row.label, row.group_id, row.source] for row in rows]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
