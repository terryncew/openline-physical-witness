# OpenLine Sensors — Data-Center Water Audit (public research candidate)

**Free, offline, read-only software. No API key, cloud account, paid dependency, or hardware needed.**

This tool helps engineers, researchers, journalists, and community reviewers distinguish **measured data-center water use** from modeled scenarios. It is not a physical sensor, control system, certified water-saving product, or proof that OpenLine saves water.

### Use it

With Python 3.10+:

```sh
python3 water_audit.py audit data/constructed_example.csv
python3 water_audit.py audit data/constructed_example.csv --grid-l-per-kwh 1.5
python3 water_audit.py scenario data/constructed_scenarios.json
python3 -m unittest discover -s tests -v
```

The included CSV and JSON are **fully constructed**, not measured from any data center. Input fields for `audit`:

| Field | Unit | Required evidence |
| --- | --- | --- |
| timestamp_utc | ISO 8601 UTC timestamp | monotonically increasing |
| duration_h | hours per measurement interval | 0 < h ≤ 24 |
| it_kw | average IT power | strictly positive |
| cooling_kw | average cooling electricity | nonnegative |
| makeup_l | metered freshwater / nonpotable makeup volume | nonnegative |
| blowdown_l | metered wastewater discharge from tower | nonnegative, ≤ makeup |

Use *measured* interval totals. `site_wue_makeup_l_per_it_kwh` = metered makeup / IT kWh. `makeup - blowdown` is only a **rough proxy**, not verified actual consumptive use: tank inventory changes, drift, leakage, reuse, and unmetered discharges may break the identity. Grid-water intensity is an explicit **user-supplied scenario**; the tool does not know your grid mix.

The scenario calculator makes assumptions visible. For cooling-tower evaporation E and concentration cycles C>1, a simplified steady-state relation gives M = E*C/(C-1) and blowdown B = E/(C-1), assuming negligible drift and stable inventory. **Dry cooling share, cycles of concentration, and heat rejection technology are engineering choices, not outcomes of sensor software.** Its environmental results are illustrative, with no thermodynamic/thermal-safety certification or chemistry safety model.

### Boundaries and failure modes

- Read-only outputs: the tool neither connects to BMS/CDU systems nor changes any setpoints.
- No measured water savings or independent facility pilot; no physical prototype and no measured cold-plate diagnostic advantage.
- Reported modeled ~70% site makeup reduction from the earlier private Sensors 002 comparison was primarily due to changes in cooling plant design, not a verified advantage of OpenLine. A matched hardware/sensor comparison produced zero additional modeled water savings.
- Site makeup (withdrawals) and source-electricity water (regional scenario) are **different accounting boundaries**; don't relabel either as total water consumption.
- No independent guarantee of water chemistry, GPU thermal headroom, safe control, tariff, carbon, or regional watershed impact.
- This is a research and public-accountability starting point. Bring actual facility data, independently verify units and meters, test a strong conventional baseline, and submit corrections.

### What would change the verdict

A controlled before/after or matched-period shadow-mode study showing a *new, useful measurement-informed decision* that reduces **verified net water consumption** without unacceptable energy, equipment or reliability penalty. A qualified facility owner must authorize any operational experiment.

### Prior work / evidence

- [Berkeley Lab, 2024 US Data Center Energy Usage Report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report).
- [Open Compute Project: Cooling Environments](https://www.opencompute.org/projects/cooling-environments/).
- [Public OpenLine Sensors membrane/Physical Witness research](https://github.com/terryncew/openline-physical-witness).
- Independent Source Audit 002 is retained privately; headline simulated savings are excluded from public performance claims.

This research is provided without warranty and is **not for live cooling system or safety-critical operation**.
