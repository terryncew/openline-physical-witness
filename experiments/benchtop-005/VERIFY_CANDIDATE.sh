#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -v
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
gcc -std=c99 -Wall -Wextra -Werror -fsyntax-only firmware/otdb_apw_005_rp2040_firmware.c
gcc -std=c99 -Wall -Wextra -Werror -pedantic firmware/reference_guard.c tests/reference_guard_host_test.c -lm -o "$build_dir/guard_test"
gcc -std=c99 -Wall -Wextra -Werror -pedantic firmware/lockin_core.c tests/lockin_core_host_test.c -lm -o "$build_dir/lockin_test"
"$build_dir/lockin_test"
"$build_dir/guard_test"
gcc -std=c99 -Wall -Wextra -Werror -pedantic firmware/lockin_core.c tests/lockin_core_host_test.c -lm -o "$build_dir/lockin_test"
"$build_dir/lockin_test"
python3 tools/hardware_readiness.py --json
sha256sum -c SHA256SUMS.txt
echo 'PASS: offline software tests, model replay and source receipts. HARDWARE HOLD remains.'
