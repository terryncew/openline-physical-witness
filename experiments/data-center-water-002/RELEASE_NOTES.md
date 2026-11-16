## Independent audit update — candidate 0.2.1

GPT-6 reproduced Argon’s 21/21 standard and optimized tests on the exact RC 0.2 ZIP, then found two untested boundary failures: an accepted 2.30 L/kWh_th evaporation coefficient above the stated 1.55 ceiling, and hidden generator truth (`reg`) used by the static benchmark comparator. Corrected both. Added two adversarial tests. All simulation results remain hypothetical and field savings unverified.

# OpenLine Sensors — public research candidate 0.2

**Research / reproducibility release, not a validated performance release.**

Scope: one dependency-free, Python 3.10+ command-line instrument (`water_audit.py`) that audits user-supplied CSV water and energy totals (with unit/column mapping for gallons, m3, MW, and reclaimed water, plus First-Law thermodynamic leak/anomaly checks), one transparent steady-state scenario model with orthogonal plant-vs-sensor attribution and grid EWIF crossover bounds, one matched-plant diagnostic comparator (`compete`) and pre-hardware engineering matrix (`hardware-matrix`), explicitly constructed fixtures plus a public literature benchmark catalog (`data/public_literature_benchmarks.json`), and 21 independent negative/unit tests. No external calls, credentials, remote telemetry, actuation, hardware construction, or downloadable private research archives.

Tested: Python 3.10+ normal and `-O` optimized mode, 21/21 tests each (`0` ResourceWarnings). Validated source file hash in each CSV audit result.

Deliberately excluded: 70.2% water savings as an OpenLine effect; $353k-$420k claimed earnings; 98.33% real-world fault identification; unattended cooling-system control; non-reproducible customer reports. See `CHANGELOG.md` for the complete VERIFIED / MODELED / REJECTED / UNTESTED disposition table.
