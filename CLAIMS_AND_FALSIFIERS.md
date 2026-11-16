# Exact Claims, Epistemic Separation & Pre-Registered Falsifiers (`CLAIMS_AND_FALSIFIERS.md`)

## 1. Five-Level Epistemic Separation
To prevent conflating simulation outputs with experimental sensor performance, every artifact in Release Candidate 004 is classified into one of five strict epistemic levels:

| Epistemic Level | What Is Established in Release 004 | What Is NOT Claimed |
| :--- | :--- | :--- |
| **Level 1: Analytical & Numerical Physics** | 1D/2D [Cahill $3\omega$ multilayer heat conduction](https://pubs.aip.org/aip/jap/article/138/21/211101/3374176/A-tutorial-on-the-3-method-for-measuring-thermal), 10-zone axial finite-volume + 64-node Cauer RC ladder, Bruggeman porous dielectric/thermal mixing, and 4x4 Schur-marginalized Fisher Information Matrix ($\lambda_{\min} = 366.08$). | Not a substitute for 3D turbulent multiphase CFD or physical wet-lab calibration. |
| **Level 2: Literature-Inspired Synthetic Scenarios** | Fair pre-calibrated comparison (`N_cal = 60`, `SHA-256: d393b92d...`) showing `B3` Multi-Sensor Fusion winning in constant-EC fouling (`0.67%` vs `3.96%`) and partial reference-arm fouling (`7.72%` vs `71.17%`), while `OTDB-APW Rev D` wins under unmeasured $1.35\times\text{--}2.15\times$ soluble CP (`8.17%` vs `43.31%`). | **NOT** empirical LBNL beamline data (`0` LBNL files ingested) and **NOT** measured commercial sensor precision. |
| **Level 3: CAD, Layout & Typed Schematic Design** | `otdb_apw_afe_rev_d.kicad_sch` (`41` symbols, `140` typed library pins, `204` placed pins across `52` nets, `0` programmatic ERC errors, `4/4` injected faults caught), `otdb_apw_rev_b.gds` (`0` Shapely geometric violations), and `otdb_apw_peek_flow_cell.stl`. | **NOT** native `kicad-cli` signed off (`HOLD_NATIVE_KICAD_CLI_ABSENT`) and **NOT** foundry PDK DRC signed off (`FOUNDRY_HOLD_1..6`). |
| **Level 4: Physical Prototype & Wet-Lab Validation** | **NONE (`0` wafers fabricated, `0` wet-lab hours, `USD 0.00` spent).** | No physical sensor precision, SNR, or durability has been experimentally measured. |
| **Level 5: Downstream Industrial Economics** | Modeled component cost (`USD 30.05` raw 1k BoM; `USD 348.00` slip-stream node; `USD 11,250` Phase-1 pilot estimate). | **NO** realized plant savings (`USD 683k-1.946M` scenario figures retired from public claims). |

## 2. Pre-Specified Physical Falsifiers (not externally registered)
The OTDB-APW physical hypothesis is **FALSIFIED** if any of the following occurs during Phase-1 wet-loop testing:
1. **Falsifier F1 (Soluble CP Rejection Failure)**: During a $1.8\times$ soluble NaCl boundary-layer step at $d_f = 0\,\mu\text{m}$ on a clean membrane mimic, `OTDB-APW Rev D` reports an apparent solid scale thickness $> 1.5\,\mu\text{m}$ or fails to outperform calibrated 4-frequency EIS + `Pt1000` (`B1`) and Multi-Sensor Fusion (`B3`) by at least $2.0\times$ RMSE across $d_f \in [2, 25]\,\mu\text{m}$.
2. **Falsifier F2 (Reference-Arm Shear-Step Failure)**: Optical profilometry or cross-sectional SEM after 48 hours of $\text{CaSO}_4 / \text{CaCO}_3$ scaling shows reference-arm thickness $d_{f,\text{ref}} > 0.15\,d_{f,\text{sense}}$, triggering the `NC5` partial reference-fouling loss regime (`71.17%` error).
3. **Falsifier F3 (Passivation Bilayer Delamination / Pinhole Breach)**: The $30\text{ nm }\text{Al}_2\text{O}_3 / 30\text{ nm }\text{HfO}_2$ ALD bilayer exhibits DC/low-frequency shunt resistance $R_{\text{shunt}} < 50\text{ M}\Omega$ within 60 days in $50\text{ mM NaCl}$ at $45\,^\circ\text{C}$.
