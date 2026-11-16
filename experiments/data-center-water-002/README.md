# OpenLine Sensors 004 — Data-Center Water, Power & Public-Benefit Solutions Design Engine (`v0.4.1-rc1 (independently challenged)`)

**Free, offline, vendor-neutral engineering design & audit software (Python 3.10+ standard library only, Apache-2.0).**

Extends `water_audit.py` (`v0.2.1`, 23/23 accepted tests) with `solutions.py` (`50/50` total unit and adversarial tests in standard and `-O` modes): an executable engineering design and competition engine that takes a proposed or operating data center's stated site conditions (`site.json`), weather (real chronological intervals or clearly constructed seasonal weighted bins) (`weather.csv`), utility tariffs and infrastructure costs (`tariff.json`), and optional meter logs (`telemetry.csv`), and outputs physics-screened **modeled** cooling/water/grid alternatives, Pareto frontiers, equipment boundaries, and public-benefit cost-incidence receipts.

### Independent closeout boundary (0.4.1)

The initial 0.4 engineering models are **not calibrated facility digital twins**. Independent dogfooding repaired overlapping and mislabeled synthetic weather, invalid chemistry setpoints, free thermal-storage peak credits, unauthorized sewer deductions, omitted rack-upgrade capital costs, signed-contract assumptions, missing public-disclosure fallbacks, and incomplete decision recall. All **50 tests** pass normal and optimized Python, plus a 400-case chemistry stress pass. No paid dependencies or live controls.

**Before using a financial or resource result:** require real chronological weather and load profiles (the included 4-bin seasonal fixtures are constructed), vendor capacity/fan/chiller curves, verified water chemistry, confirmed municipal sewer-deduct eligibility, certified rack temperatures and full retrofit CapEx, current utility tariffs, and enforceable agreements. Public NPV and potential savings are *what-if calculations*. There is **no observed water saving, field-tested sensor identifiability, guaranteed operating feasibility, verified take-or-pay contract, or qualified dispatch**. `S3` uses heuristic assumed fault avoidance rather than a calculated Fisher-information matrix. `S7` emits content hashes rather than cryptographically signed owner-authorization receipts.

The engine rejects wet-tower options when chemistry is missing but continues to compare an explicitly modeled dry/chiller alternative. A plant lacking certified rack-upgrade costs is excluded from cost-based selection. It does not purchase hardware, operate controls, or provide a permitting determination.

### One-Command Verification & CLI Usage

```sh
python3 -W error::ResourceWarning -m unittest discover -s tests -v
python3 -O -W error::ResourceWarning -m unittest discover -s tests -v

# 1. Engineer & compete S1-S7 solutions for an Arid High-Silica AI Cluster (Phoenix, AZ)
python3 water_audit.py design \
  --site data/site_phoenix_arid.json \
  --weather data/weather_phoenix_sample.csv \
  --tariff data/tariff_phoenix.json \
  --telemetry data/constructed_example.csv \
  --output-dir examples/phoenix_design_packet

# 2. Engineer & compete S1-S7 solutions for a Humid High-EWIF Cluster with District Heat Reuse (Ashburn, VA)
python3 water_audit.py design \
  --site data/site_ashburn_humid.json \
  --weather data/weather_ashburn_sample.csv \
  --tariff data/tariff_ashburn.json \
  --output-dir examples/ashburn_design_packet

# 3. Output the Three Complete Worked Engineering Concept Packets
python3 water_audit.py concepts

# 4. Audit Promised vs. Documented Public-Benefit & Ratepayer Claims
python3 water_audit.py claims --file data/public_claims_filing_sample.json

# 5. Retained v0.2.1 Observed CSV Audit, Scenario & Matched-Plant Sensor Competition Commands
python3 water_audit.py audit data/constructed_example.csv --grid-l-per-kwh 1.5
python3 water_audit.py scenario data/constructed_scenarios.json
python3 water_audit.py compete
python3 water_audit.py hardware-matrix
```

### The Seven Engineered Solutions (`S1–S7`) in `solutions.py`

1. **`S1` — Chemistry-Bounded Cooling-Tower Optimizer (vs. [DOE FEMP BMP #10](https://www.energy.gov/cmei/femp/best-management-practice-10-cooling-tower-management) & [EPA WaterSense Sec. 6.3](https://www.epa.gov/system/files/documents/2023-05/ws-commercial-watersense-at-work_Section_6.3_Cooling_Towers.pdf))**:
   - Computes both conductivity Cycles of Concentration ($\text{CoC}_{\text{EC}} = \sigma_B / \sigma_M$) and mass-balance Cycles ($\text{CoC}_{\text{mass}} = M / B$), flagging `epa_watersense_eq64_eq65_leak_or_drift_mismatch_detected` when they diverge by $>10\%$.
   - Bounds maximum permissible $\text{CoC}$ by amorphous silica ($\le 150\text{–}175\text{ mg/L}$), skin-temperature Langelier Saturation Index ($\text{LSI}$), calcium-alkalinity product, and chloride stress-corrosion limits. Abstains fail-closed (`ABSTAIN_REQUIRED_MEASUREMENTS_MISSING`) when water chemistry inputs are missing.
2. **`S2` — Weather-Constrained Dry/Hybrid Heat-Rejection Dispatch**:
   - Evaluates hour-by-hour thermodynamic feasibility across `P0` (Existing Wet Tower), `P1` (`S1` Tower Optimizer Only), `P2` (Hybrid Dry/Wet at Current Rack Limit), `P3` (Warm-Water `W40` Hybrid Dry/Wet), and `P4` (Zero-Evap Dry Cooler + Mechanical Chiller Trim).
   - Never assigns 100% dry capacity on hot hours by fiat; exposes the multi-objective **Pareto frontier** across site makeup water, total (site + upstream grid) water, peak electrical demand ($\text{kW}$), and annualized cost ($\$/\text{yr}$).
3. **`S3` — Heuristic Sensor/Observer & Modeled Value-of-Information Gate**:
   - Compares dual heat estimates ($\hat{Q}_{\text{elec,liquid}}$ vs. $\hat{Q}_{\text{enthalpy}} = \dot{m}c_p\Delta T$) and refuses new hardware (`REFUSE_NEW_HARDWARE_EXISTING_TELEMETRY_SUFFICES`) when calibrated redundant RTDs and differential pressure already exist. Rejects the `$210,000` custom $3\omega$+EIS microchannel cartridge on negative net Value of Information (`-$29,540/yr`).
4. **`S4` — Water-Source Substitution & Recovery**:
   - Models municipal reclaimed water and AHU coil condensate harvest, strictly preserving the physical law that **reclaimed water reduces potable freshwater withdrawal (`-30.9%` to `-85.2%`) without reducing site evaporative consumption (`0.0 L` evaporative delta)**.
5. **`S5` — Grid & Community Cost Mitigation**:
   - Represents 4-hour Thermal Energy Storage (TES) as a **candidate design**; assigns **zero effective reduction without declared storage/charging and dispatch evidence**, and does not establish a chronological storage dispatch and compares three project-finance cost allocations modeled on [LBNL Large-Load Rate Design (Aug 2026)](https://eta-publications.lbl.gov/sites/default/files/2026-08/rate_designs_large_loads_2026.08.10.pdf) and [PUCO / AEP Ohio Data Center Tariff Case No. 24-508](https://safeguard.sh/resources/blog/ohio-aep-data-center-tariff-85-percent-minimum-12-years-explained): `ALLOC_A` (Socialized Utility Upgrade + Unconditional Abatement), `ALLOC_B` (hypothetical Developer 100% CIAC + 12-Yr 85% Minimum Billing Demand Take-or-Pay), and `ALLOC_C` (TES Peak Shave + Downsized Upgrade + Take-or-Pay).
6. **`S6` — Waste-Heat Reuse Feasibility Gate**:
   - Computes Carnot-derated booster heat-pump $\text{COP}$ ([MDPI *Energies* 2026, 19(3), 800](https://www.mdpi.com/1996-1073/19/3/800)) and trenching/piping economics, rejecting sites without a proximate heat offtaker (`NO_GO_NO_VIABLE_HEAT_OFFTAKER` in Phoenix; `GO_VIABLE_PROXIMATE_HEAT_REUSE` with `+$3.74M` NPV in Ashburn).
7. **`S7` — Content-Hash Evidence & Advisory Decision Recall**:
   - Emits SHA-256 **content-hash** assumption receipts (not signatures or receiver authorization) (`assumption_receipts.json`) and reopens design conclusions when explicitly presented with changed source content (`REOPENED_BY_SOURCE_CHANGE`) when weather, makeup silica, rack thermal limits, or grid water intensity change.
