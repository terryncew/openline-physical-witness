# First physical falsification experiment — prospective draft

**Not pre-registered, not run, requires laboratory approval.** This is a compact draft of an earlier computational feasibility study, corrected for assumptions that would bias results. Do not treat the below as a completed experiment or a ready-to-order kit.

## Gate 0: Device feasibility

Qualify manufacturer pin assignments, power-rail design, ADC acquisition on separate differential/reference channels, simultaneous timing, electrical isolation, thermal self-heating, and flow-cell leak/safety. Native KiCad ERC and vendor datasheet checks must pass before manufacture. If no valid acquisition path exists, the test stops here.

## Gate 1: Observe a signal from a real deposit

Run a clean water/saline blank with time-stamped raw EIS, single-arm thermal and differential thermal channels (if an actual sensor board is available). Compare against an independent conventional EIS+temperature+flow baseline. Use a physically deposited calcium carbonate layer on a removable surface coupon; independently measure real mass or surface profile with properly calibrated lab equipment. No resistor substitution counts as physical fouling evidence.

## Gate 2: Blind, adversarial confounder tests

Freeze calibrations and decision thresholds **before** holdouts. Randomize order, hold sense/reference liquid chemistry constant when testing differential contamination, and separately vary temperature, flow, and bulk conductivity, logging actual values. Test both real mineral deposit and no-deposit blank; an electrolyte-strength change is **not** a membrane concentration-polarization experiment. Actual CP requires a documented membrane/permeate-flux apparatus and independent measurement/assumption.

## Gate 3: Reference failure and conventional alternative

Deliberately foul the reference path, including mild/partial deposits, and observe whether the candidate detects the fault **before** issuing a thickness estimate. The original computational system showed an unflagged 71.17% error in one partial-reference-fouling scenario. If the witness misses real reference contamination, fail closed and reject instrument qualification. If calibrated conventional fusion equals or outperforms the thermal/electrical candidate under matched conditions, adopt the simpler conventional method.

## Reporting

Publish raw traces, calibration history, instrument model, component numbers, third-party ground truth, sample count, repeat variability, excluded runs, and experimental uncertainty. Distinguish SUPPORT / FALSIFIED / INCONCLUSIVE; lack of a sufficiently sensitive ground-truth measurement is INCONCLUSIVE, not support. Use the original 48-hour/60-day protocol as a later-stage reference, not a claim that it has been performed. All equipment use, spending and outreach require owner approval.
