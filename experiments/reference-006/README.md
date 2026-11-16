# Physical Witness 006 — reference-arm observability challenge

**Research design and reproducible host tests only. No manufactured sensor, working PCB, hardware firmware, or physical measurements. Do not use for instrument control.**

This is a narrowly scoped response to the Rev D **NC5 failure**: fouling of the supposedly clean reference arm produced **71.17% mean error without an alarm in a constructed synthetic case**. The earlier design also loses to calibrated conventional multi-sensor fusion when soluble concentration polarization is absent (**3.96% vs. 0.67%** in the published synthetic S1 case). These are not measurements of an actual device.

The simplest possible differential sensor subtracts `sense - reference`. If both fouled, this can hide the deposit. No improved software can recover information that was never measured. A **third witness, measured separately**, provides an extra comparison (`reference - protected guard`). If the guard is independently known to remain clean under a matched environment, the two readings may distinguish deposit signal from reference contamination. If the guard also fouls, or experiences different temperature, conductivity or flow, the new comparison may be misleading. The included `models/observability_certificate.py` demonstrates both the benefit **and** the remaining ambiguity using exact arithmetic, not random scenarios.

## What's implemented

- `firmware/triarm_witness.{h,c}`: host-testable **research-only** fail-closed pre-estimation check requiring two complex thermal frequencies, an independent IDE witness, verified separate channels, a recent external blank/clean-reference check, monotonically increasing sample sequence, matched water conditions, and a turbidity warning for mixed particulate fouling. One suspected contamination signal latches the hold until maintenance. A passing check is named **OBSERVATION_CONSISTENT_ONLY**, never an authorization to control hardware or a calibrated mineral thickness estimate.
- `tests/test_triarm_witness.c`: deterministic hostile inputs for phase-only drift, fouling at one frequency, electrical drift, stale/replayed frames, missing channel, invalid calibration, water mismatch and mixed turbidity. Numeric thresholds are **illustrative research parameters only** and not claimed to detect a given contamination thickness.
- `models/observability_certificate.py`: identifies when two-arm and three-arm measurements are insufficient even in an ideal noiseless model.
- `design/three_arm_concept.svg`: editable **functional block and fluid-path concept**, not a CAD schematic or manufacturable design.
- `design/THREE_ARM_INTERFACE.md`: proposed sensor/controller interface, alternative architecture choices, signal routing and bench challenges.
- `design/LAB_HANDOFF.md`: minimal real-world experiment, matched conventional baseline, decision thresholds and independent ground-truth requirements.
- `tools/hardware_hold.py`: machine-checkable physical-readiness **HOLD**, never a synthetic PASS for native ERC, PCB DRC, firmware, independent reference qualification or physical test data.

## Reproduce without any external API

```bash
bash VERIFY_RESEARCH_ONLY.sh
```

Requires Python 3 and GCC with UBSan. No downloads, proprietary SDKs, cloud models or hardware are needed. Source checksums are reverified. **These are software-invariant tests, not instrument sensitivity tests.** The original Rev D published tag `v0.4.0-rc4` and Benchtop 005 package are unchanged.

## Decision on the three proposed fixes

1. **Protected third reference + independent witness** — **ADOPT AS A TESTABLE RESEARCH DESIGN**, not a qualified sensor. Adds an observation potentially sufficient to expose reference contamination when its cleanliness and environment are independently supported.
2. **Periodic blank / flush / shear-step reference challenge** — **INCLUDE IN LAB PROTOCOL**. The mechanical cleaner cannot be assumed safe, contamination-free, or effective until wet-lab measurements. Flow changes can themselves change the thermal signal; a reversal is diagnostic only against independently measured ground truth.
3. **An additional turbidity/conductivity channel for mixed foulants** — **SCREEN / ABSTAIN**. The published S1 comparator was calibrated *multi-sensor fusion*, not merely turbidity plus conductivity, so this addition isn't a demonstrated performance improvement. Direct to the conventional baseline or abstain until it is fairly validated.

## Why the work stops here

The source **cannot** establish that a protected arm stays clean, that water conditions match, that the electronics sample independent channels with sufficient SNR, that the full 48-pin AD5941 mapping is correct, or that the design works outside the synthetic model. Closing those boundaries needs a manufacturer-verified schematic, native KiCad ERC and PCB routing, actual acquisition drivers, a flow-cell prototype, measured data, and blinded conventional comparisons. No cost or scientific superiority claim is made here.

Reference literature: [2023 peer-reviewed membrane-fouling monitoring via 3ω](https://www.nature.com/articles/s41598-023-42337-1), [USGS instrument cleaning and calibration guidance](https://pubs.usgs.gov/publication/tm1D11/full), [AD5941 manufacturer's device description](https://www.analog.com/en/products/AD5941.html). Third-arm architectures and sensor-cleaning proposals require prior-art analysis before claiming novelty.
