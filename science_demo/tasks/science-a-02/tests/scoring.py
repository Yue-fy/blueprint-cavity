"""Standard-library-only, offline scoring for the private optional science tasks."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import stat

MAX_ANSWER_BYTES = 1024 * 1024
REQUIRED_FIELDS = {"value", "confidence", "rationale"}


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _invalid(reason):
    return {"valid": False, "reason": reason, "value_score": 0.0,
            "correct": False, "calibration": 0.0, "reward": 0.0}


def score_answer(answer, gold):
    """Score a decoded answer; malformed answers always receive zero total credit."""
    if not isinstance(answer, dict) or set(answer) != REQUIRED_FIELDS:
        return _invalid("Answer must contain exactly value, confidence, and rationale.")
    value, confidence = answer["value"], answer["confidence"]
    if value is not None and not _finite_number(value):
        return _invalid("value must be a finite number or null.")
    if not _finite_number(confidence) or not 0 <= confidence <= 1:
        return _invalid("confidence must be a finite number in [0, 1].")
    if not isinstance(answer["rationale"], str):
        return _invalid("rationale must be a string.")
    target = gold["value"]
    if not _finite_number(target) or target == 0:
        raise ValueError("Scientific task gold must be finite and nonzero.")
    value_score = 0.0
    relative_error = None
    if value is not None:
        # Divide before subtracting to avoid overflow for opposite large values.
        relative_error = abs(value / target - 1)
        if relative_error <= .001:
            value_score = 1.0
        elif relative_error < .05:
            value_score = (.05 - relative_error) / .049
    correct = value_score >= .99
    calibration = 1 - (confidence - int(correct)) ** 2
    return {"valid": True, "reason": "ok", "relative_error": relative_error,
            "value_score": value_score, "correct": correct,
            "calibration": calibration, "reward": .9 * value_score + .1 * calibration}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key.")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Nonfinite JSON constant.")


def score_file(answer_path, gold):
    """Read at most 1 MiB plus one byte; reject nonstandard JSON and duplicates."""
    try:
        # Artifact handoff must be a regular file. Nonblocking/no-follow open
        # also prevents FIFOs and symlink races from stalling the verifier.
        descriptor = os.open(answer_path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                return _invalid("Answer must be a regular file.")
            if info.st_size > MAX_ANSWER_BYTES:
                return _invalid("Answer exceeds 1 MiB.")
            raw = stream.read(MAX_ANSWER_BYTES + 1)
        if len(raw) > MAX_ANSWER_BYTES:
            return _invalid("Answer exceeds 1 MiB.")
        decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
    except (OSError, UnicodeError, ValueError, RecursionError):
        return _invalid("Answer missing or malformed JSON.")
    return score_answer(decoded, gold)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--answer", type=Path, default=Path("/workspace/answer.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("/logs/verifier"))
    args = parser.parse_args(argv)
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    result = score_file(args.answer, gold)
    # Infinite error is a valid internal outcome for very large finite answers;
    # store it as null so the report itself always remains strict JSON.
    if result.get("relative_error") is not None and not math.isfinite(result["relative_error"]):
        result["relative_error"] = None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "reward.txt").write_text(f'{result["reward"]:.17g}\n', encoding="utf-8")
    (args.output_dir / "breakdown.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
