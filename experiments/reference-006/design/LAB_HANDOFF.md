# Independent experimental falsification — small lab handoff

**Unregistered prospective experiment. No data have yet been collected. Requires laboratory review, safe chemical handling, legal authorization and qualified electronics supervision.** The cheapest physically meaningful test is not a semiconductor wafer; it is a sensor coupon placed in a removable, inspectable flow cell with an independent check of actual surface deposition.

## Phase 0 — dry electrical qualification (required before wet operation)

Use reference board or wired prototype only after complete device pin mapping, manufacturer component/footprint parity, native KiCad ERC and PCB DRC, protective electrical review, and passing firmware/DAQ acquisition validation. Verify *two independent reference measurements* from distinct analogue acquisition paths, valid phasor amplitudes and phases at two frequencies, noise floor and channel crosstalk. Check that the electrical reference can be deliberately perturbed in a blinded challenge without forging either reading in software. If independence cannot be demonstrated: **STOP, classify design not testable**.

## Phase 1 — simple flow-cell test

Use S (depositing test surface), R (ordinary reference), G (serviceable protected guard) and a removable adjacent witness coupon. Match and measure each branch's temperature, conductivity, flow and residence time. Establish a physical clean baseline using optical inspection and/or coupon weight/profilometry. Alternate clean water and safe controlled mineral-deposition conditions with ordinary changes in bulk ionic strength, flow and temperature. *A NaCl concentration step is a bulk conductivity challenge, not proof of true membrane concentration polarization*; CP requires permeation and suitable membrane boundary measurements.

Prespecify the order of trials and hide the conditions from the person analyzing recorded signals. Include at least one clean S/R/G set, deliberate R-only fouling with G clean, matched S+R fouling, induced R+G fouling, reversible bulk-water change, and a mixed particulate/organic/salt trial. Physical ground truth must be documented before unblinding through optical microscopy, calibrated step-height/profilometry, removable coupon mass gain or another independently validated measurement. A laboratory should decide the feasible number of replicates and allowable materials in advance.

## Comparison and falsifiers

Compare a calibrated conventional multi-sensor baseline using the SAME apparatus and experimental resources (EIS + temperature/flow/pressure/EC where appropriate) rather than an artificially uncalibrated estimator. Include turbidity or optical observation if the physical question involves mixed suspended solids. Record both sensors' estimates and their **abstention decisions**, alongside detection lead time, false alarm rate, absolute or relative thickness error, and reference-fault detection. Do not discard failed trials. Never infer measured membrane thickness from a synthetic generator.

The proposal is unsupported if a protected G does not remain sufficiently clean, cannot be made flow/chemical comparable, or the R-G witness cannot detect deliberately contaminated R above empirically measured noise. If the two-arm baseline matches or beats the added witness under matched budgets, reject the third-arm complexity for that context. If a user could bypass a HOLD by missing a channel, replaying a frame or restarting the system, software must also fail acceptance. Do not promote to field use based on a 48-hour bench demonstration.

## Data and reporting

Publish exact measured CSVs, calibration instrument specifications, recording timestamps, test order, versioned firmware, PCB fabrication package, blinded truth/unblinding key separated during analysis, raw spectra, matched conventional baseline and negative results. Label anything derived from simulation separately. Record who physically verified the protected arm and when; make an expired or failed blank inspection visible to the operator. Obtain explicit owner permission before purchasing, making external contacts or undertaking lab work.
