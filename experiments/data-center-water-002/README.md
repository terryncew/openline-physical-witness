# OpenLine Sensors — Data-Center Water Audit (public research candidate 0.2.1)

**Free, offline, read-only software. No API key, cloud account, paid dependency, or hardware needed.**

This tool helps engineers, researchers, journalists, and community reviewers distinguish **measured data-center water use** from modeled scenarios, convert and validate real utility/BMS exports, and separate cooling-plant design changes from sensor claims. It is not a physical sensor, control system, certified water-saving product, or proof that OpenLine saves water.

### Three Water Boundaries (Do Not Conflate Them)

1. **Technology Cooling System (TCS — Rack/CDU Closed Loop)**: Circulates treated water or propylene-glycol (`PG25`) between server cold plates and a Coolant Distribution Unit ([OCP Cooling Environments](https://www.opencompute.org/projects/cooling-environments/)). Because the TCS loop is closed, its circulation rate (e.g., $1.5\text{ L/min per kW}$) is **not** water consumption.
2. **Facility Water System (FWS — Cooling Tower / Adiabatic / Hybrid Heat Rejection)**: Rejects facility heat to the atmosphere. Cooling towers withdraw **makeup water** ($M$) to replace **evaporated water** ($E$, consumptive loss to air), **drift** ($D$), and **blowdown** ($B$, mineral-concentrated wastewater discharge). At steady state with Cycles of Concentration $C > 1$:
   $$M = E \frac{C}{C - 1}, \qquad B = \frac{E}{C - 1} - D$$
   Per [Zenodo DOI 10.5281/zenodo.23246001](https://zenodo.org/doi/10.5281/zenodo.23246001), drift leaves at circulating concentration and displaces blowdown one-for-one.
3. **Electricity Supply (Indirect Source Water)**: Thermoelectric power plants evaporate water to generate the electricity used by both **IT servers** and **cooling equipment** ([Shehabi et al., 2024 LBNL Report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report); [Guidi & Dominici, Aug 2026](https://www.researchgate.net/publication/408326368_The_hidden_water_geography_of_US_hyperscale_data_centers_in_the_AI_era)). Switching from evaporative cooling to dry cooling cuts onsite water ($M$) but can increase cooling electricity and upstream river/aquifer water consumption depending on the regional grid's water intensity ($\text{EWIF}$, $\text{L/kWh}$).

### One-Command Reproduction & Usage

With Python 3.10+ (standard library only):

```sh
python3 -m unittest discover -s tests -v && python3 -O -m unittest discover -s tests -v
python3 water_audit.py audit data/constructed_example.csv --grid-l-per-kwh 1.5
python3 water_audit.py audit data/newcomer_utility_export_gal.csv --map timestamp_utc=interval_start_utc,duration_h=hours,it_kw=it_load_mw,cooling_kw=cooling_load_mw,makeup_l=tower_makeup_gal,blowdown_l=tower_blowdown_gal,reclaimed_l=reclaimed_makeup_gal --water-unit gal --power-unit mw --grid-l-per-kwh 1.65 --grid-range 0.18,1.65,2.40
python3 water_audit.py scenario data/constructed_scenarios.json
python3 water_audit.py compete
python3 water_audit.py hardware-matrix
```

The included CSV and JSON fixtures are **explicitly constructed illustrations**, not measurements from a live data center.

| Field | Default Unit (`--water-unit` / `--power-unit`) | Required evidence & fail-closed checks |
| --- | --- | --- |
| `timestamp_utc` | ISO 8601 UTC timestamp | Strictly increasing, timezone-aware |
| `duration_h` | hours (`(0, 24]`) | Non-overlapping intervals; gaps tracked in `uncovered_gap_hours_between_rows` |
| `it_kw` | `kw` (or `mw`, `w`) | Strictly positive finite number (booleans/formulas rejected) |
| `cooling_kw` | `kw` (or `mw`, `w`) | Nonnegative finite number |
| `makeup_l` | `l` (or `gal`, `m3`, `kl`, `ccf`) | Nonnegative finite number |
| `blowdown_l` | `l` (or `gal`, `m3`, `kl`, `ccf`) | Nonnegative finite number, $\le \text{makeup\_l}$ |
| `reclaimed_l` *(optional)* | `l` (or `gal`, `m3`, `kl`, `ccf`) | Nonnegative finite number, $\le \text{makeup\_l}$; separates potable vs. non-potable intake |

### What `water_audit.py` Checks

- **Observed Interval Audit (`audit`)**: Computes metered site WUE (`site_makeup_l / it_kwh`), potable vs. reclaimed withdrawal share, observed PUE, exact covered window end (`covered_window_end_utc`), and **First-Law thermodynamic & mass-balance anomalies** (flagging intervals where $(M-B)/Q_{\text{rejected,kWh}} > 1.55\text{ L/kWh}_{\text{th}}$ due to basin leaks/overflow/meter faults, or where implied $M/B$ indicates scaling risk $>10$ or stuck blowdown $<1.5$).
- **Orthogonal Scenario Attribution (`scenario`)**: Decomposes modeled water differences into `dry_cooling_plant_attributed_delta_l`, `coc_chemistry_attributed_delta_l`, `evap_coeff_attributed_delta_l`, and `sensor_only_attributable_delta_l` (`0.0` when physical heat-rejection settings match), plus the exact grid water intensity crossover (`crossover_grid_ewif_l_per_kwh_where_energy_penalty_cancels_site_saving`).
- **Matched-Plant Sensor Competition (`compete`)**: Compares passive model-based FDD (`Incumbent_B_Competent_Passive_Energy_Balance_FDD`) against active perturbation (`Candidate_C`) and COTS reference sensing (`Candidate_D`) on identical plant hardware. Shows that **competent passive FDD ties active/reference sensing on `100.0%` of normal, single-sensor-drift, and unconfounded-fouling trials**, while active/reference sensing only changes the diagnosis under simultaneous collinear multi-sensor drift + bypass/fouling confounding (a computational result, unvalidated in the field).

### Independent adversarial recheck (0.2.1)

The 0.2 release candidate contained two research-validation defects. It accepted an evaporation scenario above the tool's own theoretical latent-heat ceiling and, in the weakest simulated benchmark arm, used a hidden fault label when constructing its classification. Both were corrected and covered by tests. **The whole matched-plant competition is still a constructed, builder-visible experiment, not a blinded independent evaluation or field measurement.** Its 100% figures must not be reported as deployed accuracy.

### Prior Work, Licensed References & Public Invitation

- [Berkeley Lab, 2024 U.S. Data Center Energy Usage Report (LBNL-2001637)](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report)
- [Guidi & Dominici (Aug 2026), The Hidden Water Geography of U.S. Hyperscale Data Centers in the AI Era](https://www.researchgate.net/publication/408326368_The_hidden_water_geography_of_US_hyperscale_data_centers_in_the_AI_era)
- [Lee et al. (Nov 12, 2026), Embedded Flexible MEMS Microsensor in a Liquid-Cooling Cold Plate for AI Servers, *Micromachines* 17(11), 1312](https://www.mdpi.com/2072-666X/17/11/1312)
- [LBNL Fault Detection and Diagnostics (FDD) Datasets (PMC10235024, CC BY 4.0)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10235024/)
- [Measurement Standard for Large Computational Loads (Zenodo DOI: 10.5281/zenodo.23246001)](https://zenodo.org/doi/10.5281/zenodo.23246001)
- [OpenLine Physical Witness Repository](https://github.com/terryncew/openline-physical-witness)

We invite engineers and researchers to challenge these models, submit reproducible corrections, or test the tool on **legally shareable, public-domain or open-licensed** datasets. **Never post confidential facility telemetry, credentials, or proprietary customer records.** Provided without warranty under Apache License 2.0 and **not for live cooling system or safety-critical operation**.
