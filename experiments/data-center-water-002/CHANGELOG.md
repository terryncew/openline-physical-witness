# Candid Changelog & Claim Disposition Ledger (`CHANGELOG.md`)

## Version 0.4.1-rc1 — GPT-6 independent source dogfood (2026-11-16)
- 50/50 tests normal and optimized (35 inherited + 15 independent); 400-case bounded chemistry stress test; clean-room extraction pending fresh-archive replay.
- Fixed overlapping constructed-weather bins, made provenance explicit, and reject more than one year of weather samples. Weather fixtures are **synthetic weighted bins**.
- Corrected S1's initially unsafe low-SiO2 concentration target; added no-valid-chemistry abstention; only credit sewer deductions after explicit utility eligibility.
- Removed automatic 35% TES and fractional IT-load peak savings without declared dispatch evidence; developer-paid upgrade/85% take-or-pay outcomes are **conditional contract scenarios**, never verified agreements.
- Excluded hypothetical W40 rack upgrades from cost-based Pareto selection until their capex and certification are declared.
- Reject non-boolean approval flags; refuse to substitute promised tax/jobs/infrastructure numbers for missing public disclosures; retain true documented zeros.
- Added canonical site and tariff hash checks for broader Decision Recall and labeled SHA-256 receipts as **unsigned content hashes**.
- Renamed S3 authority claims to **heuristic modeled sensor value**, not demonstrated Fisher rank or calibrated identification.
- Keep dry/chiller design inquiry available when wet-tower chemistry is missing, but reject unqualified wet plant operation.
- More transparent report/economic limitations and regenerated illustrative scenarios. No field savings or certifiable real-time control.

## Version 0.4.0-rc1 (2026-11-16 — Solutions Design Engine & Public-Benefit Accountability)

### 1. New Engineering Capabilities Built on Canonical `v0.2.1` (`23f3a182...`)
- **Added `solutions.py` & `water_audit.py design / claims / concepts` CLI**:
  - Implements `S1` (Chemistry-Bounded Cooling-Tower Optimizer vs. DOE FEMP BMP #10 / EPA WaterSense Sec 6.3), `S2` (Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier), `S3` (Fisher-Information Sensor/Observer Gate), `S4` (Reclaimed & Condensate Water-Source Substitution), `S5` (4-Hr Thermal Storage Peak Shaving & 3 Ratepayer/Developer Cost Allocations), `S6` (Waste-Heat Reuse Feasibility Gate), and `S7` (Cryptographic Assumption Receipts & Automatic Decision Recall).
  - Generates the 5 required design artifacts (`candidate_solutions.json`, `ranked_pareto.csv`, `engineering_report.md`, `assumption_receipts.json`, `equipment_boundary.md`) plus 3 worked engineering concept packets (`concepts`) and a promised-vs-documented public claims auditor (`claims`).
  - Preserves all `23/23` unit tests from `v0.2.1` untouched and adds `12/12` new adversarial and cross-climate transfer tests in `tests/test_solutions_004.py` (`35/35` total tests passing in standard and `-O` Python with `0` `ResourceWarning`s).

## Version 0.2.1 (2026-11-16 — GPT-6 Independent Corrections on Candidate 0.2)
- Enforced `MAX_SCENARIO_EVAP_COEFF_L_PER_KWH_TH = 1.55` in `evaluate_scenario()` to match `audit()`'s First-Law thermodynamic ceiling.
- Extracted `classify_static_mems_threshold(mems_dt, mems_flow)` taking only the two observed numbers so the static comparator never receives ground-truth regime or fault flags.

## Version 0.2 (2026-11-16 — Branch `research/data-center-water-audit-001`)
- Fixed boolean-to-float coercion (`EvidenceError`), ragged CSV row acceptance (`None` key in `csv.DictReader`), and spreadsheet formula injection (`=`, `+`, `@`).
- Added `--map`, `--water-unit` (`l`, `gal`, `m3`, `kl`, `ccf`), `--power-unit` (`kw`, `mw`, `w`), optional `reclaimed_l`, `--grid-range`, drift mass-balance displacement ($B = E/(\text{CoC}-1) - D$ per [Zenodo 10.5281/zenodo.23246001](https://zenodo.org/doi/10.5281/zenodo.23246001)), and orthogonal plant-vs-sensor attribution.

### Independent Claim Disposition Table (`VERIFIED` / `MODELED` / `REJECTED` / `UNTESTED`)

| Claim or Component | Disposition | Evidence & Boundary |
| --- | --- | --- |
| **Offline Audit & Solutions Design CLI (`water_audit.py` + `solutions.py`, 35/35 standard & `-O` tests)** | **VERIFIED (Software Logic Only)** | Reproducible with Python 3.10+ standard library; passes all 23 `v0.2.1` tests and 12 `v0.4.0` adversarial/transfer tests (`0` `ResourceWarning`s). |
| **S1 Cooling-Tower Chemistry Optimizer (`S1A/S1B/S1C`)** | **MODELED (Open Implementation of DOE FEMP / EPA Best Practice)** | Reproduces [DOE FEMP BMP #10](https://www.energy.gov/cmei/femp/best-management-practice-10-cooling-tower-management) (`CoC 3->6` saves `20.0%` makeup) when chemistry permits, caps `CoC` at `3.63` in high-silica Phoenix water (`28 mg/L SiO2`), catches `>10%` mass-vs-conductivity leak mismatch ([EPA WaterSense Eq. 6-4 vs 6-5](https://www.epa.gov/system/files/documents/2023-05/ws-commercial-watersense-at-work_Section_6.3_Cooling_Towers.pdf)), and abstains when chemistry inputs are missing. |
| **S2 Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier** | **MODELED (Plant Engineering Simulation)** | Proves dry cooling cannot reject heat on $43\,^\circ\text{C}$ Phoenix summer hours at `W32` (`q_dry_kw = 0.0`), and shows that in high-EWIF PJM (`Ashburn`, $2.40\text{ L/kWh}$), zero-evap chiller retrofit (`P4`) is Pareto-dominated by `W40` hybrid cooling (`P3`) because chiller kWh consumes more river water at the power plant (`232.51M` vs `223.91M L/yr`). |
| **S3 Sensor/Observer Gate & Custom $3\omega$+EIS Cartridge ($210k CapEx)** | **REJECTED (Custom Cartridge) / MODELED (COTS & Passive FDD)** | Refuses extra hardware in well-instrumented plants (`Ashburn`) where passive energy-balance FDD suffices; rejects custom $3\omega$+EIS cartridge (`-$29,540/yr` net VoI) in favor of `$0` maintenance ABA steps or `$292.40–$1,490` COTS Pt100/auto-zero $\Delta P$ reference kits when uncalibrated cold-plate MEMS sensors are present. |
| **70.2% site-water reduction as an OpenLine sensor breakthrough (Sensors 002)** | **REJECTED (Plant-Design Confounder)** | Holding `W40` warm-water, `CoC=8`, and hybrid dry-cooling constant on a healthy incumbent produces identical site water (`0 L` sensor-only water delta). |
