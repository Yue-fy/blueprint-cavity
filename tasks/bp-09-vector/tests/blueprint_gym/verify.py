"""Offline CLI: python -m blueprint_gym.verify --gold ... --answer ... --output-dir ..."""

import argparse
import json
import math
from pathlib import Path

try:  # Also permit the verifier and scorer to be copied together into task tests.
    from .scoring import invalid_result, score_answer
except ImportError:
    from scoring import invalid_result, score_answer


MAX_JSON_BYTES = 1024 * 1024


def _reject_constant(value):
    raise ValueError("non-finite JSON number: " + value)


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON number overflows a finite float")
    return number


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key: " + key)
        result[key] = value
    return result


def read_json(path):
    """Read at most 1 MiB, rejecting duplicate keys and nonstandard numbers."""
    with Path(path).open("rb") as stream:
        content = stream.read(MAX_JSON_BYTES + 1)
    if len(content) > MAX_JSON_BYTES:
        raise ValueError("JSON input exceeds 1 MiB")
    return json.loads(content.decode("utf-8"), parse_constant=_reject_constant,
                      parse_float=_finite_float, object_pairs_hook=_unique_object)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--answer", required=True)
    parser.add_argument("--output-dir", required=True)
    arguments = parser.parse_args(argv)
    try:
        gold = read_json(arguments.gold)
        answer = read_json(arguments.answer)
        result = score_answer(answer, gold)
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        result = invalid_result("unable to load verifier input: " + str(error))
    output = Path(arguments.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "reward.txt").write_text(format(result["reward"], ".17g") + "\n", encoding="utf-8")
    (output / "breakdown.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
