# Scientific boundaries and alternative mechanisms

### What the screenshot gets right

Rev D's NC5 synthetic reference contamination is a serious, quantified model failure. Subtraction of two similarly fouled surfaces can hide a deposit. Existing water-sensor literature recommends physical cleaning, calibration and lab cross-checks; a purely internal math gate cannot verify a dirty surface is clean. See [2025 best-practice high-frequency monitoring review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11880092/) and [USGS field cleaning/calibration](https://pubs.usgs.gov/publication/tm1D11/full).

### What it overstates

"That will happen in real water" is a plausible field risk, not measured probability for OTDB. The S1 synthetic result shows conventional **matched-budget multi-sensor fusion** winning 0.67% versus 3.96%; it does *not* separately establish that simple turbidity + conductivity was the winning comparator. More sensors also introduce new failure modes and calibration costs. The PCB issue is real: a programmatic 52-net check is not full native ERC/PCB DRC or a qualified manufacturing package.

### Novelty test

The 3ω method has already been used in published membrane-fouling monitoring: [Scientific Reports 2023, Membrane fouling monitoring by 3ω sensing](https://www.nature.com/articles/s41598-023-42337-1). The project must neither claim 3ω for membrane fouling as a new discovery nor imply a novel validated industrial sensor. A differential thermal/electrical design with an independent protected reference is a **hypothesis**, not established novel intellectual property. Check patents and research before claiming novelty.

### Three contenders

**A. Protected third reference:** adds an independent R-G observable; can address the model identifiability gap if G remains clean and comparable. Cost/complexity: three coupons, extra acquisition, matching and service proof. Key failure: G fouls, or flow/chemistry no longer match.

**B. Periodic cleaning/blank challenge:** cheaper physical strategy, plausible maintenance pattern; must actually demonstrate the challenge's recovery and detectability. Risks: chemical/flow cross-contamination, pressure changes, transient signal, erosion of sensing interface.

**C. Conventional multi-sensor fusion and abstention:** strong baseline already beats Rev D on S1 and NC5. Remains the default practical option until the additional witness physically outperforms it on cases where CP and mixed fouling confound measurements. Do not automatically choose a new chip when existing sensors suffice.

**Minimal decision:** test the third-arm's independent information using a coupon-level wet experiment. If it doesn't beat B or C under matched resources, stop adding complexity.
