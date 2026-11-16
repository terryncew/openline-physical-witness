# Equipment, Permitting & Safety Boundary Specification — ASHBURN_VA_10MW_AI_CLUSTER

## 1. Physical Loop Separation
- **Boundary A (TCS — Closed Server/CDU Loop)**: PG25 or inhibited DI water. Recirculating volume is NOT water consumption.
- **Boundary B (FWS — Cooling Tower / Dry Cooler / Hybrid)**: Consumes water via latent evaporation ($E$) and drift ($D$), and discharges blowdown ($B$) to sewer.
- **Boundary C (Upstream Grid Electricity)**: Consumes thermoelectric cooling water at the power plant across BOTH IT server kWh and cooling kWh.

## 2. Hard Operational & Safety Boundaries
- **No Live Actuation**: `water_audit.py` and `solutions.py` are offline design and auditing tools. They never connect to or actuate PLCs, BACnet/Modbus registers, pumps, or chemical dosing valves.
- **Chemical & Legionella Signoff**: Raising cooling-tower Cycles of Concentration (`S1`) or blending reclaimed water (`S4`) requires a licensed water-treatment engineer, ASHRAE Standard 188 Legionella water-management plan, and municipal discharge permit verification.
- **Unpriced / Site-Specific Items Flagged `NOT_READY_FOR_PROCUREMENT`**: Union pipefitting labor, structural roof/pad engineering for dry coolers or TES tanks, utility interconnection studies, and municipal sewer deduct meter certification must be quoted locally.
