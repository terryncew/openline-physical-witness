# 005 independent engineering closeout: bounded physical-proof path

**Verdict:** software-side validation improves; physical instrument readiness remains **HOLD**.

The first consequential constraint is acquisition, not another simulation. The 005 design promises independent differential and reference-arm 3ω measurements and alternates impedance on two IDEs, but the source supplies neither real RP2040/AD5941 acquisition drivers nor timing/synchronization evidence, nor a manufacturer-verified 48-pin AD5941 schematic and routed board. Until those exist, a one-command check cannot honestly claim a build-ready prototype.

## Evidence added in this companion

- `firmware/reference_guard.{h,c}`: host-compilable reference-phasor interlock. It checks a **separately observed** calibrated reference phasor, not the candidate's own estimate. It **holds** on missing calibration, reference, stale data, NaNs, temperature shift, out-of-range conditions and complex reference drift. Zero thresholds are not a physical endorsement: the values in the host test are illustrative.
- `tests/reference_guard_host_test.c`: adversarial **synthetic** host harness includes healthy, stale/future sample, missing witness, phase-only drift, amplitude drift and invalid threshold cases. This does not imply physical-fault detection sensitivity or functioning electronics.
- `tools/hardware_readiness.py`: machine-readable FAIL-CLOSED hardware gate. Counts the AD5941's symbolic pins and demands native ERC, RP2040 SDK driver/flash image, routed PCB and genuine physical measurement. Not a pin mapping tool or native ERC replacement.
- `tests/test_hardware_readiness.py`: verifies the gate refuses to treat the sketch as build-ready.

- `firmware/lockin_core.{h,c}` plus `tests/lockin_core_host_test.c`: coherent 1 Hz / 8 Hz **software** demodulation of independent differential/reference sample arrays with deterministic rejection of missing, stale-index, non-finite and incomplete samples. Values tested in synthetic microvolt phasors, not from an AFE. No RP2040 transport, power-on procedure or hardware timing closed.

## More consequential mistakes still caught

The earlier feasibility report's $284.50 option B includes two MicruX platinum IDEs at an unsupported $31/unit; current site prices are substantially larger and sold in packs. The $222.50 option A is also unquoted and excludes lab equipment and instrument calibration. No credible sub-$300 all-in price is established.

The proposed saline-step test is a **bulk-conductivity confounder test**, not actual membrane concentration polarization, which requires membrane transport/permeate flux. The synthetic benchmark separately imposes a large uncompensated salt bias on the conventional EIS baseline; its apparent thermal advantage is not independent physical evidence.

A hardware-integrated reference witness remains an *unproven* design idea. The host-level gate can refuse bad input, but only a calibrated, separate measurement path and real contamination experiments can establish that it detects faults.

## External boundary

To match the physical hardware standard shown in Anthropic/Diode's electronics demonstration, a manufacturing partner needs to deliver a vendor-mapped schematic, completed PCB, purchase/assembly, microcontroller firmware that talks to actual devices, and bench measurements under independent test conditions. Our current assets cannot substitute for that. No sensor has been fabricated; no wafer, board, or physical foulant has been tested. Nothing is approved for deployment, purchases or lab claims.

**Do not replace the validated Rev D release tag with this experimental module.** Publish 005 as an explicitly separate review-only supplement if needed, or retain it privately until a hardware collaborator takes over.
