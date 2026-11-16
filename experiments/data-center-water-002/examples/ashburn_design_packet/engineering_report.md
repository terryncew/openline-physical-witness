# Engineering Design & Public-Benefit Accountability Report — ASHBURN_VA_10MW_AI_CLUSTER

- **Receipt SHA-256**: `91dd29bbe3c32143648bb7ad6d58bdaf4377a0c1c0958f44d45b688ec9c5e1a7`
- **Epistemic Status**: `SOLUTIONS_ENGINEERED_MODELED_ONLY_NO_ACTUATION` (All water/energy/cost reductions below are modeled from supplied inputs, NOT observed field savings.)

## 1. S1 — Chemistry-Bounded Cooling-Tower Optimizer (vs. DOE FEMP BMP #10)
- **Classification**: `OPEN_IMPLEMENTATION_OF_DOE_FEMP_AND_EPA_WATERSENSE_BEST_PRACTICE`
- **Selected Regime (`S1C_ACID_FEED_PLUS_SIDESTREAM_FILTRATION`)**: Max permissible CoC = `6.77` (bounded by `SILICA_CEILING`), reducing modeled site makeup by `16.19%` (`23,864,932 L/yr`) and providing `$67,413.76/yr` in modeled net operating savings (`CONDITIONAL_POSITIVE_MODELED_SAVINGS_REQUIRES_TARIFF_AND_CHEMISTRY_VERIFICATION`; not a measured outcome).

## 2. S2 — Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier

| Plant Architecture | Feasible | Pareto Optimal | Dry Share (%) | Site Makeup (L/yr) | Site + All Grid Water (L/yr) | Peak Cool (kW) | Annualized Cost ($/yr) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P0_EXISTING_WET_TOWER_BASELINE` | Yes | `False` | `0.0%` | `147,386,027` | `366,271,096` | `411.2` | `$896,031` |
| `P1_S1_TOWER_OPTIMIZER_ONLY` | Yes | `True` | `0.0%` | `123,521,094` | `342,406,163` | `411.2` | `$820,468` |
| `P2_HYBRID_DRY_WET_AT_CURRENT_RACK_LIMIT` | Yes | `True` | `92.94%` | `8,724,735` | `232,113,641` | `665.0` | `$607,973` |
| `P3_WARM_WATER_W40_HYBRID_DRY_WET` | Yes | `False` | `100.0%` | `0` | `223,910,141` | `762.2` | `$613,442` |
| `P4_ZERO_EVAP_DRY_PLUS_CHILLER_RETROFIT` | Yes | `True` | `100.0%` | `0` | `232,507,134` | `2,921.3` | `$1,381,591` |

## 3. S3 — Sensor/Observer Fisher-Information Gate
- **Decision**: `REFUSE_NEW_HARDWARE_EXISTING_TELEMETRY_SUFFICES`
- **Heat Balance Check**: $Q_{\text{elec,liquid}} = 8,500.0\text{ kW}$ vs. $Q_{\text{enthalpy}} = 8,484.4\text{ kW}$ ($z = 0.047$)
- **Custom $3\omega$+EIS Cartridge Accepted**: `False` (Not needed)

## 4. S4 — Water-Source Substitution (Potable vs. Reclaimed & Condensate)
- **Potable Freshwater Withdrawal**: `828,710 L/yr` (`-90.5%` vs. 100% potable)
- **Reclaimed Intake / AHU Condensate**: `4,696,025 L/yr` / `3,200,000 L/yr`
- **Site Evaporative Consumption**: `7,436,000 L/yr` (**0.0 L reduction from reclaimed substitution**—reclaimed water saves drinking water, not evaporation)

## 5. S5 — Grid Peak Mitigation & Ratepayer vs. Developer Cost Allocation
- **Contract boundary**: All developer contribution, take-or-pay and collateral protections are hypothetical contractual choices until executed and enforceable; the zero-risk table entries are CONDITIONAL, not observed.
- **Dispatch boundary**: A TES tank size or proposed peak reduction is not chronological proof of charge/recharge or grid coincident demand reduction.
- **Facility Peak Demand**: `10,665.0 kW` $\to$ `10,665.0 kW` (via `0.0 kW` 4-hr Thermal Storage shave)

| Finance & Tariff Structure | Who Pays Grid Upgrade | Upfront Ratepayer Exposure ($) | Stranded Ratepayer Risk at Yr 6 ($) | Public Fiscal NPV ($) | Ratepayer Shift Flag |
| --- | --- | --- | --- | --- | --- |
| `ALLOC_A_CONVENTIONAL_SOCIALIZED_TARIFF_AND_ABATEMENT` | General Utility Ratepayers (socialized into rate base) | `$22,000,000` | `$12,100,000` | `$-2,717,159` | `True` |
| `ALLOC_B_DEVELOPER_CIAC_AND_85PCT_TAKE_OR_PAY` | Data-Center Developer (100% CIAC + collateralized take-or-pay) | `$0` | `$0` | `$29,762,646` | `True` |
| `ALLOC_C_THERMAL_STORAGE_PEAK_SHAVE_PLUS_TAKE_OR_PAY` | Data-Center Developer (downsized upgrade + TES peak shave) | `$0` | `$0` | `$29,762,646` | `True` |

## 6. S6 — Waste-Heat Reuse Feasibility Gate
- **Decision**: `GO_VIABLE_PROXIMATE_HEAT_REUSE` (Feasible: `True`, NPV: `$3,742,820`)

## 7. Public-Benefit Summary for Residents & Officials
- **What is promised vs. modeled**: Any claim that novel software or a cold-plate sensor alone cuts facility water by 70% is **rejected**; large site-water reductions require physical dry/hybrid heat rejection (`S2`), water-chemistry-bounded cycles of concentration (`S1`), or reclaimed water substitution (`S4`).
- **Who bears the infrastructure risk**: A fully executed, enforceable, collateralized developer CIAC/take-or-pay arrangement (`ALLOC_B` / `ALLOC_C`) could contractually transfer upgrade risk. The table's zero-risk outcomes are CONDITIONAL scenarios, not proof such contracts exist or eliminate all stranded costs.
