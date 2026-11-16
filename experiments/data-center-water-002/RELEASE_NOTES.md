# OpenLine Sensors 004 — Solutions Design Engine & Water Audit (private independent acceptance candidate 0.4.1-rc1)

**Engineering design, simulation, and accountability tool — not a certified live control system or field-validated savings claim.**

Scope: Extends canonical `openline-sensors-water-0.2.1` (`23f3a182...`, 23/23 tests) with `solutions.py` and `tests/test_solutions_004.py` (50/50 total standard and `-O` tests passing with 0 ResourceWarnings). Implements and competes all 7 engineering approaches (`S1` Chemistry-Bounded Tower Optimizer, `S2` Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier, `S3` Heuristic Sensor/Observer Gate, `S4` Reclaimed & Condensate Water Substitution, `S5` Conditional Thermal Storage Peak-Shaving Design & 3 Ratepayer/Developer Cost Allocations, `S6` Waste-Heat Reuse Feasibility Gate, and `S7` Assumption Receipts & Decision Recall), 3 complete worked engineering concept packets (`concepts`), and a promised-vs-documented public claims verifier (`claims`).


## Independent corrections in 0.4.1

The first 004 archive was **not** accepted solely on its passing 35 tests. GPT-6's independent check introduced 15 additional adversarial tests (50 total), including: overlapped constructed-weather intervals; unsafe high-silica concentration target; invented 35% thermal storage benefit without dispatch; sewer deductions without utility approval; missing W40 rack retrofit costs; unsigned take-or-pay agreements misreported as accomplished ratepayer protection; uncalibrated Fisher-information claims; changes to tariff/site inputs not triggering recall; documented zeros silently replaced by promised benefits; and string booleans pretending to be approval.

New model conclusions are different from earlier sample reports. Full demonstration packets have been regenerated and must not be compared as if equipment and tariff conditions were held constant. All resource and savings outputs are **modeled only**. In particular, the Phoenix tower's modeled chemistry treatment may be necessary but does not produce positive operating savings when sewer deductions are unapproved. Real engineering qualification remains open.

SHA-256 receipts are not signatures. Constructed seasonal weather bins are not actual weather stations or chronological control-ready records. This release is a **candidate** for public research code review, not a certified control system or equipment ordering package.
