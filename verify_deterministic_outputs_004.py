#!/usr/bin/env python3
"""
OTDB-APW Release Repair 004 — Deterministic Output & Cleanroom Hygiene Verifier
(`verify_deterministic_outputs_004.py`).
1. Compares regenerated JSON outputs in `build_outputs/` against frozen reference reports in `artifacts/`
   within strict numerical tolerance (`1e-12`).
2. Scans every file in the public release tree to enforce Gate 5 cleanroom hygiene:
   - Zero ASCII control characters (`0x00-0x08`, `0x09` tab in prose/code, `0x0B` vertical tab, `0x0C`, `0x0E-0x1F`)
   - Zero private emails, internal Google Drive/Docs links, or machine-local `/working_dir` paths
   - Zero bundled `.onnx` model weights or unrelated `capabilities_007_008_v2` subtrees
   - Zero claims of `"LBNL operando benchmark"` or `"validated by LBNL"`
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


COMPARE_JSON_FILES = [
    "GATE2_ELECTRICAL_AND_ERC_REPORT_004.json",
    "GATE3_GATE4_FAIR_SYNTHETIC_BENCHMARK_REPORT_004.json",
    "MANUFACTURABILITY_AND_FOUNDRY_HOLD_REPORT_004.json",
    "MEMS_DRC_AND_LAYOUT_REPORT.json",
    "PEEK_FLOW_CELL_CAD_REPORT.json",
    "REPRODUCIBLE_SDI_BENCHMARK_004.json",
    "WORKER_B_INHERITANCE_REPORT_004.json",
]

TEXT_EXTENSIONS = {".py", ".md", ".json", ".c", ".h", ".cir", ".kicad_sch", ".net", ".cff", ".txt", ".toml", ".sh"}

FORBIDDEN_PATTERNS = [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"drive\.google\.com",
    r"docs\.google\.com",
    r"/working_dir/",
    r"LBNL operando benchmark",
    r"validated by LBNL",
    r"evaluated by LBNL",
]


def _compare_values(a: Any, b: Any, path: str, diffs: list[str], rel_tol: float = 1e-12, abs_tol: float = 1e-12) -> None:
    if isinstance(a, float) or isinstance(b, float):
        try:
            fa, fb = float(a), float(b)
            if not math.isclose(fa, fb, rel_tol=rel_tol, abs_tol=abs_tol):
                diffs.append(f"{path}: float mismatch {fa} vs {fb}")
        except (TypeError, ValueError):
            diffs.append(f"{path}: non-numeric mismatch {a!r} vs {b!r}")
        return
    if type(a) is not type(b):
        diffs.append(f"{path}: type mismatch {type(a).__name__} vs {type(b).__name__}")
        return
    if isinstance(a, dict):
        keys_a, keys_b = set(a.keys()), set(b.keys())
        if keys_a != keys_b:
            diffs.append(f"{path}: dict keys mismatch {sorted(keys_a ^ keys_b)}")
            return
        for k in sorted(keys_a):
            _compare_values(a[k], b[k], f"{path}.{k}", diffs, rel_tol, abs_tol)
        return
    if isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length mismatch {len(a)} vs {len(b)}")
            return
        for idx, (va, vb) in enumerate(zip(a, b)):
            _compare_values(va, vb, f"{path}[{idx}]", diffs, rel_tol, abs_tol)
        return
    if a != b:
        diffs.append(f"{path}: value mismatch {a!r} vs {b!r}")


def verify_regenerated_outputs(root_dir: Path) -> dict[str, Any]:
    artifacts_dir = root_dir / "artifacts"
    build_dir = root_dir / "build_outputs"
    diffs: list[str] = []
    exact_hash_matches = 0

    for fname in COMPARE_JSON_FILES:
        ref_p = artifacts_dir / fname
        gen_p = build_dir / fname
        if not ref_p.exists():
            diffs.append(f"Missing reference file: {ref_p.name}")
            continue
        if not gen_p.exists():
            diffs.append(f"Missing regenerated file: {gen_p.name}")
            continue
        ref_bytes = ref_p.read_bytes()
        gen_bytes = gen_p.read_bytes()
        if hashlib.sha256(ref_bytes).hexdigest() == hashlib.sha256(gen_bytes).hexdigest():
            exact_hash_matches += 1
        ref_obj = json.loads(ref_bytes.decode("utf-8"))
        gen_obj = json.loads(gen_bytes.decode("utf-8"))
        _compare_values(ref_obj, gen_obj, fname, diffs)

    return {
        "compared_json_count": len(COMPARE_JSON_FILES),
        "exact_byte_hash_matches": exact_hash_matches,
        "tolerance_diffs": diffs,
        "all_within_tolerance": len(diffs) == 0,
    }


def audit_cleanroom_hygiene(root_dir: Path) -> dict[str, Any]:
    violations: list[str] = []
    scanned_files = 0

    for p in sorted(root_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root_dir).as_posix()
        if rel.startswith("build_outputs/") or "__pycache__" in rel or rel.startswith(".git/"):
            continue
        if p.suffix.lower() == ".onnx":
            violations.append(f"Forbidden ONNX model weight found in public RC: {rel}")
        if "capabilities_007_008" in rel or "evidence_008" in rel or "workspace_handoff" in rel:
            violations.append(f"Forbidden private autonomy subtree found in public RC: {rel}")

        if p.suffix.lower() in TEXT_EXTENSIONS or p.name in ("LICENSE", "SHA256SUMS.txt", "SHA256SUMS_SOURCE.txt"):
            scanned_files += 1
            txt = p.read_text(encoding="utf-8")
            # Check for control characters (< 32 except \n and \r)
            bad_ctrl = sorted({hex(ord(c)) for c in txt if ord(c) < 32 and c not in ("\n", "\r")})
            if bad_ctrl:
                violations.append(f"{rel}: contains literal control characters {bad_ctrl}")
            # Skip self-reference in verifier/test files when checking forbidden regex literals
            if p.name not in ("verify_deterministic_outputs_004.py", "test_otdb_apw_release_004.py"):
                for pat in FORBIDDEN_PATTERNS:
                    if re.search(pat, txt, flags=re.IGNORECASE):
                        violations.append(f"{rel}: matched forbidden pattern {pat!r}")

    # Check canonical Apache-2.0 LICENSE length and Abstract word count
    lic_p = root_dir / "LICENSE"
    if not lic_p.exists() or lic_p.stat().st_size < 9000:
        violations.append("LICENSE file is missing or shorter than canonical Apache-2.0 text (<9,000 bytes).")

    abs_p = root_dir / "ABSTRACT_200_WORDS.md"
    abstract_word_count = 0
    if not abs_p.exists():
        violations.append("ABSTRACT_200_WORDS.md is missing.")
    else:
        lines = [ln.strip() for ln in abs_p.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
        words = " ".join(lines).split()
        abstract_word_count = len(words)
        if abstract_word_count > 200 or abstract_word_count < 80:
            violations.append(f"ABSTRACT_200_WORDS.md word count ({abstract_word_count}) outside [80, 200] range.")

    return {
        "scanned_text_files": scanned_files,
        "abstract_word_count": abstract_word_count,
        "violation_count": len(violations),
        "violations": violations,
        "cleanroom_hygiene_passed": len(violations) == 0,
    }


def verify_source_manifest(root_dir: Path, manifest_name: str = "SHA256SUMS_SOURCE.txt") -> dict[str, Any]:
    manifest_p = root_dir / manifest_name
    if not manifest_p.exists():
        return {"passed": False, "checked": 0, "mismatches": [f"Missing {manifest_name}"]}
    mismatches: list[str] = []
    checked = 0
    for line in manifest_p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected_sha, rel_path = line.split(None, 1)
        rel_path = rel_path.lstrip("*").strip()
        fp = root_dir / rel_path
        if not fp.exists():
            mismatches.append(f"Missing file: {rel_path}")
            continue
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        checked += 1
        if actual_sha != expected_sha:
            mismatches.append(f"SHA256 mismatch on {rel_path}: expected {expected_sha}, got {actual_sha}")
    return {
        "manifest": manifest_name,
        "checked_files": checked,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "passed": len(mismatches) == 0 and checked > 0,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    out_check = verify_regenerated_outputs(root)
    hyg_check = audit_cleanroom_hygiene(root)
    src_check = verify_source_manifest(root, "SHA256SUMS_SOURCE.txt")
    summary = {
        "deterministic_output_check": out_check,
        "cleanroom_hygiene_check": hyg_check,
        "source_manifest_check": src_check,
    }
    print(json.dumps(summary, indent=2))
    if not (out_check["all_within_tolerance"] and hyg_check["cleanroom_hygiene_passed"] and src_check["passed"]):
        sys.exit(1)
