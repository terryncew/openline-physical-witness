# Blinded 48-Hour Wet-Loop & 60-Day Endurance Validation Protocol (`BLIND_LAB_TEST_PROTOCOL.md`)

**Status**: Prospective protocol for independent testing (not externally registered) (`0` physical wet-lab hours executed to date).
**Prior-Art Testbed Alignment**: Designed for compatibility with high-pressure crossflow cells such as [Nassr et al., *Rev. Sci. Instrum.* 96, 065209 (2025), DOI: 10.1063/5.0264117](https://pubs.aip.org/aip/rsi/article/96/6/065209/3350882/Crossflow-membrane-filtration-system-for-operando) and microfluidic impedimetric membrane-mimic cassettes such as [Khaja et al., *ACS Appl. Mater. Interfaces* 18, 25382–25395 (2026), DOI: 10.1021/acsami.5c26362](https://pmc.ncbi.nlm.nih.gov/articles/PMC13154124/).

## 1. Blinded 48-Hour Crossflow Fouling & Soluble CP Protocol (12 Randomized Dosing Windows)
1. **Independent Blinding Coordinator**: An experimentalist not involved in running the `OTDB-APW Rev D` inversion software prepares 12 randomized 4-hour fluid/foulant dosing windows across a 48-hour continuous slip-stream run ($u = 0.25\text{ m/s} \pm 18\%$, $T = 22\text{--}32\,^\circ\text{C}$, $P = 2.0\text{--}6.5\text{ bar}$):
   * **3 Pure Soluble CP Windows ($d_f = 0\,\mu\text{m}$)**: Step changes in NaCl/KCl ionic strength ($10\text{ mM} \to 100\text{ mM}$) with zero particulate or supersaturated scalant.
   * **3 Constant-EC Colloidal Polystyrene Bead Windows**: $800\text{ nm}$ polystyrene latex beads ($10^3\text{--}10^5\text{ particles/mL}$ in $10\text{ mM KCl}$ per [Khaja et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13154124/)).
   * **4 Mineral Scaling + Soluble CP Windows**: Supersaturated $\text{CaCO}_3$ / $\text{CaSO}_4$ / amorphous $\text{SiO}_2$ growing $d_f \in [2, 28]\,\mu\text{m}$ under active permeate-driven concentration polarization ($\text{CP} \in [1.4\times, 2.1\times]$ per [Nassr et al. 2025](https://pubs.aip.org/aip/rsi/article/96/6/065209/3350882/Crossflow-membrane-filtration-system-for-operando)).
   * **2 Negative-Control / Boundary Windows**: One macro-cake overrun ($d_f > 120\,\mu\text{m}$) and one intentional reference-arm shear-step perturbation.
2. **Ground-Truth Reference Measurements**: Independent optical coherence tomography (OCT), ex-situ cross-sectional FE-SEM (`JEOL JSM-7900F`), or synchrotron transmission WAXS/SAXS thickness measurement at the end of each coupon window.
3. **Pre-Registered Pass/Fail Criteria**:
   * **PASS**: Across the 4 Mineral Scaling + Soluble CP windows, `OTDB-APW Rev D` achieves $\text{MAPE} \le 12.0\%$ and $\ge 2.0\times$ lower RMSE than co-installed calibrated 4-frequency EIS + `Pt1000` (`B1`), with $0/3$ false fouling alarms ($>1.5\,\mu\text{m}$) during the 3 Pure Soluble CP windows and reference-arm fouling ratio $d_{f,\text{ref}}/d_{f,\text{sense}} \le 0.15$.
   * **FAIL / FALSIFIED**: If `OTDB-APW Rev D` exceeds $15.0\%$ MAPE on mineral scaling under CP, triggers $\ge 1$ false alarm during pure NaCl steps, or suffers $>15\%$ reference-arm fouling.

The interval between 12% and 15% MAPE is indeterminate and requires a reported confidence interval and independent review. The thresholds are proposed research criteria, not previously registered in a public trial registry.

## 2. 60-Day Hydrothermal Passivation Endurance Protocol
1. Immerse 5 packaged `OTDB-APW Rev D` fused-silica dies ($30\text{ nm }\text{Al}_2\text{O}_3 / 30\text{ nm }\text{HfO}_2$ ALD bilayer) in agitated $50\text{ mM NaCl}$ at $45\,^\circ\text{C}$ under continuous $1\omega = 4\text{ Hz}$ ($12\text{ mA}_{\text{pk}}$) and $5\text{ kHz}$ excitation for 60 days.
2. Measure open-water $3\omega$ baseline drift ($\mu\text{V}$) and DC/low-frequency shunt resistance ($R_{\text{shunt}}$) every 24 hours.
3. **Pass Criterion**: $R_{\text{shunt}} \ge 500\text{ M}\Omega$ and uncompensated $3\omega$ baseline drift $\le 0.50\,\mu\text{V}$ over 60 days (`0` boehmite blisters under 100x optical inspection).
