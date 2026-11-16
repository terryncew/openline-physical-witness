# Agent guide — OpenLine Physical Witness

This is a **public scientific research artifact**, not a running instrument or an autonomous command-and-control system. This file is navigation and evidence policy for researchers, coding assistants, and indexing agents.

## Ground truth and evidence levels

1. **Original frozen release:** `v0.4.0-rc4` (Release 004) contains reproducible **synthetic** equations, comparator models, CAD concepts and host software. Treat its physical-accuracy predictions as hypotheses. The immutable tag is distinct from current `main`.
2. **Benchtop 005:** `experiments/benchtop-005/` explores open-source impedance hardware and a first real fouling challenge. It includes host-tested code, but neither a manufacturer-qualified PCB nor running hardware I/O drivers. Its part prices are **not** a verified purchase-ready BOM.
3. **Reference 006:** `experiments/reference-006/` contains an exact-arithmetic demonstration of two-arm ambiguity and conditional three-arm observability, plus host-tested fault screening and a physical test protocol. It **does not** fix NC5 in a real device.
4. **Physical evidence:** none yet. There are **zero fabricated wafers, assembled PCBs, wet-lab trials or demonstrated physical accuracy results**.

## Read these files first

- `README.md` — scientific purpose, evolution 004 → 005 → 006 and reproduction commands.
- `RESEARCH_STATUS.md` — current state, failures, scope and next disprovable experiment.
- `experiments/README.md` — direct paths to later research.
- `experiments/reference-006/design/LAB_HANDOFF.md` — independent physical testing and fair baseline.
- `CLAIMS_AND_FALSIFIERS.md`, `HONEST_LIMITATIONS.md` — original detailed synthetic claims and their boundaries.

## Reproduction and integrity

- Original 004: `bash ./REPRODUCE_OTDB_APW_RELEASE_004.sh` after installing `requirements.txt` in Python 3.11 and GCC.
- 005: `(cd experiments/benchtop-005 && bash VERIFY_CANDIDATE.sh)`.
- 006: `(cd experiments/reference-006 && bash VERIFY_RESEARCH_ONLY.sh)`.
- Root SHA256 manifests record the original 004 file set (including the current main-branch README); supplemental packages contain their own checksums. Do not silently modify tracked snapshots or infer that an unlisted file is included in a frozen release.

## Research integrity

State whether a result is analytical, modeled, host-tested, CAD-reviewed or **physically measured**. Do not describe test software as operational firmware; concept diagrams as manufactured hardware; a 48-pin transcription as a manufacturer-approved board; a proposed protocol as preregistered; or LBNL/NJIT/other researchers as partners or endorsers. The NC5 **71.17% unflagged synthetic error** and the no-concentration-polarization baseline loss remain open evidence, not past successes.

Physical acceptance requires vendor-verified full pin/footprint routing, native CAD ERC/DRC, firmware acquisition and calibration, protected-reference cleanliness, blind real fouling measurements, and a competent conventional comparator on the same apparatus. Do not claim superiority if a conventional design wins. Host checks must never be interpreted as authorization to construct, energize or deploy experimental equipment.

Independent contributions, counterexamples, replication and physical measurements are welcome through normal public GitHub issues or PRs; do not solicit undisclosed private archives or secrets. Any new claims must provide measured or executable evidence and a clear falsifier.
