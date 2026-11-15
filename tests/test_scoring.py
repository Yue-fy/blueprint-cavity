"""Behavioral contracts for the offline verifier; no datasets or network required."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import time
import unittest

try:
    from blueprint_gym.scoring import score_answer
except ModuleNotFoundError:
    score_answer = None


def gold(value=100, unit="m2", family="area", annotated=False):
    result = {"value": value, "unit": unit, "family": family,
              "pages": [{"width": 1000, "height": 800, "space": "image_px"}]}
    if annotated:
        result["evidence"] = [{"page": 0, "bbox": [10, 10, 110, 110], "space": "image_px"}]
    return result


def answer(value=100, unit="m2", confidence=1):
    return {"value": value, "unit": unit, "confidence": confidence,
            "evidence": [{"page": 0, "bbox": [10, 10, 110, 110], "space": "image_px"}],
            "assumptions": []}


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(score_answer, "offline scoring implementation is missing")

    def invalid(self, value, target=None):
        result = score_answer(value, target or gold())
        self.assertFalse(result["valid"], result)
        self.assertEqual(result["reward"], 0)
        self.assertTrue(result["errors"])

    def test_exact_oracle_and_weighted_breakdown(self):
        result = score_answer(answer(), gold())
        self.assertEqual(result["reward"], 1)
        self.assertEqual(result["components"], {"value": .75, "evidence": .15, "calibration": .1})
        self.assertEqual(result["evidence_mode"], "structural")

    def test_empty_missing_and_wrong_container(self):
        for value in (None, {}, [], "answer", 100):
            with self.subTest(value=value): self.invalid(value)

    def test_every_required_field_is_required(self):
        for key in answer():
            item = answer()
            del item[key]
            with self.subTest(field=key): self.invalid(item)

    def test_wrong_area_with_arbitrary_evidence_cannot_exceed_trap_bound(self):
        for confidence in (0, .5, 1):
            item = answer(10000, confidence=confidence)
            item["evidence"][0]["bbox"] = [500, 500, 600, 600]
            result = score_answer(item, gold())
            self.assertLessEqual(result["reward"], .1)
            self.assertEqual(result["evidence_score"], 0)

    def test_length_unit_conversions(self):
        for value, unit in ((1, "m"), (1000, "mm"), (100, "cm"), (1 / .3048, "ft"), (1 / .0254, "in")):
            with self.subTest(unit=unit):
                self.assertEqual(score_answer(answer(value, unit), gold(1, "m", "length"))["reward"], 1)

    def test_area_unit_conversions(self):
        for value, unit in ((1, "m2"), (1, "m²"), (1 / .09290304, "ft2"), (1 / .09290304, "ft²")):
            with self.subTest(unit=unit):
                self.assertEqual(score_answer(answer(value, unit), gold(1))["reward"], 1)

    def test_dimension_mismatch_gets_no_value_or_evidence(self):
        result = score_answer(answer(100, "m", 0), gold())
        self.assertTrue(result["valid"])
        self.assertEqual(result["value_score"], 0)
        self.assertEqual(result["evidence_score"], 0)
        self.assertAlmostEqual(result["reward"], .1)

    def test_unknown_units_are_invalid(self):
        for unit in ("acres-ish", "", None, 1, True):
            with self.subTest(unit=unit): self.invalid(answer(unit=unit))

    def test_count_exact_and_off_by_one(self):
        for target, value, expected in ((10, 10, 1), (10, 9, .5), (10, 11, .5), (9, 10, 0), (10, 12, 0)):
            result = score_answer(answer(value, "count"), gold(target, "count", "count"))
            self.assertEqual(result["value_score"], expected)

    def test_fractional_count_is_invalid(self):
        self.invalid(answer(10.5, "count"), gold(10, "count", "count"))

    def test_large_counts_keep_integer_precision(self):
        target = 10 ** 100
        for difference, expected in ((0, 1), (1, .5), (2, 0)):
            self.assertEqual(score_answer(answer(target + difference, "count"),
                                          gold(target, "count", "count"))["value_score"], expected)

    def test_quantity_boundaries_and_linear_interpolation(self):
        for value, expected in ((98, 1), (102, 1), (91.5, .5), (108.5, .5), (85, 0), (115, 0), (0, 0)):
            with self.subTest(value=value):
                self.assertAlmostEqual(score_answer(answer(value), gold())["value_score"], expected)

    def test_zero_gold_is_exact_only(self):
        self.assertEqual(score_answer(answer(0), gold(0))["value_score"], 1)
        self.assertEqual(score_answer(answer(.001), gold(0))["value_score"], 0)

    def test_alternative_values_take_maximum(self):
        target = gold()
        target["alt_values"] = [200, 300]
        self.assertEqual(score_answer(answer(300), target)["reward"], 1)

    def test_abstention_earns_only_calibration(self):
        result = score_answer(answer(None, confidence=.2), gold())
        self.assertTrue(result["valid"])
        self.assertEqual(result["value_score"], 0)
        self.assertEqual(result["evidence_score"], 0)
        self.assertAlmostEqual(result["reward"], .096)

    def test_brier_calibration_and_correctness_threshold(self):
        self.assertAlmostEqual(score_answer(answer(confidence=.7), gold())["calibration_score"], .91)
        self.assertAlmostEqual(score_answer(answer(200, confidence=.7), gold())["calibration_score"], .51)
        self.assertEqual(score_answer(answer(102.1), gold())["calibration_score"], 1)
        self.assertEqual(score_answer(answer(102.2), gold())["calibration_score"], 0)

    def test_booleans_nonfinite_and_overflow_are_invalid(self):
        for field in ("value", "confidence"):
            for value in (True, False, float("nan"), float("inf"), -float("inf"), 10**10000):
                item = answer()
                item[field] = value
                with self.subTest(field=field, kind=type(value).__name__): self.invalid(item)

    def test_confidence_range_and_assumptions_contract(self):
        for confidence in (-.001, 1.001, "1", None): self.invalid(answer(confidence=confidence))
        for assumptions in ("scale", [None], [42], [True], {}):
            item = answer()
            item["assumptions"] = assumptions
            self.invalid(item)

    def test_evidence_contract_and_maximum(self):
        for evidence in (None, {}, "box", [None], [{"page": 0}], answer()["evidence"] * 33):
            item = answer()
            item["evidence"] = evidence
            self.invalid(item)

    def test_empty_evidence_is_valid_but_earns_none(self):
        item = answer()
        item["evidence"] = []
        result = score_answer(item, gold())
        self.assertTrue(result["valid"])
        self.assertEqual(result["reward"], .85)

    def test_page_bounds_wrong_spaces_and_invalid_geometry(self):
        for patch in ({"page": -1}, {"page": 1}, {"page": True}, {"page": 0.0},
                      {"space": "pdf_pt"}, {"bbox": [-1, 0, 10, 10]},
                      {"bbox": [0, 0, 1001, 10]}, {"bbox": [10, 10, 5, 20]},
                      {"bbox": [10, 10, 10, 20]}, {"bbox": [0, 0, True, 20]},
                      {"bbox": [0, 0, float("nan"), 20]}, {"bbox": [1, 2, 3]}):
            item = answer()
            item["evidence"][0].update(patch)
            with self.subTest(patch=patch): self.invalid(item)

    def test_duplicate_and_fullscreen_boxes_are_invalid(self):
        item = answer()
        item["evidence"] *= 2
        self.invalid(item)
        item = answer()
        item["evidence"][0]["bbox"] = [0, 0, 1000, 800]
        self.invalid(item)

    def test_annotated_bbox_and_point_evidence(self):
        target = gold(annotated=True)
        target["evidence"].append({"page": 0, "point": [20, 20], "space": "image_px"})
        result = score_answer(answer(), target)
        self.assertEqual(result["evidence_mode"], "annotated")
        self.assertEqual(result["reward"], 1)

    def test_annotated_coverage_iou_and_irrelevant_penalty(self):
        target = gold(annotated=True)
        target["evidence"].append({"page": 0, "point": [300, 300], "space": "image_px"})
        self.assertEqual(score_answer(answer(), target)["evidence_score"], .5)
        item = answer()
        item["evidence"].append({"page": 0, "bbox": [500, 500, 600, 600], "space": "image_px"})
        self.assertEqual(score_answer(item, gold(annotated=True))["evidence_score"], .5)
        item = answer()
        item["evidence"][0]["bbox"] = [10, 10, 60, 110]
        self.assertEqual(score_answer(item, gold(annotated=True))["evidence_score"], 1)
        item["evidence"][0]["bbox"] = [10, 10, 30, 110]
        self.assertEqual(score_answer(item, gold(annotated=True))["evidence_score"], 0)

    def test_partial_value_multiplies_evidence(self):
        result = score_answer(answer(108.5), gold(annotated=True))
        self.assertAlmostEqual(result["evidence_score"], .5)

    def test_iou_boundary_and_extreme_page_scale(self):
        item = answer()
        item["evidence"][0]["bbox"] = [10, 10, 40, 110]
        self.assertEqual(score_answer(item, gold(annotated=True))["evidence_score"], 1)
        target = gold(annotated=True)
        target["pages"][0].update(width=1e308, height=1e308)
        self.assertEqual(score_answer(answer(), target)["evidence_score"], 1)

    def test_gold_is_validated_and_never_mutated(self):
        target = gold(annotated=True)
        original = copy.deepcopy(target)
        score_answer(answer(), target)
        self.assertEqual(target, original)
        for patch in ({"value": True}, {"value": float("nan")}, {"unit": "bad"},
                      {"pages": []}, {"alt_values": [float("inf")]},
                      {"evidence": [{"page": 0, "point": [1, 2], "space": "pdf_pt"}]}):
            broken = gold()
            broken.update(patch)
            self.invalid(answer(), broken)

    def test_deterministic_finite_bounded_results(self):
        item = answer(-1e308)
        target = gold(1e308)
        result = score_answer(item, target)
        self.assertEqual(result, score_answer(item, target))
        json.dumps(result, allow_nan=False)
        self.assertTrue(0 <= result["reward"] <= 1)

    def test_cli_missing_malformed_nan_and_oversized_answers_write_zero(self):
        verify = importlib.import_module("blueprint_gym.verify")
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            root = Path(temporary)
            gold_path = root / "gold.json"
            answer_path = root / "answer.json"
            output = root / "out"
            gold_path.write_text(json.dumps(gold()))
            for content in (None, "{", '{"value": NaN}', '{"value": 1e999}',
                            json.dumps(answer())[:-1] + ',"extra": NaN}',
                            json.dumps(answer())[:-1] + ',"value": 100}',
                            "[" * 2000 + "]" * 2000, " " * (1048576 + 1)):
                if content is not None: answer_path.write_text(content)
                start = time.perf_counter()
                status = verify.main(["--gold", str(gold_path), "--answer", str(answer_path), "--output-dir", str(output)])
                self.assertEqual(status, 0)
                self.assertEqual(float((output / "reward.txt").read_text()), 0)
                self.assertFalse(json.loads((output / "breakdown.json").read_text())["valid"])
                self.assertLess(time.perf_counter() - start, 5)

    def test_cli_exact_oracle(self):
        verify = importlib.import_module("blueprint_gym.verify")
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            root = Path(temporary)
            for name, data in (("gold", gold()), ("answer", answer())):
                (root / (name + ".json")).write_text(json.dumps(data))
            self.assertEqual(verify.main(["--gold", str(root / "gold.json"), "--answer", str(root / "answer.json"), "--output-dir", str(root)]), 0)
            self.assertEqual((root / "reward.txt").read_text(), "1\n")
            self.assertEqual(json.loads((root / "breakdown.json").read_text())["reward"], 1)


if __name__ == "__main__":
    unittest.main()
