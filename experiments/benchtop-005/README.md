# Benchtop 005 — candidate path from models to measured membrane fouling

**Status: EXPERIMENTAL / DESIGN REVIEW ONLY. Do not fabricate or connect this electronics design to powered equipment from these files.**

This supplementary research explores a less expensive way to challenge the [OTDB-APW Rev D computational hypothesis](../../README.md). Instead of claiming that the chip sensor has been demonstrated, it asks whether a simple thermal/electrical test coupon and an existing [HunStat2 open-hardware impedance instrument](https://github.com/hunstat2/HunStat2) could produce the **first real fouling measurement**.

Potential result: an inexpensive bench experiment comparing actual calcium-carbonate deposits, solution conductivity changes, temperature/flow confounders, and a strong conventional baseline. The proposed extra reference-arm measurement attempts to address Rev D's published 71.17% synthetic failure, but **its ability to detect contamination has not been measured**.

## What is included

- `PROTOCOL_DRAFT.md`: prospective physical test and decisive negative controls; requires laboratory review, not externally preregistered.
- `VALIDATION_HOLDS.md`: independent audit of the actual 005 archive and remaining hardware, price, physics and provenance issues.
- `data/BOM_MODEL_ONLY_005.json`: 005 research component list with erroneous/unsupported purchasing conclusion disabled; **not a shopping list**.
- `models/reproduce_snr_model.py` + `data/SNR_MODEL_ONLY_005.json`: reproducible assumed-parameter SNR and reference-fouling scenarios, **not measured sensitivity, performance, or coverage**.
- `artifacts/otdb_apw_005_hunstat2_addon.kicad_sch`, `.net`: design sketches. **Their custom symbol pins do not constitute a verified 48-pin manufacturer footprint mapping or native KiCad ERC approval**.
- `firmware/otdb_apw_005_rp2040_firmware.c`: host-compilable lock-in mathematics only. **No runnable RP2040 hardware drivers, AD5941 initialization, DAC/SPI transactions, PIO/DMA loop or data acquisition app.**
- `cad/`: geometry candidates, not manufacturing approvals.

## What has been verified

The predecessor computational package passed its own three static/report-checking tests and checksum verification; this supplement adds independent behavioral tests and strict hardware qualification holds. The lock-in math C file passes `gcc -std=c99 -Wall -Wextra -Werror -fsyntax-only` locally. The NumPy-only model has a deterministic replay check, not an empirical test. There have been **zero physical measurements**.

Run the supplementary computational checks from this directory with `bash VERIFY_CANDIDATE.sh` (Python 3, GCC and NumPy required). Existing [Rev D v0.4.0-rc4](../../README.md) and GitHub release/tag stay unchanged.

## Background sources

[HunStat2 2025 paper](https://doi.org/10.1039/D5AY01179E) and [2026 correction](https://doi.org/10.1039/d5ay90168e), [Analog Devices AD5941 datasheet](https://www.analog.com/en/products/AD5941.html), [MicruX IDE product listing](https://www.micruxfluidic.com/product/interdigitated-electrodes-ide/).

**No institution or vendor has reviewed, approved or endorsed this design.** This folder contains no upstream HunStat2 code or licensed vendor drawings.


## Independent 005B engineering closeout (host-only)

`LIMITED_ENGINEERING_CLOSEOUT.md` explains the exact remaining barrier to physical reproduction. The reproducible `firmware/reference_guard.{c,h}` and `firmware/lockin_core.{c,h}` add tested software-only reference gating and two-frequency coherent demodulation; all sample traces used by the tests are synthetic. The hardware gate still fails closed. Test it with `VERIFY_CANDIDATE.sh`, which also executes adversarial host tests and a machine-readable hardware readiness gate. **The code cannot measure an AD5941 without actual wired electronics and missing SDK drivers.** All numeric guard thresholds are illustrative; it is not deployable safety instrumentation.
