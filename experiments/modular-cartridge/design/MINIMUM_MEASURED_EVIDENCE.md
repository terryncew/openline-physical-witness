# Minimum experiment that could kill the product idea

**Research proposal, not a registered protocol. Work only in a qualified laboratory with site-approved fluidic and electronics safety.** The conceptual CAD is not a rated pressure vessel and must not be connected to industrial process pressures.

### Stage 0 — reusable instrument check

First verify a commercially documented impedance channel and a separate thermometry/thermal channel using a **proper manufacturer pin/footprint map** and independent calibrated bench instruments. Native schematic/ERC, routed PCB DRC, component electrical protection and firmware acquisition must pass. Reproduce known loads and characterize crosstalk, timing, phase, ADC gain and noise **on real electronics**. If this fails, don't introduce water.

### Stage 1 — cheapest physical coupon trial

Prepare replaceable coupons with *measured real deposits* and clean negative controls. Two or more substrate/metallization choices share the same test fixture; use matched flow, water composition and temperature measurement. Independently measure actual deposit by microscopy or profilometry and a measured conventional reference. Assess whether an action-level fouling alert can separate actual deposit from reversible salt/flow/temperature changes. **Do not call bulk conductivity steps 'true membrane concentration polarization'**; that requires a permeating membrane and boundary layer investigation. Randomize and blind trial labels where feasible.

### Stage 2 — adversarial reference challenge

Deliberately foul the R arm while S has known condition, then foul R+G together. The third branch is only useful if it catches contamination without excessive false alarms, and if G stays comparably clean. Measure local stream T/EC/flow separately. Compare against periodic blank and conventional sensor fusion. The published 71.17% NC5 figure is synthetic and must not be used as a measured benchmark.

### Stage 3 — production-critical lifetime and sealing

Test candidate wet-exposed electrode and sealing material on real saline/cleaning cycles under the intended operating envelope and check corrosion, coating integrity, stray shunts, chemical attack, leakage, creep, cleaning recovery and cartridge exchange repeatability. Then obtain written fabrication quotes with yield assumptions and minimum order quantities. An accelerated test cannot be relabeled as field service lifetime without evidence.

### Minimum acceptance packet for an external lab

Raw timestamped data and blinded conditions, independently measured deposit truth, conventional baseline matched on the same water loop, complete acquisition and calibration files, photos of actual sensor/coupon, 0/failed trials reported, test conditions, accuracy *and* false-alarm rates, and costed alternative methods. Report **PASS / FAIL / INCONCLUSIVE** by environment, not only an averaged winner.

### When to STOP

If real deposits cannot be discriminated above physical noise at useful lead time, if the added witness cannot reliably detect reference contamination before the baseline, if G cannot remain clean and environmentally comparable, if sealing fails, or if the best conventional method is cheaper at equal performance: reject the bespoke chip route and preserve the negative result. The experiment is valuable either way.
