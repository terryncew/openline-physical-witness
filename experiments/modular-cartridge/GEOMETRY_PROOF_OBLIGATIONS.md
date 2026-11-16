# Independent geometry-obligation challenge

**Status: HOST-TESTED CAD REVIEW ONLY.** This work does not establish physical sealing, corrosion resistance, thermal accuracy, pressure rating or manufacturability.

A previous nominal tolerance screen could declare a 92 × 82 mm fixture geometrically valid even with mounting bolts completely outside the plate, alignment holes outside the plate, zero-length channels and negative lid thickness. A plausible nominal gasket-compression score did not constrain the rest of the design.

This repair checks the **actual candidate parameters** at the point of acceptance. It now requires positive finite physical dimensions, finite nonnegative tolerances, three explicit channels and well-formed hole coordinates; channel footprints inside gasket windows; mounting/alignment holes inside the plate; adequate port footprint/web clearance; and sufficient gasket compression over the stated tolerance corners. Malformed candidates (including zero gasket thickness, empty channel lists and NaN values) return a rejected geometry decision and JSON-safe null results rather than crashing or producing nonstandard NaN reports.

The regression suite in [`tests/test_scale_bridge.py`](tests/test_scale_bridge.py) covers the nominal fixture, eight impossible parameter mutations, six malformed inputs, and progressively widened gasket/hard-stop tolerance bands. Run `bash ./VERIFY_RESEARCH_ONLY.sh` from this folder. No generated STEP or SVG file should be construed as an approved fabrication drawing.

**Decision:** ADOPT the narrow source-code invariant repair. **HOLD** any claim that a model of geometry guarantees seal integrity or reliable sensing. Future manufacturing depends on independent CAD/pressure review, measured sealing and dimensional verification, qualified materials and actual water testing.

This is an example of *refinement paired with proof obligations*: failure conditions should be checked at relevant geometric/tolerance resolution, not inferred from a nominal summary score. It is not a demonstration of general autonomous invention or of the physical sensor's performance.
