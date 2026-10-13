"""CLI output is JSON on stdout; operational errors go to stderr."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from windup_gate.data import DatasetError
from windup_gate.evaluation import evaluate
from windup_gate.gate import Gate
from windup_gate.policy import Policy
from windup_gate.specialists.intent import IntentClassifier, ModelError
from windup_gate.specialists.language import WindupLanguageSpecialist
from windup_gate.training import train
from windup_gate.types import Request


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="windup-gate")
    commands = root.add_subparsers(dest="command", required=True)
    fit = commands.add_parser("train", help="Train on the train JSONL split only")
    fit.add_argument("--data", type=Path, default=Path("data/demo"))
    fit.add_argument("--output", type=Path, default=Path("models/intent.joblib"))
    fit.add_argument("--seed", type=int, default=42)
    analyze = commands.add_parser(
        "analyze", help="Return a routing decision without calling an LLM"
    )
    analyze.add_argument("text")
    analyze.add_argument("--target-text")
    analyze.add_argument("--requires-history", action="store_true")
    analyze.add_argument("--max-chars", type=int, default=20_000)
    analyze.add_argument(
        "--language-model",
        type=Path,
        help="Trusted local Wind-Up language weights; upstream source must be on PYTHONPATH",
    )
    report = commands.add_parser("evaluate", help="Evaluate held-out intent classification")
    report.add_argument("--data", type=Path, default=Path("data/demo"))
    report.add_argument("--split", choices=("validation", "test"), default="validation")
    report.add_argument("--output", type=Path)
    for command in (analyze, report):
        command.add_argument(
            "--model",
            type=Path,
            default=Path("models/intent.joblib"),
            help="Trusted local joblib artifact only",
        )
        command.add_argument("--min-score", type=float, default=0.6)
        command.add_argument("--min-margin", type=float, default=0.15)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "train":
            output = train(args.data, args.output, seed=args.seed)
        elif args.command == "evaluate":
            output = evaluate(
                args.data,
                args.model,
                split=args.split,
                min_score=args.min_score,
                min_margin=args.min_margin,
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
        else:
            policy = Policy(args.min_score, args.min_margin, args.max_chars)
            model = None
            try:
                model = IntentClassifier.load(args.model)
            except ModelError as exc:
                print(f"Model unavailable: {exc}", file=sys.stderr)
            request = Request(args.text, args.target_text, args.requires_history)
            language = (
                WindupLanguageSpecialist(args.language_model) if args.language_model else None
            )
            decision = Gate(model, policy, language=language).analyze(request)
            if decision.error:
                print(f"Language model unavailable: {decision.error}", file=sys.stderr)
            output = asdict(decision)
    except (DatasetError, ModelError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
    return 0
