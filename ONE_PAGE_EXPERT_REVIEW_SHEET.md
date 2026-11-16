# One-Page Expert Review Sheet — OTDB-APW Rev D (`v0.4.0-rc4`)

**Target Audience**: Instrument scientists, membrane separation researchers, and electrical engineers at national laboratories (`LBNL`, `LLNL`) and university cleanrooms (`UC Berkeley Marvell Nanofab`, `NJIT Microfluidics`).

### 1. Physical Hypothesis Under Test
Can a co-planar differential Cahill $3\omega$ thermal bridge (`4 Hz` / `36 Hz`) + 4-frequency interdigitated electrode (IDE) impedance witness (`5 kHz` / `50 kHz`) on a single fused-silica die decouple **solid interfacial fouling thickness ($d_f \in [0.5, 85]\,\mu\text{m}$)** from **soluble concentration-polarization (CP) boundary layers ($\text{CP} \in [1.35\times, 2.15\times]$)** and **$\pm 18\%$ local flow/viscosity fluctuations** without optical access?

### 2. Where OTDB-APW Wins vs. Where Conventional Baselines Win (Synthetic Holdout Summary)
* **Where OTDB-APW Rev D Wins (`S2` & `S3`)**: When unmeasured soluble CP ($1.35\times\text{--}2.15\times$) and $\pm 18\%$ flow jitter occur simultaneously (`S2`, inspired by [Nassr et al., *Rev. Sci. Instrum.* 2025](https://pubs.aip.org/aip/rsi/article/96/6/065209/3350882/Crossflow-membrane-filtration-system-for-operando)), `OTDB-APW Rev D` achieves **`8.17%` mean error (`0/20` CP false alarms)** vs **`36.58%`** (calibrated single-arm $3\omega$), **`43.31%`** (calibrated multi-sensor fusion), and **`49.18%`** (calibrated multi-frequency EIS + `Pt1000`). Under variable cake porosity $\phi \in [8\%, 38\%]$ (`S3`), the 5-state porosity-coupled solver achieves **`8.05%` mean error** vs **`32.69%`** for multi-sensor fusion.
* **Where Conventional Baselines Win (`S1`, `NC1..NC3`, `NC5`)**:
  1. **Constant-EC Particulate Fouling without Soluble CP (`S1`, inspired by [Khaja et al., *ACS Appl. Mater. Interfaces* 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13154124/))**: Calibrated multi-sensor fusion (`B3`: **`0.67%`**) and single-arm $3\omega$ (`B2`: **`0.91%`**) beat `OTDB-APW Rev D` (**`3.96%`**).
  2. **Partial Reference-Arm Fouling (`NC5`, $d_{\text{ref}} = 35\%\text{--}75\%\,d_{\text{sense}}$)**: Calibrated multi-sensor fusion (`B3`: **`7.72%`**) beats `OTDB-APW Rev D` (**`71.17%`** unflagged underestimation).
  3. **Outside Physical Window (`NC1..NC3`)**: `>85 um` cake ([`PMD75B` $\Delta P$](https://www.transcat.ca/endress-hauser-differential-pressure-deltabar-pmd75): **`1.14%`**), `18.2 MOhm-cm` UPW ([`Thornton 240-202`](https://www.servapure.com/Thornton-Sensors_c_5965.html?page=2): **`0.85%`**), and `<150 nm` conditioning films ([`QSense Pro` QCM-D](https://www.nanoscience.com/products/qsense-quartz-crystal-microbalance/qsense-pro/): **`3.40%`**).

### 3. Five-Minute Audit Checklist for Reviewers
1. **Run One-Command Cold Start**: `bash ./REPRODUCE_OTDB_APW_RELEASE_004.sh` (verifies `SHA256SUMS_SOURCE.txt` before & after, compiles C99 firmware, runs `6/6` tests under standard and `-O` Python, exits `0`).
2. **Inspect Connected KiCad 7/8 Schematic**: Open `artifacts/otdb_apw_afe_rev_d.kicad_sch` and `artifacts/otdb_apw_afe_rev_d.net` (`41` symbols, `140` typed library pins, `204` placed pins across `52` nets, split `U7A`/`U7B` `ADP7118` + `U8` `ADM8829` + `U7C` `ADP7182` regulators, dual single-channel `U3A`/`U3B` `AD5683RBRMZ` DACs). Run `kicad-cli sch erc artifacts/otdb_apw_afe_rev_d.kicad_sch` on your workstation to close `HOLD_NATIVE_KICAD_CLI_ABSENT`.
3. **Inspect GDSII & PEEK Flow Cell**: Open `artifacts/otdb_apw_rev_b.gds` in KLayout and `artifacts/otdb_apw_peek_flow_cell.stl` in FreeCAD/MeshLab.
