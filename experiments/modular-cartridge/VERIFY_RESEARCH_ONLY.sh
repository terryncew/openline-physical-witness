#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c SHA256SUMS.txt
python3 -m unittest discover -s tests -v
python3 cad/cartridge_geometry.py >/dev/null
python3 tools/readiness_gate.py | grep -q 'HOLD_PRODUCTION'
python3 cost/economics.py | grep -q 'HOLD_NO_FIELD_ECONOMICS'
sha256sum -c SHA256SUMS.txt
printf 'Research geometry/economics/replay PASS. Hardware and production remain HOLD.\n'
