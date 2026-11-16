# Independent publication qualification: 005 benchtop candidate

Last reviewed: 2026-11-15. **Disposition: OPEN RESEARCH CANDIDATE, NOT BUILD-READY.** No experimental hardware qualification or external review is claimed.

## Verified receipts

Earlier model-only package verification: the 15 source checksums were internally consistent. `bash REPRODUCE_PHYSICAL_WITNESS_005.sh` exited 0 with 3/3 unit tests and unchanged hashes. Inspection showed those unit tests assert existing JSON contents and symbolic schematic strings, rather than independently evaluating an assembled circuit, ADC timing, detailed CAD rules or laboratory outcome.

The supplied C code compiles as freestanding math definitions under host GCC syntax checking, but contains no SDK integration, AD5941 SPI register driver, dynamic ADC sample scheduler, TMUX control transactions, calibrated acquisition, firmware flashing project or fault-safe actuation system. It must not be called working microcontroller firmware.

## Findings that block fabrication / cost claims

**1. Unrealistic vendor pricing.** The original 005 report gives $222.50 for option A and $284.50 for option B (two MicruX ED-IDE1-Pt electrodes assigned $31 each). Current MicruX IDE product listings show **$612.50–$675 per package**, not $31/unit at an order quantity of two. Therefore the option-B $284.50 assertion is retracted. Option A's $222.50 is an *unquoted modeled subtotal* contingent on a PCB vendor's delivery/finish, extra assembly and laboratory equipment; the overall under-$300 rig claim is NOT demonstrated. Microbalance, profilometry, flow/calibration instrumentation and labor are not included. Order only after fresh supplier quotations.

**2. Native CAD and actual pin map not qualified.** The custom AD5941 symbol presents a shortened conceptual pin list with sequence numbers that cannot be assumed to map to the 48-LFCSP manufacturer pins. No `kicad-cli` ERC, actual package/layout review or correct downstream netlist export is evidenced. The schematic and BOM should be used only as discussion aids pending a full verified redesign. HunStat2 authors' 2026 correction should be consulted; original part number `C1206C479D5HAUTO` appears inconsistent with the claimed 4.7µF value, but supplier confirmation is required before asserting its physical capacitance. A manufacturer-confirmed 4.7µF candidate is `C1206C475K3RACTU`.

**3. SNR and fault detection are derived under assumed noise.** 005's model uses selected heat-spreading multipliers, hydrodynamic noise and seeded synthetic deposits. Its claimed detection rates are not measured, and the comparison model explicitly injects a large bias into conventional EIS under confounder conditions. The included script now reproduces these calculations openly so critics can change the assumptions. The unmonitored partial-fouling blind spot remains.

**4. Proposed chemistry doesn't replicate membrane concentration polarization by itself.** A bulk NaCl step is a *conductivity confounder*, not a measurement of membrane-surface concentration polarization under permeate flux. The original proposal also compares chemically different sense/reference streams whose compositions must be matched or explicitly modeled. A reviewable experiment should add or separately isolate permeate-driven CP after validating basic fouling observability.

**5. Test article geometry does not imply manufacturability.** ENIG PCB electrodes and packaged Pt100 sensors may be useful for exploratory proof-of-signal work, but no passivation, wetted-material qualification, calibration drift, electrode stability, laminate safety, or scalable chip geometry has been demonstrated.

## Acceptance sequence

1. Verify actual part footprints, reference chip supply rails, ADC sample scheduling, signal-to-noise under expected flow, and device/PCB safety under native KiCad + vendor review; implement hardware acquisition and a no-load electronic bench self-test.
2. Obtain firm and timestamped BOM/pricing for a sensor-only comparison, and separately price independent deposition ground truth (profilometer or calibrated mass gain), fluid cell, pump and cleaning consumables.
3. Run real blank/clean measurements and calibration against matched conventional EIS/RTD/flow instrumentation in the **same** apparatus. Record raw voltage, temperature, flow, solution conductivity, calibration, and uncertainty intervals; preserve all failure and leakage evidence.
4. Only then run seeded/randomized calcium-carbonate deposition on actual coupons with independent blind ground truth. Test partial reference fouling as an **explicit stop/falsifier**.

No fabrication, purchasing, human safety-critical deployment or laboratory endorsement is authorized by this release.
