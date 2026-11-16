# Open challenge: reducing AI cooling's real water burden

Computing infrastructure consumes water both **at a site** and **upstream through electricity generation**. More accurate sensing could help, but better measurement is not the same thing as measured savings.

We are sharing free, offline, reproducible tools for checking data-center water evidence and for separating cooling-plant improvements from claims of novel sensor performance. The work includes known limitations and negative tests. We invite technicians, cooling engineers, water researchers, and AI infrastructure teams to challenge it.

## What you can do today

1. Run the offline CSV audit using the explicitly constructed example. Compare its water and energy accounting against your own methods.
2. Run the scenario comparison with **matched equipment**; observe that identical assumptions yield no novel-sensor benefit.
3. Reproduce the case where dry cooling lowers onsite water while higher electricity-related water use offsets the apparent gain.
4. Identify missing measurements, units, physical constraints, or incumbent systems that our research has not modeled.

If you have **permission to share** anonymized facility water, cooling, power, or weather datasets under an appropriate license, submit a description or a minimal synthetic reproduction in a GitHub issue. Do **not** post confidential telemetry, site access, personal data, credentials, proprietary customer records, or facility security details.

## What would count as a breakthrough?

A replicated comparison where additional measurement or active identification reveals a fault that competent conventional systems miss, changes a *safe, owner-authorized* decision, and measurably reduces **net water consumption** at matched compute output and reliability. Account for extra electricity, source-water impacts, discharge, local conditions, capital and maintenance costs. Run controlled holdouts and report false alerts, missed dangerous faults and abstentions.

**No independent facility has validated this work. The tool does not control cooling equipment.** The previous private research model's ~70% modeled water delta came predominantly from assumed *cooling plant design changes*, not a demonstrated OpenLine sensor advantage.

The work is free to inspect, reproduce, critique and extend under the repository's Apache-2.0 license. Contributions that disprove the idea are as welcome as ones that improve it.

## 004 model challenge — build or break a cooling design

Try `python3 water_audit.py design --site data/site_phoenix_arid.json --weather data/weather_phoenix_sample.csv --tariff data/tariff_phoenix.json --output-dir out_phoenix`. This generates cooling-plant scenarios, conservative chemistry screening, cost-incidence alternatives and an equipment boundary. All sample weather, prices and loads are **constructed inputs** and should not be mistaken for site claims.

Can you supply a lawful open dataset with independently calibrated wet-bulb/IT heat load, CDU inlet, cooling tower makeup and blowdown, and site electricity for the same time intervals? Or show an established tower optimizer or vendor design this model has missed? A decisive critique is worth more than another synthetic savings headline.

Do **not** use the result for live plant actuation, chemical dosing, approved equipment purchases, or public statements of observed savings.
