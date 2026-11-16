# What becomes simpler—and what does not

## 1. Corrosion and electrode adhesion

The circulating water, salt concentration, pH and cleaning chemicals can attack a wet electrode or its adhesion interface. The screenshot's claim that gold *will* lift is plausible as a test concern, not measured evidence about this device. A thin Ti/Cr adhesion layer can improve metal-to-glass adhesion, but the full stack, protective coating, exposed edges and electrochemistry still require endurance tests. Do not confuse PCB ENIG, ENEPIG and patterned passivated Ti/Au or Pt-on-glass with equivalent surfaces. **An unqualified plating finish cannot be selected for real brine service based on catalog descriptions alone.**

Screen at least three coupon types using the same replaceable carrier: (i) cheap PCB/plated test control for rapid electrical bring-up; (ii) patterned Ti/Au on borosilicate with an appropriately qualified passivation and contact geometry; (iii) Pt or another literature-supported inert patterned electrode on glass/ceramic. Record measured impedance, electrode drift, microscopy, peel/adhesion, shunt leakage and *wet-exposed surface* before/after saline/cleaner cycles. All are candidate materials, not approved options. No vendor price has been verified.

Relevant evidence: [PCB electrodes review](https://pmc.ncbi.nlm.nih.gov/articles/PMC7693744/), [through-glass 3ω with passivation](https://www.sciencedirect.com/science/article/pii/S0924424718303832).

## 2. Thermal conduction is a measurement, not a slogan

FR-4 may couple heat into the board, but saying it is always a 'bad insulator' is physically incorrect without geometry and frequency. Alumina ceramic often has *higher* thermal conductivity than FR-4 and borosilicate, which can change heat penetration dramatically. Substrate thickness, passivation, heater geometry, frequency, fluid convection and direct contact matter.

Run the **same drive/readout** over glass, ceramic and non-deployable PCB test coupons at multiple frequencies. Measure blank-surface 3ω amplitude/phase, drift and noise, then reproducible mineral deposit samples with independent ground truth. Calibrate frequency and substrate response; choose measured sensitivity/false-alarm behavior. A suspended membrane is not a default: it adds process steps and fragile packaging. If no cartridge beats a competent single-arm 3ω or EIS baseline after calibration, drop the custom hybrid.

Relevant evidence: [3ω chip substrates and thermal isolation](https://www.mdpi.com/2504-3900/2/13/883), [modern dynamically balanced 3ω bridge](https://www.sciencedirect.com/science/article/pii/S026322412502189X).

## 3. Alignment and seals

Use a **replaceable standardized wet cartridge** rather than precision aligning an entire system every time a sensor fouls. A single clamshell fixture has hard-stop defined gasket crush, 3 removable coupons and asymmetric alignment pins. Optical alignment targets and coupon flushness must be **measured**. The current design chooses 92×82 mm outer area, 64×9 mm lid groove, 16×10 mm coupon pockets and 1.0 mm nominal gasket. These are **provisional test dimensions** and should be changed to match the laboratory membrane cell and actual parts. The 3 S/R/G streams must not be presumed hydrochemically identical because they share the inlet.

A healthy geometric screen does not establish leak safety. A qualified lab must select material based on actual electrolyte/temperature/cleaning chemistry, validate gasket force/creep, inspect microchannel bond lines and run controlled leak tests in secondary containment before fluid/electrical work. Avoid production pressure claims. See [NIST microfluidic installation leak/connector failure guidance](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=934652).

## 4. Cheapest useful product metric

The first version may only need to say **CHECK THIS MEMBRANE NOW** with calibrated false-alarm and miss rates. Claiming ±micron film thickness may be unnecessary for making better cleaning decisions. Test matched baselines: ordinary differential pressure+temperature+flow+conductivity; multi-frequency EIS; optional thermal sensor; optional 3-arm witness. Always compare at equal resources. If conventional sensors give the same warnings at lower lifetime cost, do not build the special chip.

## Commercial barriers that cannot be papered over

Actual port/connector seal ratings, substrate/coating batch process, electrochemical lifetime, thermal signal discrimination, environmental isolation of guard, manufacturer-correct electrical design and hardware firmware, calibration drift, external third-party measurements, field economics, water-system compatibility, serviceability, manufacturing yield and quality management. None are resolved by a model, unit test, image, or bill-of-materials spreadsheet.
