from __future__ import annotations

import re


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    u = unit.strip()
    u = u.replace("μ", "u").replace("µ", "u")
    u = u.replace("／", "/").replace("升", "L")
    u = u.replace(" ", "")
    replacements = {
        "10^9/L": "10^9/L",
        "x10^9/L": "10^9/L",
        "10*9/L": "10^9/L",
        "109/L": "10^9/L",
        "10^12/L": "10^12/L",
        "x10^12/L": "10^12/L",
        "1012/L": "10^12/L",
        "umol/L": "umol/L",
        "μmol/L": "umol/L",
        "µmol/L": "umol/L",
        "mmol/L": "mmol/L",
        "mg/dL": "mg/dL",
        "g/L": "g/L",
        "U/L": "U/L",
        "IU/L": "U/L",
    }
    return replacements.get(u, u)


def convert_value(code: str, value: float | None, unit: str | None, target_unit: str | None) -> tuple[float | None, str | None, list[str]]:
    notes: list[str] = []
    if value is None:
        return None, target_unit or unit, notes
    u = normalize_unit(unit)
    target = normalize_unit(target_unit) or u
    if not u or not target or u == target:
        return value, target, notes

    # CREA creatinine: mg/dL -> umol/L; 1 mg/dL ≈ 88.4 umol/L
    if code == "CREA" and u.lower() == "mg/dl" and target == "umol/L":
        notes.append("CREA mg/dL 已按 1 mg/dL≈88.4 umol/L 换算")
        return round(value * 88.4, 3), target, notes
    if code == "CREA" and u == "umol/L" and target.lower() == "mg/dl":
        notes.append("CREA umol/L 已按 1 mg/dL≈88.4 umol/L 反向换算")
        return round(value / 88.4, 3), target, notes

    # BUN: mg/dL -> mmol/L; 1 mg/dL BUN ≈ 0.357 mmol/L
    if code == "BUN" and u.lower() == "mg/dl" and target == "mmol/L":
        notes.append("BUN mg/dL 已按 1 mg/dL≈0.357 mmol/L 换算")
        return round(value * 0.357, 3), target, notes

    # GLU glucose: mg/dL -> mmol/L; 1 mmol/L = 18.018 mg/dL
    if code == "GLU" and u.lower() == "mg/dl" and target == "mmol/L":
        notes.append("GLU mg/dL 已按 18.018 mg/dL≈1 mmol/L 换算")
        return round(value / 18.018, 3), target, notes

    notes.append(f"未配置 {code} 从 {u} 到 {target} 的换算，保留原始数值")
    return value, u, notes


def extract_reference_from_line(line: str) -> tuple[float | None, float | None, str | None]:
    patterns = [
        r"(?:参考|ref|reference)\s*[:：]?\s*([0-9.]+)\s*[-~—–]\s*([0-9.]+)\s*([A-Za-z0-9^/µμ.]+)?",
        r"\(([0-9.]+)\s*[-~—–]\s*([0-9.]+)\s*([A-Za-z0-9^/µμ.]+)?\)",
    ]
    for pat in patterns:
        m = re.search(pat, line, flags=re.IGNORECASE)
        if m:
            unit = normalize_unit(m.group(3)) if len(m.groups()) >= 3 else None
            return float(m.group(1)), float(m.group(2)), unit
    return None, None, None
