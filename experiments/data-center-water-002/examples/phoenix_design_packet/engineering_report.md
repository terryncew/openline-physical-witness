# Engineering Design & Public-Benefit Accountability Report — PHOENIX_AZ_10MW_AI_CLUSTER

- **Receipt SHA-256**: `9cfcb90705fd318c5ae3f07e90cf9ed94551bbf1a2292717e922c28b2e2b9a73`
- **Epistemic Status**: `SOLUTIONS_ENGINEERED_MODELED_ONLY_NO_ACTUATION` (All water/energy/cost reductions below are modeled from supplied inputs, NOT observed field savings.)

## 1. S1 — Chemistry-Bounded Cooling-Tower Optimizer (vs. DOE FEMP BMP #10)
- **Classification**: `OPEN_IMPLEMENTATION_OF_DOE_FEMP_AND_EPA_WATERSENSE_BEST_PRACTICE`
- **Selected Regime (`S1C_ACID_FEED_PLUS_SIDESTREAM_FILTRATION`)**: Max permissible CoC = `3.63` (bounded by `SILICA_CEILING`), reducing modeled site makeup by `1.41%` (`2,081,497 L/yr`) and providing `$-9,653.64/yr` in modeled net operating savings (`HOLD_NEGATIVE_MODELED_OPERATING_SAVINGS_REQUIRES_CHEMISTRY_SAFETY_REVIEW`; not a measured outcome).

## 2. S2 — Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier

| Plant Architecture | Feasible | Pareto Optimal | Dry Share (%) | Site Makeup (L/yr) | Site + All Grid Water (L/yr) | Peak Cool (kW) | Annualized Cost ($/yr) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P0_EXISTING_WET_TOWER_BASELINE` | Yes | `True` | `0.0%` | `147,386,027` | `279,629,089` | `411.2` | `$1,019,860` |
| `P1_S1_TOWER_OPTIMIZER_ONLY` | Yes | `True` | `0.0%` | `145,304,529` | `277,547,592` | `411.2` | `$1,021,363` |
| `P2_HYBRID_DRY_WET_AT_CURRENT_RACK_LIMIT` | Yes | `True` | `69.18%` | `44,785,643` | `179,309,253` | `653.5` | `$819,285` |
| `P3_WARM_WATER_W40_HYBRID_DRY_WET` | Yes | `False` | `79.45%` | `29,857,095` | `164,846,226` | `767.9` | `$809,370` |
| `P4_ZERO_EVAP_DRY_PLUS_CHILLER_RETROFIT` | Yes | `True` | `100.0%` | `0` | `151,683,019` | `3,552.3` | `$2,280,526` |

## 3. S3 — Sensor/Observer Fisher-Information Gate
- **Decision**: `SELECT_SINGLE_COST_POSITIVE_INTERVENTION`
- **Heat Balance Check**: $Q_{\text{elec,liquid}} = 8,500.0\text{ kW}$ vs. $Q_{\text{enthalpy}} = 8,484.4\text{ kW}$ ($z = 0.047$)
- **Custom $3\omega$+EIS Cartridge Accepted**: `False` (Custom 3-omega+EIS cartridge net VoI is $-29,540.00/yr (loses money due to $210,000 CapEx); COTS Sidestream 4-Wire Pt100 + 3-Way Auto-Zero dP + Conductivity Reference Kit achieves 5/5 identifiability with +$16,402.00/yr net VoI.)

## 4. S4 — Water-Source Substitution (Potable vs. Reclaimed & Condensate)
- **Potable Freshwater Withdrawal**: `6,650,346 L/yr` (`-85.15%` vs. 100% potable)
- **Reclaimed Intake / AHU Condensate**: `37,685,296 L/yr` / `450,000 L/yr`
- **Site Evaporative Consumption**: `32,448,000 L/yr` (**0.0 L reduction from reclaimed substitution**—reclaimed water saves drinking water, not evaporation)

## 5. S5 — Grid Peak Mitigation & Ratepayer vs. Developer Cost Allocation
- **Contract boundary**: All developer contribution, take-or-pay and collateral protections are hypothetical contractual choices until executed and enforceable; the zero-risk table entries are CONDITIONAL, not observed.
- **Dispatch boundary**: A TES tank size or proposed peak reduction is not chronological proof of charge/recharge or grid coincident demand reduction.
- **Facility Peak Demand**: `10,653.5 kW` $\to$ `10,653.5 kW` (via `0.0 kW` 4-hr Thermal Storage shave)

| Finance & Tariff Structure | Who Pays Grid Upgrade | Upfront Ratepayer Exposure ($) | Stranded Ratepayer Risk at Yr 6 ($) | Public Fiscal NPV ($) | Ratepayer Shift Flag |
| --- | --- | --- | --- | --- | --- |
| `ALLOC_A_CONVENTIONAL_SOCIALIZED_TARIFF_AND_ABATEMENT` | General Utility Ratepayers (socialized into rate base) | `$28,000,000` | `$15,400,000` | `$-24,646,462` | `True` |
| `ALLOC_B_DEVELOPER_CIAC_AND_85PCT_TAKE_OR_PAY` | Data-Center Developer (100% CIAC + collateralized take-or-pay) | `$0` | `$0` | `$19,282,841` | `True` |
| `ALLOC_C_THERMAL_STORAGE_PEAK_SHAVE_PLUS_TAKE_OR_PAY` | Data-Center Developer (downsized upgrade + TES peak shave) | `$0` | `$0` | `$19,282,841` | `True` |

## 6. S6 — Waste-Heat Reuse Feasibility Gate
- **Decision**: `NO_GO_NO_VIABLE_HEAT_OFFTAKER` (Feasible: `False`, NPV: `$0`)

## 7. Public-Benefit Summary for Residents & Officials
- **What is promised vs. modeled**: Any claim that novel software or a cold-plate sensor alone cuts facility water by 70% is **rejected**; large site-water reductions require physical dry/hybrid heat rejection (`S2`), water-chemistry-bounded cycles of concentration (`S1`), or reclaimed water substitution (`S4`).
- **Who bears the infrastructure risk**: A fully executed, enforceable, collateralized developer CIAC/take-or-pay arrangement (`ALLOC_B` / `ALLOC_C`) could contractually transfer upgrade risk. The table's zero-risk outcomes are CONDITIONAL scenarios, not proof such contracts exist or eliminate all stranded costs.
