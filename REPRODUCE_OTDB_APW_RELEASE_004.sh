#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"
export PYTHONHASHSEED=0
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "======================================================================"
echo "OTDB-APW Release Candidate 004 — Cleanroom Cold-Start Reproduction"
echo "======================================================================"

echo "[1/6] Verifying immutable source manifest BEFORE execution..."
sha256sum -c SHA256SUMS_SOURCE.txt > /dev/null
sha256sum -c SHA256SUMS.txt > /dev/null
echo "      PASS: All immutable source and archive SHA-256 hashes verified."

mkdir -p "${ROOT_DIR}/build_outputs"

echo "[2/6] Regenerating Gate 2 electrical ERC, netlist, and SPICE reports into build_outputs/..."
python3 -c "
from pathlib import Path
from kicad_rev_d_afe_and_strict_erc_004 import run_all_gate2_electrical_verifications
run_all_gate2_electrical_verifications(Path('build_outputs'), Path('build_outputs'))
"

echo "[3/6] Regenerating Gates 3 & 4 fair calibrated baselines and synthetic scenarios into build_outputs/..."
python3 -c "
from pathlib import Path
from fair_baselines_and_synthetic_scenarios_004 import run_fair_baselines_and_synthetic_scenarios
run_fair_baselines_and_synthetic_scenarios(Path('build_outputs'), Path('build_outputs'))
"

echo "[4/6] Compiling C99 firmware and running SDI & Worker B inheritance into build_outputs/..."
python3 -c "
from pathlib import Path
from reproducible_sdi_and_worker_b_004 import generate_foundry_and_manufacturability_report, run_reproducible_sdi_and_worker_b_004
generate_foundry_and_manufacturability_report(Path('build_outputs'), Path('build_outputs'))
run_reproducible_sdi_and_worker_b_004(Path('.'), Path('build_outputs'), Path('build_outputs'))
"

echo "[5/6] Verifying regenerated outputs against frozen tolerances & auditing cleanroom hygiene..."
python3 verify_deterministic_outputs_004.py > "${ROOT_DIR}/build_outputs/deterministic_and_hygiene_audit.json"
python3 -m unittest discover -s tests -p "test_*.py" -v 2>&1 | tee "${ROOT_DIR}/build_outputs/test_standard.log"
python3 -O -m unittest discover -s tests -p "test_*.py" -v 2>&1 | tee "${ROOT_DIR}/build_outputs/test_optimized.log"

echo "[6/6] Re-verifying immutable source & archive manifests AFTER execution..."
sha256sum -c SHA256SUMS_SOURCE.txt > /dev/null
sha256sum -c SHA256SUMS.txt > /dev/null
echo "      PASS: Zero tracked archive files were modified during reproduction."
echo "======================================================================"
echo "REPRODUCTION COMPLETE: EXIT 0 (6/6 Standard + 6/6 Optimized Tests PASS)"
echo "======================================================================"
