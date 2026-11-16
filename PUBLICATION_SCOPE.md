# Publication scope and validation limits

This repository contains only the **OTDB-APW Rev D computational research candidate** and a proposed external physical test. It is neither a complete OpenLine system nor a demonstration of the entire autonomous research workflow. No private workspaces, model weights, private conversation records, access tokens, unpublished internal handoffs, or closed-loop deployment credentials are part of this release.

**What a reproducer validates:** local execution of numerical models, comparison of four synthetic architectures in stated synthetic regimes, code-level sensor estimation, structural schematic checks, C99 firmware-core execution on a host compiler, and repeatable generated reports.

**What it does not validate:** physical sensor accuracy, measured manufacturer instrument performance, environmental durability, lab/national-lab affiliation or endorsement, process/foundry compatibility, or autonomous intelligence superiority. The cited LBNL and NJIT papers are independent prior art and experimental inspirations; their raw experimental data were **not** supplied to this project.

**Known safety failure:** the model's default reference-arm integrity screen fails to catch partial reference-arm fouling (NC5); in the published synthetic benchmark this yields 71.17% mean thickness error. A later exploratory guard was tested separately in simulation but is not included, qualified, or represented as an approved repair here. Do not use this prototype for process control.

The wet-loop test design in `BLIND_LAB_TEST_PROTOCOL.md` is **proposed and pre-specified, not independently registered**, and no external researcher has agreed to perform it. Native KiCad ERC, board layout validation, fab signoff, and actual measurements are explicit holds. Publication alone is not external verification.

No private input files are required for the research reproduction script. Open-source license and third-party references are documented in `LICENSE` and `THIRD_PARTY_NOTICES.md`.
