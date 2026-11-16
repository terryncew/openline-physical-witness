### Independent verification correction (0.2.1, 2026-11-16)
- Independently falsified RC 0.2's physics cap: 2.30 L/kWh_th passed the scenario engine despite its own 1.55 L/kWh_th ceiling; now rejected.
- Removed direct hidden ground-truth (`reg`) use from the static benchmark comparator. It now takes *only* sensor readings. This was oracle leakage, not a valid comparator.
- Explicitly labeled matched-plant experiments as constructed, same-source and not an independent blinded holdout.
- Added two regression tests. No actual savings, sensor win, or operational qualification is claimed.

# Candid Changelog & Claim Disposition Ledger (`CHANGELOG.md`)

## Version 0.2 (2026-11-16 — Branch `research/data-center-water-audit-001`)

### 1. Evidenced Software & Physics Repairs over Candidate 0.1 (`c265a546...`)
- **Fixed Boolean-to-Float Coercion (`EvidenceError`)**: `evaluate_scenario()` and `audit()` previously allowed Python `bool` values (`True -> 1.0`, `False -> 0.0`) via `float()`. Booleans are now explicitly rejected.
- **Fixed Ragged CSV Row Acceptance (`EvidenceError`)**: `audit()` now rejects CSV rows with extra unquoted commas (`None` key in `csv.DictReader`), missing cells, duplicate headers, or leading spreadsheet formula injection characters (`=`, `+`, `@`).
- **Enforced First-Law Thermodynamic Latent-Heat Bounds & Drift Mass Balance**: `evaluate_scenario()` now rejects unphysical evaporation coefficients (`> 2.50 L/kWh_th`, vs. theoretical pure latent evaporation `~1.481 L/kWh_th`), models tower drift displacement ($B = E/(\text{CoC}-1) - D$ per [Zenodo 10.5281/zenodo.23246001](https://zenodo.org/doi/10.5281/zenodo.23246001)), decomposes plant-design vs. chemistry vs. sensor attribution (`attribution_decomposition_l_model`), and computes the exact grid water intensity crossover (`EWIF*`).
- **Added User CSV Unit/Column Adapter & Thermodynamic Anomaly Flags**: Added `--map`, `--water-unit` (`l`, `gal`, `m3`, `kl`, `ccf`), `--power-unit` (`kw`, `mw`, `w`), `--grid-range`, optional `reclaimed_l` accounting, `covered_window_end_utc`, and interval anomaly flags (`THERMODYNAMIC_EVAP_CEILING_EXCEEDED`, `SCALING_RISK_HIGH_IMPLIED_COC`, `LOW_IMPLIED_COC_ONCE_THROUGH_OR_STUCK_BLOWDOWN`).
- **Added Matched-Plant Sensor Competition (`compete`) & Pre-Hardware Matrix (`hardware-matrix`)**: Demonstrates that on an equally equipped plant, competent passive energy-balance FDD (`Incumbent_B`) ties active ABA perturbation (`Candidate_C`) on `100.0%` of normal, single-sensor-drift, and unconfounded-fouling trials (`0.0 L` water delta), with active/reference sensing only separating simultaneous collinear multi-sensor drift + bypass/fouling confounders in simulation.

### 2. Independent Claim Disposition Table (`VERIFIED` / `MODELED` / `REJECTED` / `UNTESTED`)

| Prior Claim or Component | Disposition | Evidence & Boundary |
| --- | --- | --- |
| **Offline CSV & JSON water/energy audit CLI (`water_audit.py`, 21/21 standard & `-O` tests)** | **VERIFIED (Software Logic Only)** | Reproducible with Python 3.10+ standard library; rejects malformed, overlapping, ragged, boolean, and unphysical inputs fail-closed. |
| **70.2% site-water reduction as an OpenLine sensor breakthrough (Sensors 002)** | **REJECTED (Plant-Design Confounder)** | Ablation (`SENSORS_002_INDEPENDENT_ABLATION.py`) proved that holding `W40` warm-water, `CoC=8`, and hybrid dry-cooling constant on a healthy incumbent produces identical `46,487,615 L/yr` site water (`0 L` incremental OpenLine delta). |
| **$353k–$420k/yr net savings & 54.9% software-only water reduction (Sensors 002 Arm B)** | **REJECTED as Unconditional Software Gain / MODELED Scenario Only** | Assumed pre-existing uninstalled dry-cooler hardware; without dry-cooler hardware, modeled software/chemistry delta drops to `3.23%`, and all financial figures are unverified model assumptions. |
| **66.7% "combined water reduction" (Sensors 002)** | **REJECTED as Total Facility Water** | Excluded indirect grid water from IT server electricity (`87,600 MWh/yr`); including total IT + cooling grid electricity changes modeled reduction to `29.89%–34.30%` in thermoelectric grids (Ashburn/Phoenix/Austin). |
| **98.33% cold-plate fault accuracy & 1,950 GPU throttle hours avoided (Sensors 002)** | **MODELED (Synthetic Generator Only) / UNTESTED in Hardware** | Derived from synthetic trials parameterized around [Lee et al. (Nov 12, 2026)](https://www.mdpi.com/2072-666X/17/11/1312) 120h MEMS drift; competent passive energy-balance FDD ties active ABA on 100% of non-collinear trials. |
| **Custom $3\omega$ + EIS In-Line Microchannel Cartridge ($210k CapEx, Arm E / OTDB-APW)** | **REJECTED for Capital Spend / UNTESTED Physically** | Zero fabricated wafers, zero wet-lab hours, native KiCad ERC unrun, vulnerable to partial reference fouling without software screen, and saves `<1%` facility water standalone inside a closed TCS loop. |
| **COTS Sidestream Pt100 + Auto-Zero dP + EC Reference Kit ($292.40 BOM)** | **MODELED / NOT READY for Field Control** | Electrically valid COTS benchtop BOM (4x MAX31865 + TCA9548A), but unbuilt, uncalibrated on wet loops, and lacks industrial pressure/UL certification or installation labor pricing. |
| **97.5% HVAC economizer fault accuracy & $89.40 kit (Sensors 001)** | **REJECTED** | Relied on fixed 600 ppm $\text{CO}_2$ contrast (degraded to `76.3%` at 40 ppm contrast) and an incomplete 2-sensor unmultiplexed BOM. |
| **Zero-corruption water replay on 21 literature rows (Sensors 001 / 008)** | **REJECTED as Attested Field Proof / REPAIRED in Software** | Earlier `status_flag` label leak and hardcoded `0` counter repaired; literature rows lack attested reference sensor custody (`0/21` reference-verified). |
