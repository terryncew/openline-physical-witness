# Research status and independent handoff

**Last consolidated:** November 2026. **Scientific status:** computational research + host-tested exploratory extensions; **physical readiness: HOLD**.

## What question does this project investigate?

Can a compact combination of thermal-wave and electrical-impedance measurements distinguish early mineral deposition on water-treatment membranes from dissolved-salt concentration changes, temperature and flow disturbances? Could an independently verified protected reference reveal reference-arm fouling before it corrupts that estimate? The potential water, energy and equipment benefits are conditional on physical experiments and cost engineering; this repo does not claim realized savings.

## What is established?

- **004**: Reproducible published simulations, comparator estimators, preliminary circuit/CAD concepts, host C signal math, tests and negative controls. In the synthetic CP+flow case, the model appears promising; in the no-CP case conventional calibrated multisensor methods win.
- **NC5 failure**: Partial contamination of the nominal reference yields **71.17% mean synthetic error with no warning**; conventional fusion yields **7.72%** in the same constructed case. This is a serious unresolved deployment barrier.
- **005**: Research-only route to a test coupon and flow cell using open-source impedance hardware. Host-side demodulation and fail-closed checks run, but PCB pin/footprint parity, working hardware drivers, native electrical checks, itemized current supplier costs and physical readings have not been established.
- **006**: Third-arm/reference-guard concept plus mathematical counterexamples and host-tested fault detector. A clean third witness **can** make some contaminating-reference conditions distinguishable. It **cannot** resolve ambiguity if the protected guard also fouls or the channels lack comparable conditions and independent acquisition.

## Where to inspect or reproduce

- Original frozen research release: [`v0.4.0-rc4`](https://github.com/terryncew/openline-physical-witness/releases/tag/v0.4.0-rc4) and [004 technical dossier](README.md#original-technical-dossier--otdb-apw-rev-d).
- Low-cost test candidate: [Benchtop 005](experiments/benchtop-005/README.md).
- Three-reference experiment: [Reference 006](experiments/reference-006/README.md) and its [functional schematic](experiments/reference-006/design/three_arm_concept.svg).
- Physical experiment and rejection conditions: [independent laboratory handoff](experiments/reference-006/design/LAB_HANDOFF.md).
- For external automated analysis: [AGENTS.md](AGENTS.md), [claims/falsifiers](CLAIMS_AND_FALSIFIERS.md), [honest limits](HONEST_LIMITATIONS.md).

## What would change the scientific conclusion?

A lab must build or adapt safe electronics with verified pin mapping and hardware acquisition, use a flow-cell coupon with actual deposited mineral, obtain independently calibrated physical truth, and compare simultaneously against competent conventional multi-sensor instrumentation. Deliberately dirty the ordinary reference while keeping/monitoring a third guard, then deliberately challenge the guard too. Record samples, calibrations, failures and abstentions without selecting only favorable trials.

**If the three-arm witness cannot flag reference contamination ahead of severe estimator error, if it cannot remain reliably clean and environmentally matched, or if conventional instrumentation matches or wins at similar cost, reject the extra complexity.**

No wafers, PCBs or wet-lab tests have been completed. There is no physical error rate, demonstrated economics, laboratory endorsement, safe-to-build schematic, approved fab package or field deployment permission. The next necessary evidence is **real hardware acquisition and blinded measured fouling**, not more model-generated scenarios.
