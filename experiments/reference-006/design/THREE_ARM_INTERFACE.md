# Three-arm reference-witness architecture — review blueprint, NOT PCB files

## Problem and observability

Let `F_s` represent sense-surface deposit response, `F_r` the reference deposit response, and `B` the response to shared bulk water conditions. Assume matched gains only for this algebraic example. A conventional two-arm differential yields `D = (F_s+B) - (F_r+B) = F_s - F_r`. Without an independent measurement of `F_r`, `D` cannot identify `F_s`. A numerical estimator cannot repair this missing rank.

Introduce a **third protected witness** `F_g`, also exposed to comparable bulk effects `B`. Measure `R = (F_r+B) - (F_g+B) = F_r - F_g` through a *different raw measurement path*. With independently verified `F_g ≈ 0` and matched transfer functions, `D+R ≈ F_s`. This is a **conditional identifiability statement**, not proof of physical calibration or device performance. If `F_g` fouls equally to `F_r`, `R≈0` falsely suggests a clean reference. If the third branch sees different hydrodynamics or chemistry, `B` will not cancel. `models/observability_certificate.py` contains exact counterexamples.

## Candidate plumbing: three observation surfaces

The editable flow concept in `three_arm_concept.svg` shows a common monitored inlet split to an exposed **sense coupon** (S), a **reference coupon** (R), and a **serviceable protected witness coupon** (G). Each branch requires local temperature, conductivity and flow telemetry; a common inlet alone does not prove identical local conditions. An optional independent optical check and separately removable mass/step-height coupon are the only basis for saying the protected witness remains clean during a physical test. **Do not assume any porous shield or filter maintains dissolved salt boundary layers.** Every guard/cleaning arrangement must be bench compared under real CP and deposited solids; preservation of relevant transport conditions is the constraint.

S, R, G sensors require two separately acquired complex thermal phasors, independently monitored analogue reference paths and an impedance measurement on R/G. Time-multiplexing through AD5941's **single ADC channel** is not simultaneous observation. Synchronization, settling time, phase drift, ADC mux switching, analogue noise coupling and crosstalk must be measured. The existing Benchtop 005 schematic has a conceptual 21-pin AD5941 symbol for a 48-lead physical chip and does **not** qualify this architecture for production.

## Minimal state/control boundary

The current research C module takes already acquired and independently calibrated measurements. It enforces: a confirmed baseline under documented clean conditions; presence of S/R/G channels from separately verified acquisition; an explicitly recent blank check; monotonic sequence and sample age; physical environment matching; two frequency complex R-G phasors; a second independent R-G electrical measurement; and an independent turbidity observation. Failure of any witness causes HOLD. A reference drift faults and *latches* until manual maintenance. Returning `OBSERVATION_CONSISTENT_ONLY` **never authorizes** an automated action or implies known mineral thickness; a receiving controller must have a separate receiver-controlled acceptance gate.

These are code-enforced conditions for a future instrument, **not proof** that upstream firmware is trustworthy. Config booleans such as `clean_baseline_externally_confirmed` and `guarded_coupon_inspected_clean` are attestations from a proposed human/lab workflow, not cryptographically verified physical facts. State is held in RAM and not durable through power loss; before deployment, implement an externally auditable persistent service ledger and epoch/nonce replay protection.

## Hardware work required before assembly

A qualified electronics team must source actual HunStat2 schematics and AD5941 pin table, select full manufacturer symbols/footprints, calculate analogue input common-mode and gain, verify all op-amp supply rails, ground partition, phase noise, protective resistors, excitation power, mux charge injection and reference channel independence. Build a KiCad PCB with complete electrical rules, run native ERC and PCB DRC plus footprint parity, and verify bench traces with known test impedances before fluid exposure. An isolated lab supply and interlocks must be selected by the qualified builder. **Do not order a board from the existing 005 `.kicad_sch` sketch.**

## Adversarial challenges

The prototype must distinguish a deliberately fouled R from a clean R with *the same S-R differential*; a blank/flush test must distinguish a fouled R from a reversible bulk-water shift; simultaneous fouling of R and G must be deliberately induced to establish the limitation; mismatched flow/temp/conductivity must trigger HOLD. Introduce realistic mixed silt + organic film + scale and compare to calibrated multi-sensor fusion and conventional pressure/turbidity/EC monitoring. Pre-define false-alarm, abstention, sensitivity and recovery metrics with blinded physical ground truth.

## One critical diagnostic result

The current C guard can detect bad **reported input channels**, but no software-only test can prove those readings came from independently acquired physical sensors. That is the current hardware-to-software boundary and the first lab acceptance test.

## Manufacturer pin-map recovery (additional computational repair)

`AD5941_48_PIN_REVIEW_MAP.csv` transcribes the 48 numbered **AD5941** leads from Analog Devices **Rev. G (February 2026), Table 7, pp. 19–21**, with critical SPI/electrode/power signals asserted in an automated completeness test. Source: [manufacturer datasheet, Rev.G](https://www.analog.com/media/en/technical-documentation/data-sheets/AD5940-5941.pdf). The 7×7 mm LFCSP has an **exposed pad** that must connect to ground per the package drawing; this pad is *not* one of the 48 leads and its footprint pad number must be verified separately. This CSV is a review aid, not a checked KiCad symbol, footprint or routed PCB. The previously published 005 concept symbol remains explicitly incomplete. Independent datasheet double-check, native ERC, design-rule checks and physical inspection are still REQUIRED.
