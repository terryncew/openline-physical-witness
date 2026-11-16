#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v gcc >/dev/null
command -v python3 >/dev/null
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
for flags in '-O0' '-O2'; do
  gcc -std=c99 -Wall -Wextra -Werror -pedantic "$flags" -fsanitize=undefined -fno-sanitize-recover=all \
   firmware/triarm_witness.c tests/test_triarm_witness.c -lm -o "$build_dir/triarm"
  "$build_dir/triarm"
done
python3 models/observability_certificate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/hardware_hold.py
sha256sum -c SHA256SUMS.txt
printf '\nResearch software: PASS. Hardware readiness: HOLD. No measured field accuracy.\n'
