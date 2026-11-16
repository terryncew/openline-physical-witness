# Third-Party Licenses, Datasheets & Scientific Provenance Inventory

## 1. Runtime & Scientific Software Dependencies (External Environment)
No proprietary binaries, third-party source trees, or unverified neural network weights (`.onnx`) are bundled inside this standalone public release archive. The simulation and verification suite executes on standard open-source scientific Python and GCC packages:

| Dependency | Pinned Version | License | Role in Release Candidate 004 |
| :--- | :--- | :--- | :--- |
| `Python` | `3.11+` | PSF License Agreement | Core execution runtime and `unittest` test runner |
| `numpy` | `2.1.3` | BSD-3-Clause | Linear algebra, Cauer RC ladder, and Gauss-Newton solvers |
| `scipy` | `1.15.2` | BSD-3-Clause | Reference numerical routines |
| `matplotlib` | `3.10.1` | PSF-based / BSD-compatible | Generation of technical architecture and benchmark figures |
| `shapely` | `2.1.2` | BSD-3-Clause | Geometric polygon width/spacing checks on `otdb_apw_rev_b.gds` |
| `gcc` | `11.0+` | GPLv3 with GCC Runtime Exception | Compilation of `otdb_apw_firmware_core.c` into `build_outputs/libotdb_firmware.so` |

## 2. Prior-Art Scientific Literature (Inspiration & Baseline Methodology Only)
No experimental datasets from external institutions are bundled in this archive. All benchmark traces are generated synthetically by `IndependentMismatchWorldGenerator`:
1. **LBNL Operando Crossflow SAXS/WAXS Prior Art**: Mostafa Nassr et al., *"Crossflow membrane filtration system for operando fouling characterization using transmission x-ray scattering,"* *Rev. Sci. Instrum.* **96**(6), 065209 (2025), [DOI: 10.1063/5.0264117](https://pubs.aip.org/aip/rsi/article/96/6/065209/3350882/Crossflow-membrane-filtration-system-for-operando).
2. **NJIT 3D Impedimetric Microfluidic Membrane-Mimic (`IM3`) Prior Art**: Najamuddin Naveed Khaja, Sreerag Kaaliveetil, Niranjan Haridas Menon, Sushma Yadav, Chetan Prakash Sharma, and Sagnik Basuray, *"3D Impedimetric Microfluidic Membrane-Mimic Cassette (IM3) with Interdigitated Electrodes for Fouling Analysis at Membrane Interfaces,"* *ACS Appl. Mater. Interfaces* **18**(17), 25382–25395 (2026), [DOI: 10.1021/acsami.5c26362](https://pmc.ncbi.nlm.nih.gov/articles/PMC13154124/) (CC-BY 4.0).
3. **Cahill $3\omega$ Electro-Thermal Method**: David G. Cahill, *"Thermal conductivity measurement from 30 to 750 K: The $3\omega$ method,"* *Rev. Sci. Instrum.* **61**(2), 802–808 (1990), [DOI: 10.1063/1.1141498](https://doi.org/10.1063/1.1141498).
4. **ALD $\text{Al}_2\text{O}_3 / \text{HfO}_2$ Aqueous Passivation Stability**: Abdulagatov et al., *ACS Appl. Mater. Interfaces* (2011), [https://pubmed.ncbi.nlm.nih.gov/22032254/](https://pubmed.ncbi.nlm.nih.gov/22032254/).

## 3. Manufacturer Component Datasheets Referenced in `otdb_apw_afe_rev_d.kicad_sch`
* **Analog Devices `AD5940/AD5941`**: [https://www.analog.com/media/en/technical-documentation/data-sheets/ad5940-5941.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/ad5940-5941.pdf)
* **Analog Devices `AD8421BRZ`**: [https://www.analog.com/media/en/technical-documentation/data-sheets/ad8421.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/ad8421.pdf)
* **Analog Devices `AD5683RBRMZ` (Single-Channel 16-Bit nanoDAC+)**: [https://www.analog.com/en/products/ad5683r.html](https://www.analog.com/en/products/ad5683r.html)
* **Analog Devices `ADP7118AUJZ-3.3-R7` (+3.3 V Low-Noise CMOS LDO)**: [https://www.analog.com/media/en/technical-documentation/data-sheets/adp7118.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/adp7118.pdf)
* **Analog Devices `ADM8829ARTZ` (Switched-Capacitor Voltage Inverter)**: [https://www.analog.com/media/en/technical-documentation/data-sheets/adm8828_8829.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/adm8828_8829.pdf)
* **Analog Devices `ADP7182AUJZ-2.5-R7` (-2.5 V Low-Noise Negative LDO)**: [https://www.analog.com/media/en/technical-documentation/data-sheets/adp7182.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/adp7182.pdf)
* **STMicroelectronics `STM32G474CBT6`**: [https://www.st.com/resource/en/datasheet/stm32g474cb.pdf](https://www.st.com/resource/en/datasheet/stm32g474cb.pdf)
