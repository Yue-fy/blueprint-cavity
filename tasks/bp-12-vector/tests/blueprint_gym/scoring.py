"""Pure standard-library scoring with strict, fail-closed input validation.

Evidence is always gated by numerical correctness. Unannotated evidence can
only establish structural validity; it is not proof of semantic relevance.
"""

from decimal import Decimal, localcontext
import math


WEIGHTS = {"value": .75, "evidence": .15, "calibration": .10}
MAX_EVIDENCE = 32
MAX_BOX_PAGE_FRACTION = .90
SPACES = {"pdf_pt", "image_px"}
UNITS = {
    "m": ("length", "1"), "mm": ("length", ".001"),
    "cm": ("length", ".01"), "ft": ("length", ".3048"),
    "in": ("length", ".0254"),
    "m2": ("area", "1"), "m²": ("area", "1"),
    "mm2": ("area", ".000001"), "mm²": ("area", ".000001"),
    "cm2": ("area", ".0001"), "cm²": ("area", ".0001"),
    "ft2": ("area", ".09290304"), "ft²": ("area", ".09290304"),
    "in2": ("area", ".00064516"), "in²": ("area", ".00064516"),
    "count": ("count", "1"),
}


def invalid_result(message, evidence_mode="structural"):
    """Return the same JSON-safe, zero-credit envelope for all invalid input."""
    return {"reward": 0.0, "value_score": 0.0, "evidence_score": 0.0,
            "calibration_score": 0.0, "components": dict.fromkeys(WEIGHTS, 0.0),
            "valid": False, "errors": [str(message)], "evidence_mode": evidence_mode}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value, label):
    _require(type(value) in (int, float), label + " must be a finite number (not a boolean)")
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError):
        finite = False
    _require(finite, label + " must be finite")
    return value


def _unit(value, label):
    _require(isinstance(value, str) and value in UNITS, label + " is unsupported")
    return UNITS[value]


def _quantity(value, dimension, label):
    _number(value, label)
    if dimension == "count":
        _require(value == int(value), label + " must be an integer count")


def _geometry(element, pages, label, answer=False):
    _require(isinstance(element, dict), label + " must be an object")
    page = element.get("page")
    _require(type(page) is int and 0 <= page < len(pages), label + " has an invalid page")
    canonical = pages[page]
    _require(element.get("space") == canonical["space"], label + " space must match the canonical page space")
    has_box, has_point = "bbox" in element, "point" in element
    _require(has_box and not has_point if answer else has_box != has_point,
             label + " must contain exactly one " + ("bbox" if answer else "bbox or point"))
    coordinates = element["bbox"] if has_box else element["point"]
    _require(isinstance(coordinates, list) and len(coordinates) == (4 if has_box else 2),
             label + " coordinates have the wrong shape")
    for number in coordinates:
        _number(number, label + " coordinate")
    width, height = canonical["width"], canonical["height"]
    xs, ys = coordinates[::2], coordinates[1::2]
    _require(all(0 <= x <= width for x in xs) and all(0 <= y <= height for y in ys),
             label + " lies outside the page")
    if has_box:
        x0, y0, x1, y1 = coordinates
        _require(x0 < x1 and y0 < y1, label + " bbox must have positive width and height")
        if answer:
            fraction = ((x1 - x0) / width) * ((y1 - y0) / height)
            _require(fraction <= MAX_BOX_PAGE_FRACTION, label + " bbox is oversized (>90% of page)")
    if "note" in element:
        _require(isinstance(element["note"], str), label + " note must be a string")


def _validate_gold(gold):
    _require(isinstance(gold, dict), "gold must be an object")
    _require(all(key in gold for key in ("value", "unit", "family", "pages")), "gold is missing required fields")
    dimension, _ = _unit(gold["unit"], "gold unit")
    _quantity(gold["value"], dimension, "gold value")
    _require(isinstance(gold["family"], str) and bool(gold["family"]), "gold family must be a nonempty string")
    pages = gold["pages"]
    _require(isinstance(pages, list) and bool(pages), "gold pages must be a nonempty list")
    for page in pages:
        _require(isinstance(page, dict), "gold page must be an object")
        for axis in ("width", "height"):
            _require(axis in page, "gold page is missing " + axis)
            _number(page[axis], "gold page " + axis)
            _require(page[axis] > 0, "gold page dimensions must be positive")
        _require(isinstance(page.get("space"), str) and page["space"] in SPACES, "gold page has unsupported space")
    alternatives = gold.get("alt_values", [])
    _require(isinstance(alternatives, list), "gold alt_values must be a list")
    for value in alternatives:
        _quantity(value, dimension, "gold alternative value")
    evidence = gold.get("evidence", [])
    _require(isinstance(evidence, list), "gold evidence must be a list")
    for element in evidence:
        _geometry(element, pages, "gold evidence")


def _validate_answer(answer, pages):
    _require(isinstance(answer, dict), "answer must be an object")
    _require(all(key in answer for key in ("value", "unit", "confidence", "evidence", "assumptions")),
             "answer is missing required fields")
    dimension, _ = _unit(answer["unit"], "answer unit")
    if answer["value"] is not None:
        _quantity(answer["value"], dimension, "answer value")
    _number(answer["confidence"], "answer confidence")
    _require(0 <= answer["confidence"] <= 1, "answer confidence must be in [0,1]")
    _require(isinstance(answer["assumptions"], list) and
             all(isinstance(item, str) for item in answer["assumptions"]),
             "answer assumptions must be a list of strings")
    evidence = answer["evidence"]
    _require(isinstance(evidence, list) and len(evidence) <= MAX_EVIDENCE,
             "answer evidence must be a list with at most 32 boxes")
    seen = set()
    for element in evidence:
        _geometry(element, pages, "answer evidence", answer=True)
        identity = (element["page"], tuple(element["bbox"]))
        _require(identity not in seen, "answer evidence contains duplicate boxes")
        seen.add(identity)


def _value_score(answer, gold):
    if answer["value"] is None:
        return 0.0
    dimension, factor = UNITS[answer["unit"]]
    gold_dimension, gold_factor = UNITS[gold["unit"]]
    if dimension != gold_dimension:
        return 0.0
    if dimension == "count":
        # Integer arithmetic preserves off-by-one distinctions even above 2**53.
        actual = int(answer["value"])
        best = 0.0
        for target in [gold["value"]] + gold.get("alt_values", []):
            expected = int(target)
            difference = abs(actual - expected)
            best = max(best, 1.0 if difference == 0 else .5 if expected >= 10 and difference == 1 else 0.0)
        return best
    with localcontext() as context:
        context.prec = 50
        actual = Decimal(str(answer["value"])) * Decimal(factor)
        best = 0.0
        for target in [gold["value"]] + gold.get("alt_values", []):
            expected = Decimal(str(target)) * Decimal(gold_factor)
            difference = abs(actual - expected)
            if expected == 0:
                score = float(actual == 0)
            else:
                relative = difference / abs(expected)
                score = 1.0 if relative <= Decimal(".02") else 0.0 if relative >= Decimal(".15") else float((Decimal(".15") - relative) / Decimal(".13"))
            best = max(best, score)
        return best


def _hits(box, element):
    if box["page"] != element["page"]:
        return False
    x0, y0, x1, y1 = box["bbox"]
    if "point" in element:
        x, y = element["point"]
        return x0 <= x <= x1 and y0 <= y <= y1
    # Decimal avoids float underflow/overflow and preserves the inclusive .3 edge.
    with localcontext() as context:
        context.prec = 50
        a = [Decimal(str(n)) for n in box["bbox"]]
        b = [Decimal(str(n)) for n in element["bbox"]]
        overlap = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
        union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - overlap
        return union > 0 and overlap >= Decimal(".3") * union


def _evidence_score(answer, gold):
    boxes, annotations = answer["evidence"], gold.get("evidence", [])
    if not boxes:
        return 0.0
    if not annotations:
        return 1.0
    matches = [[_hits(box, element) for element in annotations] for box in boxes]
    coverage = sum(any(row[index] for row in matches) for index in range(len(annotations))) / len(annotations)
    irrelevant = sum(not any(row) for row in matches) / len(boxes)
    return max(0.0, coverage - irrelevant)


def score_answer(answer: object, gold: dict) -> dict:
    """Validate and score a submission without network, files, or side effects.

    Unknown units and malformed contracts fail closed. A known but wrong unit
    dimension remains a valid wrong answer. Explicit null value is abstention.
    Duplicate or page-filling (>90% area) submission boxes invalidate the answer.
    Annotated evidence credit is coverage minus the fraction of irrelevant
    boxes, clamped to [0,1], and then multiplied by value_score.
    """
    mode = "structural"
    try:
        _validate_gold(gold)
        mode = "annotated" if gold.get("evidence") else "structural"
        _validate_answer(answer, gold["pages"])
        value = _value_score(answer, gold)
        evidence = _evidence_score(answer, gold) * value
        calibration = 1 - (answer["confidence"] - int(value >= .99)) ** 2
        components = {"value": WEIGHTS["value"] * value,
                      "evidence": WEIGHTS["evidence"] * evidence,
                      "calibration": WEIGHTS["calibration"] * calibration}
        return {"reward": min(1.0, max(0.0, sum(components.values()))),
                "value_score": value, "evidence_score": evidence,
                "calibration_score": calibration, "components": components,
                "valid": True, "errors": [], "evidence_mode": mode}
    except (ValueError, TypeError, OverflowError) as error:
        return invalid_result(error, mode)
