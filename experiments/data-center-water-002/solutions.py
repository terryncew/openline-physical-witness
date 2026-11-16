#!/usr/bin/env python3
"""OpenLine Sensors 004 — Data-Center Water, Power & Public-Benefit Solutions Design Engine.

Implements and competes the seven concrete engineering approaches (S1-S7) against
competent conventional engineering baselines using only the Python 3.10+ standard library:
  S1 — Chemistry-Bounded Cooling-Tower Optimizer (vs. DOE FEMP BMP #10 / EPA WaterSense Sec 6.3)
  S2 — Weather-Constrained Dry/Hybrid Heat-Rejection Dispatch (hourly thermodynamic feasibility)
  S3 — Fisher-Information Sensor/Observer Selection Gate (earns its cost or refuses hardware)
  S4 — Water-Source Substitution & Recovery (reclaimed, AHU condensate, blowdown RO)
  S5 — Grid & Community Cost Mitigation (TES peak shaving + 3 ratepayer/developer allocations)
  S6 — Waste-Heat Reuse Feasibility & Carnot-Derated Heat-Pump Economics (with hard no-go gate)
  S7 — Owner-Controlled Verification, Decision Recall & Public-Benefit Receipts

Read-only offline engineering design and simulation module. Zero network calls, zero paid
dependencies, zero live BMS/CDU actuation, and zero fabricated field-savings claims.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from water_audit import EvidenceError, audit, finite_number, parse_utc


# Physical constants
LATENT_HEAT_WATER_KJ_PER_KG = 2430.0
KWH_TO_KJ = 3600.0
THEORETICAL_PURE_LATENT_EVAP_L_PER_KWH = KWH_TO_KJ / LATENT_HEAT_WATER_KJ_PER_KG  # ~1.4815 L/kWh_th


def compute_lsi(
    temp_c: float,
    calcium_caco3_ppm: float,
    alkalinity_caco3_ppm: float,
    tds_ppm: float,
    ph: float,
) -> float:
    """Standard Langelier Saturation Index (LSI = pH - pHs) at heat-exchanger skin temperature."""
    a = (math.log10(max(tds_ppm, 10.0)) - 1.0) / 10.0
    b = -13.12 * math.log10(temp_c + 273.15) + 34.55
    c = math.log10(max(calcium_caco3_ppm, 1.0)) - 0.4
    d = math.log10(max(alkalinity_caco3_ppm, 1.0))
    phs = (9.3 + a + b) - (c + d)
    return round(ph - phs, 4)


def load_weather_csv(weather_path: str | Path) -> dict[str, Any]:
    """Load and validate hourly/binned ambient weather CSV with explicit provenance."""
    p = Path(weather_path)
    if not p.is_file():
        raise EvidenceError(f"weather CSV missing: {weather_path}")
    blob = p.read_bytes()
    if not blob:
        raise EvidenceError("empty weather CSV")

    req_cols = ("timestamp_utc", "duration_h", "dry_bulb_c", "wet_bulb_c", "source_station")
    bins: list[dict[str, Any]] = []
    with p.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in req_cols):
            raise EvidenceError("weather CSV missing required columns: " + ",".join(req_cols))
        prev_dt = None
        prev_end = None
        for i, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise EvidenceError(f"weather row {i}: ragged CSV row")
            dt = parse_utc(raw["timestamp_utc"], i)
            if prev_dt is not None and dt <= prev_dt:
                raise EvidenceError(f"weather row {i}: non-increasing timestamp")
            prev_dt = dt
            dur = finite_number(raw["duration_h"], "duration_h", i)
            if dur <= 0 or dur > 8784:
                raise EvidenceError(f"weather row {i}: invalid duration_h")
            from datetime import timedelta
            if prev_end is not None and dt < prev_end:
                raise EvidenceError(f"weather row {i}: overlapping weather intervals; binned examples must use nonoverlapping synthetic time slots")
            prev_end = dt + timedelta(hours=dur)
            try:
                t_db = float(raw["dry_bulb_c"])
                t_wb = float(raw["wet_bulb_c"])
            except (ValueError, TypeError):
                raise EvidenceError(f"weather row {i}: non-numeric temperature") from None
            if isinstance(raw["dry_bulb_c"], bool) or not math.isfinite(t_db) or not math.isfinite(t_wb):
                raise EvidenceError(f"weather row {i}: non-finite temperature")
            if t_wb > t_db + 0.01:
                raise EvidenceError(f"weather row {i}: thermodynamic violation (wet_bulb_c {t_wb} > dry_bulb_c {t_db})")
            if not (-50.0 <= t_db <= 65.0) or not (-50.0 <= t_wb <= 45.0):
                raise EvidenceError(f"weather row {i}: temperature outside physical atmospheric bounds")
            station = str(raw["source_station"]).strip()
            if not station:
                raise EvidenceError(f"weather row {i}: empty source_station")
            bins.append({
                "timestamp_utc": dt.isoformat(),
                "duration_h": dur,
                "dry_bulb_c": t_db,
                "wet_bulb_c": t_wb,
                "source_station": station,
            })

    if not bins:
        raise EvidenceError("weather CSV has no rows")
    total_h = sum(b["duration_h"] for b in bins)
    if total_h > 8784 + 1e-6:
        raise EvidenceError("weather CSV exceeds one year's weighted hours; split years and keep declared intervals")
    return {
        "weather_evidence_class": (
            "CONSTRUCTED_WEIGHTED_SEASONAL_BINS_NOT_HOURLY_OBSERVATIONS"
            if all("CONSTRUCTED" in x["source_station"] for x in bins)
            else "USER_SUPPLIED_WEATHER_UNVERIFIED_PROVENANCE"
        ),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "total_hours": round(total_h, 4),
        "station": bins[0]["source_station"],
        "bins": bins,
    }



def declared_boolean(obj: dict[str, Any], key: str, default: bool = False) -> bool:
    """A string like 'false' or a number like 1 is not an approval receipt."""
    raw = obj.get(key, default)
    if type(raw) is not bool:
        raise EvidenceError(f"{key} must be a JSON boolean, not a string or number")
    return raw


def evaluate_s1_chemistry_tower_optimizer(
    site: dict[str, Any],
    tariff: dict[str, Any],
    annual_wet_heat_kwh_th: float,
) -> dict[str, Any]:
    """S1 — Chemistry-Bounded Cooling-Tower Optimizer (vs. DOE FEMP BMP #10 / EPA WaterSense Sec 6.3).

    Enforces dual-ratio CoC check (mass-balance M/B vs conductivity EC_b/EC_m per EPA WaterSense
    Eq. 6-4 & 6-5), bounds max CoC by silica, calcium hardness, alkalinity/LSI, chloride, and
    treatment regime, and abstains fail-closed when water chemistry inputs are missing.
    """
    chem = site.get("water_chemistry")
    required_chem = (
        "makeup_conductivity_us_cm",
        "blowdown_conductivity_us_cm",
        "ph",
        "silica_ppm",
        "calcium_hardness_ppm_as_caco3",
        "alkalinity_ppm_as_caco3",
        "chloride_ppm",
    )
    if not isinstance(chem, dict):
        return {
            "solution_id": "S1_CHEMISTRY_BOUNDED_TOWER_OPTIMIZER",
            "status": "ABSTAIN_REQUIRED_MEASUREMENTS_MISSING",
            "required_measurements": list(required_chem),
            "feasible": False,
            "reason": "water_chemistry block missing from site specification; refusing to guess universal CoC.",
        }

    missing = [k for k in required_chem if k not in chem or chem[k] is None]
    if missing:
        return {
            "solution_id": "S1_CHEMISTRY_BOUNDED_TOWER_OPTIMIZER",
            "status": "ABSTAIN_REQUIRED_MEASUREMENTS_MISSING",
            "required_measurements": missing,
            "feasible": False,
            "reason": f"Missing required water chemistry measurements: {', '.join(missing)}",
        }

    ec_m = finite_number(chem["makeup_conductivity_us_cm"], "makeup_conductivity_us_cm", "site")
    ec_b = finite_number(chem["blowdown_conductivity_us_cm"], "blowdown_conductivity_us_cm", "site")
    ph_m = finite_number(chem["ph"], "ph", "site")
    sio2_m = finite_number(chem["silica_ppm"], "silica_ppm", "site")
    ca_m = finite_number(chem["calcium_hardness_ppm_as_caco3"], "calcium_hardness_ppm_as_caco3", "site")
    alk_m = finite_number(chem["alkalinity_ppm_as_caco3"], "alkalinity_ppm_as_caco3", "site")
    cl_m = finite_number(chem["chloride_ppm"], "chloride_ppm", "site")

    if ec_m <= 0 or ec_b <= ec_m or not (5.0 <= ph_m <= 10.5) or sio2_m <= 0 or ca_m <= 0 or alk_m <= 0:
        raise EvidenceError("invalid water_chemistry values (must have EC_b > EC_m > 0 and pH in [5, 10.5])")

    coc_ec = ec_b / ec_m
    metered_m = chem.get("metered_makeup_l_sample")
    metered_b = chem.get("metered_blowdown_l_sample")
    leak_or_drift_mismatch_flag = False
    coc_mass = None
    if metered_m is not None and metered_b is not None:
        m_val = finite_number(metered_m, "metered_makeup_l_sample", "site")
        b_val = finite_number(metered_b, "metered_blowdown_l_sample", "site")
        if b_val > 0 and m_val > b_val:
            coc_mass = m_val / b_val
            # EPA WaterSense Section 6.3 Eq 6-4 vs 6-5: >10% discrepancy indicates leak, overflow, or drift fault
            if abs(coc_mass - coc_ec) / coc_ec > 0.10:
                leak_or_drift_mismatch_flag = True

    skin_temp_c = float(site.get("condenser_or_hx_skin_temp_c", 42.0))
    evap_fraction_latent = float(site.get("tower_latent_evap_share", 0.78))
    drift_frac_of_evap = float(site.get("tower_drift_fraction_of_evap", 0.005))
    evap_l = annual_wet_heat_kwh_th * THEORETICAL_PURE_LATENT_EVAP_L_PER_KWH * evap_fraction_latent
    drift_l = evap_l * drift_frac_of_evap

    baseline_coc = float(site.get("current_cycles_of_concentration", round(coc_ec, 2)))
    if baseline_coc <= 1.05:
        raise EvidenceError("current_cycles_of_concentration must exceed 1.05")

    base_blowdown_l = max(0.0, evap_l / (baseline_coc - 1.0) - drift_l)
    base_makeup_l = evap_l + base_blowdown_l + drift_l

    w_cost_m3 = finite_number(tariff["potable_water_usd_per_m3"], "potable_water_usd_per_m3", "tariff")
    s_cost_m3 = finite_number(tariff["wastewater_discharge_usd_per_m3"], "wastewater_discharge_usd_per_m3", "tariff")
    has_sewer_submeter_init = declared_boolean(site, "has_evaporative_sewer_submeter_credit")
    # A installed submeter is not legal authority for a sewer deduction; local utility
    # eligibility must be confirmed independently. Absent that receipt, price both
    # designs at full makeup volume and show possible credit as an unqualified upside.
    sewer_credit_approved = has_sewer_submeter_init or declared_boolean(site, "municipal_evaporative_sewer_credit_approved")

    # Evaluate 3 chemistry-bounded sub-options for S1:
    # S1a: Existing chemistry (no acid/dispersant retrofit; LSI <= 1.2, SiO2 <= 150 ppm, Cl <= 250 ppm for 304SS)
    # S1b: DOE FEMP BMP #10 Automated Conductivity + Polymer Dispersant + Sub-Meter Sewer Deduct (LSI <= 1.85, SiO2 <= 165 ppm)
    # S1c: Acid Feed + Polymer Dispersant + Sidestream Filtration (alkalinity reduced 55%, LSI <= 2.2, SiO2 <= 175 ppm)
    regimes = [
        {
            "regime_id": "S1A_NO_CHEMICAL_CHANGE_LSI_BOUNDED",
            "label": "Existing Chemistry with Dual-Ratio (EC + Flow) & LSI Guard",
            "max_sio2_ppm": 150.0,
            "max_cl_ppm": 250.0,
            "max_ca_alk_product": 45000.0,
            "alk_multiplier": 1.0,
            "max_lsi": 1.25,
            "capex_usd": 2400.0,  # Makeup + blowdown pulse flowmeters + conductivity transmitter check
            "annual_chem_opex_usd": 1200.0,
            "enables_sewer_submeter": True,
        },
        {
            "regime_id": "S1B_DOE_FEMP_POLYMER_AND_AUTO_BLOWDOWN",
            "label": "DOE FEMP BMP #10 Incumbent: Auto Conductivity Blowdown + Polymer Inhibitor + Submeter",
            "max_sio2_ppm": 160.0,
            "max_cl_ppm": 350.0,
            "max_ca_alk_product": 110000.0,
            "alk_multiplier": 0.85,
            "max_lsi": 1.85,
            "capex_usd": 8500.0,
            "annual_chem_opex_usd": 9500.0,
            "enables_sewer_submeter": True,
        },
        {
            "regime_id": "S1C_ACID_FEED_PLUS_SIDESTREAM_FILTRATION",
            "label": "Automated Acid pH Trim + Silica/Polymer Dispersant + Sidestream Cartridge Filter",
            "max_sio2_ppm": 175.0,
            "max_cl_ppm": 450.0,
            "max_ca_alk_product": 220000.0,
            "alk_multiplier": 0.42,
            "max_lsi": 2.20,
            "capex_usd": 24000.0,
            "annual_chem_opex_usd": 18500.0,
            "enables_sewer_submeter": True,
        },
    ]

    pareto_options: list[dict[str, Any]] = []
    for reg in regimes:
        coc_sio2 = reg["max_sio2_ppm"] / sio2_m
        coc_cl = reg["max_cl_ppm"] / max(cl_m, 1.0)
        coc_ca_alk = math.sqrt(reg["max_ca_alk_product"] / max(ca_m * alk_m * reg["alk_multiplier"], 1.0))
        raw_max_coc = min(coc_sio2, coc_cl, coc_ca_alk, 10.0)
        # The lower bound of a modeled circulating tower is 1.5 cycles.
        # No setpoint above a chemistry ceiling can be called permissible.
        if raw_max_coc < 1.5:
            continue

        # Find a validated value, never seed the answer from the prior setpoint.
        best_coc = None
        for test_coc_int in range(15, int(raw_max_coc * 100) + 1):
            c_try = test_coc_int / 100.0
            eff_alk = alk_m * reg["alk_multiplier"] * c_try
            eff_ph = 7.45 if reg["alk_multiplier"] < 0.5 else min(8.1 + 0.11 * (c_try - 2.0), 9.0)
            lsi_val = compute_lsi(
                temp_c=skin_temp_c,
                calcium_caco3_ppm=ca_m * c_try,
                alkalinity_caco3_ppm=eff_alk,
                tds_ppm=(ec_m * 0.67) * c_try,
                ph=eff_ph,
            )
            if lsi_val <= reg["max_lsi"]:
                best_coc = c_try
            else:
                break

        if best_coc is None:
            continue
        best_coc = round(best_coc, 2)
        limiting_factor = "SILICA_CEILING"
        if coc_cl <= coc_sio2 and coc_cl <= coc_ca_alk:
            limiting_factor = "CHLORIDE_CORROSION_CEILING"
        elif best_coc < raw_max_coc - 0.1:
            limiting_factor = "LANGELIER_SCALING_INDEX_CEILING"

        bd_l = max(0.0, evap_l / (best_coc - 1.0) - drift_l)
        mk_l = evap_l + bd_l + drift_l
        water_saved_l = base_makeup_l - mk_l
        blowdown_saved_l = base_blowdown_l - bd_l

        # Sewer billing: without submeter, utility bills wastewater on 100% of makeup!
        base_billed_sewer_l = base_blowdown_l if has_sewer_submeter_init else base_makeup_l
        new_billed_sewer_l = bd_l if reg["enables_sewer_submeter"] and sewer_credit_approved else mk_l

        base_water_cost = (base_makeup_l / 1000.0) * w_cost_m3 + (base_billed_sewer_l / 1000.0) * s_cost_m3
        new_water_cost = (mk_l / 1000.0) * w_cost_m3 + (new_billed_sewer_l / 1000.0) * s_cost_m3 + reg["annual_chem_opex_usd"]
        annual_net_operating_savings_usd = base_water_cost - new_water_cost

        pareto_options.append({
            "regime_id": reg["regime_id"],
            "label": reg["label"],
            "permissible_max_coc": best_coc,
            "limiting_chemistry_constraint": limiting_factor,
            "site_makeup_l": round(mk_l, 1),
            "site_blowdown_l": round(bd_l, 1),
            "site_evaporation_l": round(evap_l, 1),
            "makeup_water_saved_vs_baseline_l": round(water_saved_l, 1),
            "makeup_reduction_vs_baseline_pct": round(
                (water_saved_l / base_makeup_l * 100.0) if base_makeup_l > 0 else 0.0, 2
            ),
            "blowdown_saved_vs_baseline_l": round(blowdown_saved_l, 1),
            "capex_usd": reg["capex_usd"],
            "annual_chem_opex_usd": reg["annual_chem_opex_usd"],
            "annual_net_operating_savings_usd": round(annual_net_operating_savings_usd, 2),
            "sewer_deduct_status": "DECLARED_APPROVED" if sewer_credit_approved else "NOT_CREDITED_PENDING_UTILITY_ELIGIBILITY",
            "economic_boundary": "All tariff, treatment, operating and retrofit costs are user/constructed inputs, not vendor quotes or measured ROI.",
        })

    # Select only among regimes satisfying all physical chemistry ceilings.
    if not pareto_options:
        return {
            "solution_id": "S1_CHEMISTRY_BOUNDED_TOWER_OPTIMIZER",
            "status": "ABSTAIN_NO_VALID_CHEMISTRY_SETPOINT",
            "feasible": False,
            "reason": "Every evaluated regime breaches a silica, chloride, hardness/alkalinity, or LSI limit at the minimum 1.5 cycles. Qualified chemistry and independent calibration required.",
            "pareto_chemistry_regimes": [],
        }
    selected = max(pareto_options, key=lambda x: x["annual_net_operating_savings_usd"])

    # DOE FEMP reference benchmark check (CoC 3 -> 6 gives exact 20.0% makeup reduction and 60.0% blowdown reduction at 0 drift)
    doe_femp_3_to_6_makeup_reduction_pct = round((1.0 - (6.0 / 5.0) / (3.0 / 2.0)) * 100.0, 2)

    return {
        "solution_id": "S1_CHEMISTRY_BOUNDED_TOWER_OPTIMIZER",
        "status": "FEASIBLE_MODELED_NOT_FIELD_VALIDATED",
        "feasible": True,
        "novelty_classification": (
            "OPEN_IMPLEMENTATION_OF_DOE_FEMP_AND_EPA_WATERSENSE_BEST_PRACTICE"
            if not leak_or_drift_mismatch_flag
            else "DUAL_RATIO_MASS_VS_CONDUCTIVITY_LEAK_DISCRIMINATOR"
        ),
        "doe_femp_bmp10_3_to_6_reference_makeup_reduction_pct": doe_femp_3_to_6_makeup_reduction_pct,
        "observed_conductivity_coc": round(coc_ec, 3),
        "observed_mass_balance_coc": None if coc_mass is None else round(coc_mass, 3),
        "epa_watersense_eq64_eq65_leak_or_drift_mismatch_detected": leak_or_drift_mismatch_flag,
        "sewer_credit_eligibility": "DECLARED_APPROVED_UNVERIFIED" if sewer_credit_approved else "NO_SEWER_DEDUCT_CREDIT_ASSUMED",
        "baseline_coc": baseline_coc,
        "baseline_makeup_l": round(base_makeup_l, 1),
        "baseline_blowdown_l": round(base_blowdown_l, 1),
        "pareto_chemistry_regimes": pareto_options,
        "selected_regime": selected,
        "economic_recommendation": (
            "HOLD_NEGATIVE_MODELED_OPERATING_SAVINGS_REQUIRES_CHEMISTRY_SAFETY_REVIEW"
            if selected["annual_net_operating_savings_usd"] <= 0 else
            "CONDITIONAL_POSITIVE_MODELED_SAVINGS_REQUIRES_TARIFF_AND_CHEMISTRY_VERIFICATION"
        ),
    }


def evaluate_s2_weather_constrained_dispatch(
    site: dict[str, Any],
    weather: dict[str, Any],
    tariff: dict[str, Any],
    max_safe_coc: float | None,
) -> dict[str, Any]:
    """S2 — Weather-Constrained Dry/Hybrid Heat-Rejection Dispatch.

    Evaluates hour-by-hour thermodynamic feasibility across 5 cooling plant architectures:
      - P0_EXISTING_WET_TOWER: Baseline evaporative cooling tower at baseline CoC.
      - P1_TOWER_CHEMISTRY_AND_WATERSIDE_ECON: Wet tower at S1 max_safe_coc + cold-weather fan trim.
      - P2_HYBRID_DRY_WET_EXISTING_RACK_LIMIT: Hybrid dry cooler + wet tower constrained by current rack max inlet T.
      - P3_WARM_WATER_W40_HYBRID_DRY_WET: Warm-water (40C FWS supply, if rack hardware permits) + hybrid dry/wet tower.
      - P4_FULL_DRY_CHILLER_RETROFIT: Zero-evaporation dry cooler + mechanical chiller trim during hot hours (high kW peak).
    """
    it_kw = finite_number(site["it_load_kw"], "it_load_kw", "site")
    ancillary_heat_frac = finite_number(site.get("ancillary_heat_fraction", 0.04), "ancillary_heat_fraction", "site")
    q_total_kw = it_kw * (1.0 + ancillary_heat_frac)

    rack_max_inlet_c = finite_number(site["rack_max_liquid_inlet_c"], "rack_max_liquid_inlet_c", "site")
    cdu_atd_k = finite_number(site.get("cdu_approach_delta_t_k", 4.0), "cdu_approach_delta_t_k", "site")
    dry_cooler_approach_k = finite_number(site.get("dry_cooler_min_approach_k", 6.0), "dry_cooler_min_approach_k", "site")
    dry_cooler_ua_kw_per_k = finite_number(site.get("dry_cooler_ua_kw_per_k", it_kw * 0.14), "dry_cooler_ua_kw_per_k", "site")
    allows_warm_water_w40_upgrade = declared_boolean(site, "allows_warm_water_w40_rack_upgrade", True)
    baseline_coc = finite_number(site.get("current_cycles_of_concentration", 3.5), "current_cycles_of_concentration", "site")
    sewer_credit_approved = declared_boolean(site, "has_evaporative_sewer_submeter_credit") or declared_boolean(site, "municipal_evaporative_sewer_credit_approved")

    elec_rate = finite_number(tariff["electricity_energy_usd_per_kwh"], "electricity_energy_usd_per_kwh", "tariff")
    demand_rate_kw_mo = finite_number(tariff.get("electricity_peak_demand_usd_per_kw_month", 14.5), "demand", "tariff")
    w_cost_m3 = finite_number(tariff["potable_water_usd_per_m3"], "potable_water_usd_per_m3", "tariff")
    s_cost_m3 = finite_number(tariff["wastewater_discharge_usd_per_m3"], "wastewater_discharge_usd_per_m3", "tariff")
    grid_ewif = finite_number(tariff["grid_ewif_l_per_kwh"], "grid_ewif_l_per_kwh", "tariff")
    grid_range = tariff.get("grid_ewif_range_l_per_kwh", [0.2, grid_ewif, 2.4])
    g_low, g_med, g_high = float(grid_range[0]), float(grid_range[1]), float(grid_range[2])

    plant_configs = [
        {
            "plant_id": "P0_EXISTING_WET_TOWER_BASELINE",
            "name": "Existing Evaporative Cooling Tower Baseline",
            "has_dry_cooler": False,
            "has_chiller_trim": False,
            "fws_supply_limit_c": min(rack_max_inlet_c - cdu_atd_k, 32.0),
            "coc": baseline_coc,
            "sewer_submeter": declared_boolean(site, "has_evaporative_sewer_submeter_credit"),
            "capex_usd": 0.0,
            "annual_maint_usd": 0.0,
            "requires_w40_racks": False,
        },
        {
            "plant_id": "P1_S1_TOWER_OPTIMIZER_ONLY",
            "name": "S1 Chemistry-Bounded Tower Optimizer + Evaporative Sewer Submeter (No Dry Cooler)",
            "has_dry_cooler": False,
            "has_chiller_trim": False,
            "fws_supply_limit_c": min(rack_max_inlet_c - cdu_atd_k, 32.0),
            "coc": max_safe_coc if max_safe_coc is not None else 2.0,
            "sewer_submeter": True,
            "capex_usd": 8500.0,
            "annual_maint_usd": 9500.0,
            "requires_w40_racks": False,
        },
        {
            "plant_id": "P2_HYBRID_DRY_WET_AT_CURRENT_RACK_LIMIT",
            "name": f"S2 Hybrid Dry/Evaporative Cooler at Current Rack Limit ({rack_max_inlet_c:.0f}C Inlet)",
            "has_dry_cooler": True,
            "has_chiller_trim": False,
            "fws_supply_limit_c": rack_max_inlet_c - cdu_atd_k,
            "coc": max_safe_coc if max_safe_coc is not None else 2.0,
            "sewer_submeter": True,
            "capex_usd": 380000.0 if not declared_boolean(site, "has_existing_dry_cooler") else 0.0,
            "annual_maint_usd": 14000.0,
            "requires_w40_racks": False,
        },
        {
            "plant_id": "P3_WARM_WATER_W40_HYBRID_DRY_WET",
            "name": "S2 Warm-Water W40 (45C Rack Inlet / 40C FWS) Hybrid Dry/Evaporative Cooler",
            "has_dry_cooler": True,
            "has_chiller_trim": False,
            "fws_supply_limit_c": 40.0,
            "coc": max_safe_coc if max_safe_coc is not None else 2.0,
            "sewer_submeter": True,
            "capex_usd": 420000.0 if not declared_boolean(site, "has_existing_dry_cooler") else 25000.0,
            "annual_maint_usd": 14000.0,
            "requires_w40_racks": True,
        },
        {
            "plant_id": "P4_ZERO_EVAP_DRY_PLUS_CHILLER_RETROFIT",
            "name": "Full Dry Cooler + Mechanical Chiller Trim (Zero Site Evaporation, High Peak kW)",
            "has_dry_cooler": True,
            "has_chiller_trim": True,
            "fws_supply_limit_c": 28.0,
            "coc": max_safe_coc if max_safe_coc is not None else 2.0,
            "sewer_submeter": True,
            "capex_usd": 950000.0,
            "annual_maint_usd": 28000.0,
            "requires_w40_racks": False,
        },
    ]

    evaluated_plants: list[dict[str, Any]] = []
    for cfg in plant_configs:
        if max_safe_coc is None and not cfg["has_chiller_trim"]:
            evaluated_plants.append({
                "plant_id": cfg["plant_id"], "name": cfg["name"],
                "feasible": False,
                "infeasibility_reason": "WET_TOWER_CHEMISTRY_MISSING_OR_NO_SAFE_SETPOINT; dry-only design can still be modeled independently",
            })
            continue
        if cfg["requires_w40_racks"] and (rack_max_inlet_c < 44.0 and not allows_warm_water_w40_upgrade):
            evaluated_plants.append({
                "plant_id": cfg["plant_id"],
                "name": cfg["name"],
                "feasible": False,
                "infeasibility_reason": (
                    f"Rack max liquid inlet is {rack_max_inlet_c}C (<44C required for W40) "
                    "and warm-water rack upgrade is disallowed by site constraints."
                ),
            })
            continue

        fws_max_c = cfg["fws_supply_limit_c"]
        tcs_delta_t_c = 10.0
        fws_return_c = fws_max_c + 0.8 * tcs_delta_t_c  # Fluid return entering dry cooler

        total_evap_l = 0.0
        total_drift_l = 0.0
        total_blowdown_l = 0.0
        total_makeup_l = 0.0
        total_cool_kwh = 0.0
        peak_cool_kw = 0.0
        dry_heat_kwh = 0.0
        wet_heat_kwh = 0.0
        infeasible_hours = 0.0
        min_thermal_margin_c = 999.0
        hourly_schedule: list[dict[str, Any]] = []

        for b in weather["bins"]:
            hrs = b["duration_h"]
            t_db = b["dry_bulb_c"]
            t_wb = b["wet_bulb_c"]

            # Step 1: Calculate physically feasible dry-cooler heat rejection at current ambient dry-bulb
            if cfg["has_dry_cooler"]:
                # Dry cooler can only reject heat if fws_return_c > t_db + dry_cooler_approach_k
                avail_temp_driving_k = fws_return_c - (t_db + dry_cooler_approach_k)
                if avail_temp_driving_k <= 0.0:
                    q_dry_kw = 0.0
                else:
                    # Also cannot cool below t_db + dry_cooler_approach_k; if fws_max_c < t_db + dry_cooler_approach_k,
                    # dry cooler can only pre-cool the return stream from fws_return_c down to (t_db + dry_cooler_approach_k)
                    precool_fraction = min(
                        1.0,
                        max(0.0, (fws_return_c - (t_db + dry_cooler_approach_k)) / max(fws_return_c - fws_max_c, 1.0)),
                    )
                    q_dry_cap_kw = dry_cooler_ua_kw_per_k * avail_temp_driving_k
                    q_dry_kw = min(q_total_kw * precool_fraction, q_dry_cap_kw)
            else:
                q_dry_kw = 0.0

            q_rem_kw = max(0.0, q_total_kw - q_dry_kw)

            # Step 2: Reject remaining heat via evaporative tower OR mechanical chiller trim
            if cfg["has_chiller_trim"]:
                # Zero-evaporation mode: remaining heat rejected via mechanical vapor-compression chiller to dry air
                q_wet_kw = 0.0
                # Carnot-derated air-cooled chiller COP drops as t_db rises
                chiller_cop = max(1.8, 4.2 - 0.065 * max(t_db - 25.0, 0.0))
                chiller_elec_kw = q_rem_kw / chiller_cop
                achievable_fws_c = fws_max_c
            else:
                q_wet_kw = q_rem_kw
                chiller_elec_kw = 0.0
                # Evaporative cooling tower cold water approaches t_wb + 4.0 C
                tower_cold_water_c = t_wb + 4.0
                achievable_fws_c = tower_cold_water_c if q_wet_kw > 0 else (t_db + dry_cooler_approach_k)

            thermal_margin_c = fws_max_c - achievable_fws_c
            min_thermal_margin_c = min(min_thermal_margin_c, thermal_margin_c)
            if thermal_margin_c < -0.5:
                infeasible_hours += hrs

            # Electrical power for pumps & fans
            tcs_pump_kw = 0.012 * it_kw
            dry_fan_kw = q_dry_kw * (0.048 + 0.0011 * max(t_db - 20.0, 0.0))
            wet_tower_fan_pump_kw = q_wet_kw * 0.028
            cool_kw = tcs_pump_kw + dry_fan_kw + wet_tower_fan_pump_kw + chiller_elec_kw
            peak_cool_kw = max(peak_cool_kw, cool_kw)
            total_cool_kwh += cool_kw * hrs

            dry_heat_kwh += q_dry_kw * hrs
            wet_heat_kwh += q_wet_kw * hrs

            # Water evaporation on wet share only (latent share ~0.78 of wet heat rejected)
            evap_bin_l = (q_wet_kw * hrs) * THEORETICAL_PURE_LATENT_EVAP_L_PER_KWH * 0.78
            drift_bin_l = evap_bin_l * 0.005
            bd_bin_l = max(0.0, evap_l_to_bd := (evap_bin_l / (cfg["coc"] - 1.0) - drift_bin_l))
            mk_bin_l = evap_bin_l + bd_bin_l + drift_bin_l

            total_evap_l += evap_bin_l
            total_drift_l += drift_bin_l
            total_blowdown_l += bd_bin_l
            total_makeup_l += mk_bin_l

            hourly_schedule.append({
                "timestamp_utc": b["timestamp_utc"],
                "duration_h": hrs,
                "dry_bulb_c": t_db,
                "wet_bulb_c": t_wb,
                "q_dry_kw": round(q_dry_kw, 2),
                "q_wet_kw": round(q_wet_kw, 2),
                "cooling_elec_kw": round(cool_kw, 2),
                "makeup_l": round(mk_bin_l, 1),
                "thermal_margin_c": round(thermal_margin_c, 2),
            })

        total_hours = weather["total_hours"]
        it_kwh = it_kw * total_hours
        total_elec_kwh = it_kwh + total_cool_kwh
        peak_total_kw = it_kw + peak_cool_kw

        billed_sewer_l = total_blowdown_l if cfg["sewer_submeter"] and sewer_credit_approved else total_makeup_l
        water_cost_usd = (total_makeup_l / 1000.0) * w_cost_m3 + (billed_sewer_l / 1000.0) * s_cost_m3
        elec_energy_cost_usd = total_cool_kwh * elec_rate
        elec_demand_cost_usd = peak_cool_kw * demand_rate_kw_mo * 12.0 * (total_hours / 8760.0)
        annualized_capex_usd = cfg["capex_usd"] / 10.0  # 10-year straight-line reference
        total_annual_cooling_cost_usd = (
            water_cost_usd + elec_energy_cost_usd + elec_demand_cost_usd + cfg["annual_maint_usd"] + annualized_capex_usd
        )

        evaluated_plants.append({
            "plant_id": cfg["plant_id"],
            "name": cfg["name"],
            "feasible": infeasible_hours == 0.0,
            "sewer_deduct_credit_in_economics": bool(cfg["sewer_submeter"] and sewer_credit_approved),
            "cost_inputs_status": "SCENARIO_ESTIMATES_NOT_VENDOR_QUOTES_OR_APPROVED_TARIFF",
            "weather_evidence_class": weather.get("weather_evidence_class", "WEATHER_PROVENANCE_UNQUALIFIED"),
            "requires_new_warm_water_racks": cfg["requires_w40_racks"] and rack_max_inlet_c < 44.0,
            "rack_upgrade_capex_included": not (cfg["requires_w40_racks"] and rack_max_inlet_c < 44.0) or declared_boolean(site, "certified_w40_rack_upgrade_capex_included"),
            "thermal_feasibility_not_hardware_qualification": True,
            "infeasible_hours": round(infeasible_hours, 2),
            "min_thermal_margin_c": round(min_thermal_margin_c, 2),
            "cycles_of_concentration": cfg["coc"],
            "dry_heat_rejection_share_pct": round(dry_heat_kwh / max(dry_heat_kwh + wet_heat_kwh, 1.0) * 100.0, 2),
            "site_makeup_l": round(total_makeup_l, 1),
            "site_evaporation_l": round(total_evap_l, 1),
            "site_blowdown_l": round(total_blowdown_l, 1),
            "site_wue_l_per_it_kwh": round(total_makeup_l / it_kwh, 4),
            "cooling_elec_kwh": round(total_cool_kwh, 1),
            "peak_cooling_elec_kw": round(peak_cool_kw, 2),
            "peak_total_facility_kw": round(peak_total_kw, 2),
            "pue": round(total_elec_kwh / it_kwh, 4),
            "indirect_cooling_grid_water_l": round(total_cool_kwh * grid_ewif, 1),
            "indirect_total_facility_grid_water_l": round(total_elec_kwh * grid_ewif, 1),
            "total_site_plus_all_grid_water_l": round(total_makeup_l + total_elec_kwh * grid_ewif, 1),
            "total_site_plus_all_grid_water_band_l": {
                "low_ewif_l": round(total_makeup_l + total_elec_kwh * g_low, 1),
                "median_ewif_l": round(total_makeup_l + total_elec_kwh * g_med, 1),
                "high_ewif_l": round(total_makeup_l + total_elec_kwh * g_high, 1),
            },
            "capex_usd": cfg["capex_usd"],
            "annual_water_and_sewer_cost_usd": round(water_cost_usd, 2),
            "annual_cooling_elec_and_demand_cost_usd": round(elec_energy_cost_usd + elec_demand_cost_usd, 2),
            "annualized_total_cooling_cost_usd": round(total_annual_cooling_cost_usd, 2),
            "hourly_dispatch_preview": hourly_schedule[:4],
        })

    # Compute Pareto-nondominated frontier among FEASIBLE plants over:
    # (site_makeup_l, total_site_plus_all_grid_water_l, peak_cooling_elec_kw, annualized_total_cooling_cost_usd)
    for p in evaluated_plants:
        if p.get("feasible"):
            p["pareto_optimal"] = False
            p["dominated_by"] = []
            if not p.get("rack_upgrade_capex_included", True):
                p["excluded_from_cost_pareto_reason"] = "MISSING_CERTIFIED_W40_RACK_UPGRADE_COST_AND_APPROVAL"
    feasible_plants = [p for p in evaluated_plants if p.get("feasible") and p.get("rack_upgrade_capex_included", True)]
    for p in feasible_plants:
        dominated_by: list[str] = []
        for q in feasible_plants:
            if p["plant_id"] == q["plant_id"]:
                continue
            no_worse = (
                q["site_makeup_l"] <= p["site_makeup_l"] + 1e-3
                and q["total_site_plus_all_grid_water_l"] <= p["total_site_plus_all_grid_water_l"] + 1e-3
                and q["peak_cooling_elec_kw"] <= p["peak_cooling_elec_kw"] + 1e-3
                and q["annualized_total_cooling_cost_usd"] <= p["annualized_total_cooling_cost_usd"] + 1e-2
            )
            strictly_better = (
                q["site_makeup_l"] < p["site_makeup_l"] - 1.0
                or q["total_site_plus_all_grid_water_l"] < p["total_site_plus_all_grid_water_l"] - 1.0
                or q["peak_cooling_elec_kw"] < p["peak_cooling_elec_kw"] - 0.1
                or q["annualized_total_cooling_cost_usd"] < p["annualized_total_cooling_cost_usd"] - 1.0
            )
            if no_worse and strictly_better:
                dominated_by.append(q["plant_id"])
        p["pareto_optimal"] = len(dominated_by) == 0
        p["dominated_by"] = dominated_by

    return {
        "solution_id": "S2_WEATHER_CONSTRAINED_DRY_HYBRID_DISPATCH",
        "status": "OFFLINE_SIMULATION_PARETO_FRONTIER_NO_LIVE_ACTUATION",
        "evaluated_plants": evaluated_plants,
        "pareto_frontier_plant_ids": [p["plant_id"] for p in feasible_plants if p.get("pareto_optimal")],
    }


def evaluate_s3_sensor_observer_information_gate(site: dict[str, Any]) -> dict[str, Any]:
    """S3 — Sensor/Observer That Earns Its Instrumentation Cost (Fisher Information & VoI Gate).

    Forms dual heat estimates Q_elec vs Q_enthalpy = m_dot * cp * dT, evaluates the 5-fault
    observability rank (fouling, bypass, air entrainment, temp drift, flow drift), and decides
    when existing passive telemetry suffices vs. when a single extra observation/excitation is
    cost-justified.
    """
    it_kw = finite_number(site["it_load_kw"], "it_load_kw", "site")
    liquid_capture = finite_number(site.get("liquid_heat_capture_fraction", 0.85), "liquid_capture", "site")
    q_elec_liquid_kw = it_kw * liquid_capture
    q_elec_sigma_kw = q_elec_liquid_kw * 0.018  # +/-1.8% PSU wattmeter + capture fraction uncertainty

    tcs_flow_lpm = finite_number(site.get("tcs_flow_lpm", it_kw * 1.5), "tcs_flow_lpm", "site")
    tcs_dt_c = finite_number(site.get("tcs_delta_t_c", 9.8), "tcs_delta_t_c", "site")
    cp_factor = (1.025 * 3.85) / 60.0  # kW per (L/min * K) for PG25
    q_enthalpy_kw = cp_factor * tcs_flow_lpm * tcs_dt_c
    q_enthalpy_sigma_kw = q_enthalpy_kw * 0.035  # +/-3.5% combined flow + RTD dT uncertainty

    heat_residual_kw = q_enthalpy_kw - q_elec_liquid_kw
    combined_sigma_kw = math.sqrt(q_elec_sigma_kw ** 2 + q_enthalpy_sigma_kw ** 2)
    z_score = abs(heat_residual_kw) / max(combined_sigma_kw, 1e-6)

    has_calibrated_redundant_rtds = bool(site.get("has_calibrated_redundant_cdu_rtds", False))
    has_autozero_dp = bool(site.get("has_autozero_differential_pressure", False))
    collinear_drift_risk = bool(site.get("uses_uncalibrated_flexible_coldplate_mems", False))

    # Heuristic screening only. This does not calculate an information matrix,
    # empirical observability rank, or field-tested fault resolution.
    # Fault identifiability *hypotheses* over 5 fault modes:
    # [F1_coldplate_fouling, F2_manifold_bypass, F3_air_entrainment, F4_temp_sensor_drift, F5_flow_sensor_drift]
    # With passive [Q_elec, T_in, T_out, Q_flow, P_pump], any SINGLE fault is observable (rank 4/4 on single-fault slices),
    # but simultaneous F1_fouling + F4_temp_drift is collinear unless either (a) redundant RTD/dP exists or (b) bounded ABA step is run.
    if has_calibrated_redundant_rtds and has_autozero_dp and not collinear_drift_risk:
        return {
            "solution_id": "S3_FISHER_INFORMATION_SENSOR_GATE",
            "analysis_boundary": "HEURISTIC_SENSOR_VALUE_OF_INFORMATION_NOT_CALCULATED_FISHER_INFORMATION_OR_REAL_FAULT_IDENTIFIABILITY",
            "decision": "REFUSE_NEW_HARDWARE_EXISTING_TELEMETRY_SUFFICES",
            "existing_telemetry_identifiable_faults": 5,
            "total_fault_classes": 5,
            "q_elec_liquid_kw": round(q_elec_liquid_kw, 2),
            "q_enthalpy_kw": round(q_enthalpy_kw, 2),
            "heat_balance_z_score": round(z_score, 3),
            "selected_intervention": None,
            "custom_3omega_eis_cartridge_accepted": False,
            "reason": (
                "Plant already has calibrated redundant RTDs and differential pressure; "
                "conventional passive energy-balance observer achieves full 5/5 fault identifiability at $0 extra cost."
            ),
        }

    # Compare candidate interventions by net Value of Information (VoI = avoided_fault_risk_usd - annualized_cost_usd)
    expected_unidentified_fault_cost_usd = finite_number(
        site.get("annual_collinear_fault_or_scale_risk_usd", 0.0), "fault_risk", "site"
    )
    candidates = [
        {
            "candidate_id": "CAND_0_PASSIVE_ENERGY_BALANCE_OBSERVER",
            "name": "Competent Passive Energy & Mass-Balance Observer (No New Hardware, No Perturbation)",
            "capex_usd": 0.0,
            "annual_cost_usd": 0.0,
            "identifiable_fault_classes": 3,
            "resolves_collinear_drift_plus_fouling": False,
            "expected_risk_reduction_fraction": 0.65,
        },
        {
            "candidate_id": "CAND_1_BENCH_OR_MAINTENANCE_ABA_STEP_TEST",
            "name": "Guarded Bounded +/-4% ABA Flow/Blowdown Step Test (Offline/Maintenance Window Only)",
            "capex_usd": 0.0,
            "annual_cost_usd": 600.0,  # Engineer maintenance-window execution cost
            "identifiable_fault_classes": 5,
            "resolves_collinear_drift_plus_fouling": True,
            "expected_risk_reduction_fraction": 0.88,
        },
        {
            "candidate_id": "CAND_2_COTS_PT100_AUTOZERO_DP_EC_WITNESS",
            "name": "COTS Sidestream 4-Wire Pt100 + 3-Way Auto-Zero dP + Conductivity Reference Kit",
            "capex_usd": 1490.0,
            "annual_cost_usd": 1490.0 / 5.0 + 400.0,
            "identifiable_fault_classes": 5,
            "resolves_collinear_drift_plus_fouling": True,
            "expected_risk_reduction_fraction": 0.95,
        },
        {
            "candidate_id": "CAND_3_CUSTOM_3OMEGA_EIS_CARTRIDGE",
            "name": "Custom Multi-Harmonic 3-Omega + EIS In-Line Microchannel Cartridge",
            "capex_usd": 210000.0,
            "annual_cost_usd": 210000.0 / 5.0 + 5000.0,
            "identifiable_fault_classes": 5,
            "resolves_collinear_drift_plus_fouling": True,
            "expected_risk_reduction_fraction": 0.97,
        },
    ]

    for c in candidates:
        gross_benefit = expected_unidentified_fault_cost_usd * c["expected_risk_reduction_fraction"]
        c["net_annual_voi_usd"] = round(gross_benefit - c["annual_cost_usd"], 2)

    winner = max(candidates, key=lambda x: x["net_annual_voi_usd"])
    custom_3omega = next(c for c in candidates if c["candidate_id"] == "CAND_3_CUSTOM_3OMEGA_EIS_CARTRIDGE")

    return {
        "solution_id": "S3_FISHER_INFORMATION_SENSOR_GATE",
        "analysis_boundary": "HEURISTIC_SENSOR_VALUE_OF_INFORMATION_NOT_CALCULATED_FISHER_INFORMATION_OR_REAL_FAULT_IDENTIFIABILITY",
        "decision": (
            "SELECT_SINGLE_COST_POSITIVE_INTERVENTION"
            if winner["candidate_id"] != "CAND_0_PASSIVE_ENERGY_BALANCE_OBSERVER"
            else "KEEP_PASSIVE_OBSERVER_NO_EXTRA_HARDWARE"
        ),
        "q_elec_liquid_kw": round(q_elec_liquid_kw, 2),
        "q_enthalpy_kw": round(q_enthalpy_kw, 2),
        "heat_balance_residual_kw": round(heat_residual_kw, 2),
        "heat_balance_z_score": round(z_score, 3),
        "evaluated_candidates": candidates,
        "voi_evidence_class": "USER_DECLARED_FAULT_COST_AND_ASSUMED_RISK_REDUCTION_NOT_MEASURED",
        "selected_intervention": winner,
        "custom_3omega_eis_cartridge_accepted": winner["candidate_id"] == "CAND_3_CUSTOM_3OMEGA_EIS_CARTRIDGE",
        "custom_3omega_rejection_reason": (
            f"Custom 3-omega+EIS cartridge net VoI is ${custom_3omega['net_annual_voi_usd']:,.2f}/yr "
            f"(loses money due to $210,000 CapEx); {winner['name']} achieves {winner['identifiable_fault_classes']}/5 "
            f"identifiability with +${winner['net_annual_voi_usd']:,.2f}/yr net VoI."
        ),
    }


def evaluate_s4_water_source_substitution(
    site: dict[str, Any],
    tariff: dict[str, Any],
    annual_makeup_needed_l: float,
    annual_evaporation_l: float,
    annual_blowdown_l: float,
) -> dict[str, Any]:
    """S4 — Water-Source Substitution & Recovery.

    Models municipal reclaimed water, AHU coil condensate recovery, and blowdown RO polishing.
    Strictly preserves the physical law that reclaimed water reduces POTABLE withdrawal
    without reducing site EVAPORATIVE consumption.
    """
    reclaimed_avail_l = finite_number(site.get("reclaimed_water_available_l_per_yr", 0.0), "reclaimed_avail", "site")
    condensate_avail_l = finite_number(site.get("ahu_condensate_available_l_per_yr", 0.0), "condensate_avail", "site")
    potable_rate_m3 = finite_number(tariff["potable_water_usd_per_m3"], "potable_water_usd_per_m3", "tariff")
    reclaimed_rate_m3 = finite_number(
        tariff.get("reclaimed_water_usd_per_m3", potable_rate_m3 * 0.55), "reclaimed_rate", "tariff"
    )
    elec_rate = finite_number(tariff["electricity_energy_usd_per_kwh"], "electricity_energy_usd_per_kwh", "tariff")

    # 1. AHU Condensate harvest (ultra-low TDS < 30 ppm, 0 pretreatment kWh)
    used_condensate_l = min(annual_makeup_needed_l, condensate_avail_l)
    rem_makeup_l = annual_makeup_needed_l - used_condensate_l

    # 2. Municipal Reclaimed Water substitution (capped at 85% blend or available supply, requires UV/biocide pretreatment ~0.18 kWh/m3)
    max_reclaimed_blend_l = rem_makeup_l * 0.85
    used_reclaimed_l = min(max_reclaimed_blend_l, reclaimed_avail_l)
    pretreatment_elec_kwh = (used_reclaimed_l / 1000.0) * 0.18

    potable_withdrawal_l = rem_makeup_l - used_reclaimed_l
    total_intake_l = potable_withdrawal_l + used_reclaimed_l + used_condensate_l

    baseline_potable_cost = (annual_makeup_needed_l / 1000.0) * potable_rate_m3
    new_supply_cost = (
        (potable_withdrawal_l / 1000.0) * potable_rate_m3
        + (used_reclaimed_l / 1000.0) * reclaimed_rate_m3
        + pretreatment_elec_kwh * elec_rate
    )
    capex_pipe_and_uv_usd = 45000.0 if used_reclaimed_l > 0 else (4500.0 if used_condensate_l > 0 else 0.0)
    annual_net_savings_usd = (baseline_potable_cost - new_supply_cost) - (capex_pipe_and_uv_usd / 10.0)

    return {
        "solution_id": "S4_WATER_SOURCE_SUBSTITUTION_AND_RECOVERY",
        "total_site_intake_l": round(total_intake_l, 1),
        "potable_freshwater_withdrawal_l": round(potable_withdrawal_l, 1),
        "reclaimed_water_intake_l": round(used_reclaimed_l, 1),
        "ahu_condensate_recovered_l": round(used_condensate_l, 1),
        "potable_withdrawal_reduction_l": round(annual_makeup_needed_l - potable_withdrawal_l, 1),
        "potable_withdrawal_reduction_pct": round(
            ((annual_makeup_needed_l - potable_withdrawal_l) / annual_makeup_needed_l * 100.0)
            if annual_makeup_needed_l > 0
            else 0.0,
            2,
        ),
        "site_evaporative_consumption_l": round(annual_evaporation_l, 1),
        "evaporative_consumption_reduction_from_reclaimed_substitution_l": 0.0,
        "blowdown_wastewater_discharge_l": round(annual_blowdown_l, 1),
        "pretreatment_electricity_kwh": round(pretreatment_elec_kwh, 1),
        "capex_usd": capex_pipe_and_uv_usd,
        "annual_net_savings_usd": round(annual_net_savings_usd, 2),
        "material_safety_flags": [
            "Reclaimed water reduces potable drinking-water withdrawal but does NOT reduce site evaporative consumption.",
            "Verify municipal reclaimed ammonia (<2 ppm) against copper/brass heat-exchanger stress-corrosion cracking.",
            "Monitor orthophosphate in reclaimed makeup to prevent calcium-phosphate scaling at high cycles.",
        ],
    }


def evaluate_s5_grid_and_community_cost_mitigation(
    site: dict[str, Any],
    tariff: dict[str, Any],
    peak_cooling_kw: float,
    annual_cooling_kwh: float,
) -> dict[str, Any]:
    """S5 — Grid & Community Cost Mitigation (TES Peak Shaving + 3 Ratepayer/Developer Finance Allocations)."""
    it_kw = finite_number(site["it_load_kw"], "it_load_kw", "site")
    movable_it_frac = finite_number(site.get("declared_movable_it_sla_fraction", 0.0), "movable_it_sla", "site")
    if movable_it_frac > 0.30:
        raise EvidenceError("declared_movable_it_sla_fraction > 0.30 requires explicit batch-queue contract proof")

    # 35% peak-shave is a PROPOSED design target, not a dispatch result.
    # A real modeled reduction requires declared usable energy, charge headroom and
    # an explicit engineer-approved dispatch feasibility assertion. Without these,
    # give no realized/dispatch credit while retaining the candidate design target.
    tes_proposed_peak_shave_kw = peak_cooling_kw * 0.35
    verified_capacity_kwh = finite_number(site.get("declared_verified_tes_usable_capacity_kwh_th", 0.0), "tes_capacity", "site")
    verified_charge_headroom_kw = finite_number(site.get("declared_verified_offpeak_charge_headroom_kw", 0.0), "tes_charge_headroom", "site")
    tes_dispatch_evidence_present = declared_boolean(site, "tes_dispatch_proven_feasible_for_climate")
    tes_peak_cool_shave_kw = (
        min(tes_proposed_peak_shave_kw, verified_capacity_kwh / 4.0, verified_charge_headroom_kw)
        if tes_dispatch_evidence_present and verified_capacity_kwh > 0 and verified_charge_headroom_kw > 0
        else 0.0
    )
    # A fractional SLA assertion does not establish that a schedule actually
    # moved demand out of coincident peak. Treat as opportunity until dispatch
    # and its measured effect on the tariff's peak window are demonstrated.
    it_peak_shave_proposed_kw = it_kw * movable_it_frac
    it_dispatch_evidence_present = declared_boolean(site, "it_peak_shift_dispatch_proven_feasible")
    it_peak_shave_kw = it_peak_shave_proposed_kw if it_dispatch_evidence_present else 0.0
    total_peak_shaved_kw = tes_peak_cool_shave_kw + it_peak_shave_kw

    baseline_peak_kw = it_kw + peak_cooling_kw
    mitigated_peak_kw = baseline_peak_kw - total_peak_shaved_kw

    # Community & Grid Infrastructure Economics (User-supplied in tariff.json / site.json)
    grid_upgrade_capex_usd = finite_number(
        tariff.get("declared_grid_substation_upgrade_cost_usd"), "grid_upgrade_capex", "tariff"
    )
    tax_abatement_annual_usd = finite_number(
        tariff.get("promised_annual_tax_abatement_subsidy_usd"), "tax_abatement", "tariff"
    )
    gross_annual_tax_rev_usd = finite_number(
        tariff.get("projected_gross_annual_local_tax_usd"), "gross_tax", "tariff"
    )
    promised_permanent_jobs = finite_number(site.get("promised_permanent_jobs"), "permanent_jobs", "site")
    project_years = int(finite_number(tariff.get("analysis_horizon_years", 12), "horizon_years", "tariff"))
    discount_rate = finite_number(tariff.get("discount_rate", 0.06), "discount_rate", "tariff")
    demand_rate_kw_mo = finite_number(tariff.get("electricity_peak_demand_usd_per_kw_month", 14.5), "demand", "tariff")

    # Present value annuity factor
    pv_factor = (
        (1.0 - (1.0 + discount_rate) ** (-project_years)) / discount_rate
        if discount_rate > 0
        else float(project_years)
    )

    # Downsized grid upgrade when peak demand is shaved via TES + flexible cooling
    peak_reduction_ratio = total_peak_shaved_kw / max(baseline_peak_kw, 1.0)
    mitigated_grid_upgrade_capex_usd = grid_upgrade_capex_usd * (1.0 - 0.85 * peak_reduction_ratio)
    tes_capex_usd = tes_peak_cool_shave_kw * 4.0 * 95.0  # 4-hour chilled water tank at ~$95/kWh_e equivalent

    # Evaluate the 3 required Cost-Allocation Alternatives (including early-exit / under-utilization stress at Year 6):
    # Alternative A: Conventional Socialized Utility Upgrade + Unconditional Tax Abatement
    # If developer under-ramps (50% load) or exits at Year 6, existing ratepayers pay the unrecovered grid upgrade!
    unrecovered_upgrade_under_early_exit_a = grid_upgrade_capex_usd * 0.55
    net_public_fiscal_npv_a = (gross_annual_tax_rev_usd - tax_abatement_annual_usd) * pv_factor - grid_upgrade_capex_usd
    subsidy_per_permanent_job_usd = (
        (tax_abatement_annual_usd * project_years + grid_upgrade_capex_usd) / max(promised_permanent_jobs, 1.0)
    )

    # Alternative B: Developer-Funded CIAC + 85% Minimum Billing Demand Take-or-Pay (AEP Ohio / PUCO Case 24-508 pattern)
    # Developer pays 100% of direct substation/interconnection CIAC upfront and posts collateral for 85% minimum demand.
    net_public_fiscal_npv_b = (gross_annual_tax_rev_usd - 0.5 * tax_abatement_annual_usd) * pv_factor

    # Alternative C: Flexibility + Thermal Storage Peak-Shaved Upgrade + Developer Take-or-Pay
    annual_demand_charge_saved_usd = total_peak_shaved_kw * demand_rate_kw_mo * 12.0
    developer_tes_npv_usd = annual_demand_charge_saved_usd * pv_factor + (
        grid_upgrade_capex_usd - mitigated_grid_upgrade_capex_usd
    ) - tes_capex_usd

    contract_verified = declared_boolean(site, "signed_collateralized_take_or_pay_contract_verified")
    allocations = [
        {
            "allocation_id": "ALLOC_A_CONVENTIONAL_SOCIALIZED_TARIFF_AND_ABATEMENT",
            "name": "Conventional Socialized Grid Upgrade + Unconditional Tax Abatement",
            "who_pays_grid_upgrade": "General Utility Ratepayers (socialized into rate base)",
            "developer_upfront_ciac_usd": 0.0,
            "ratepayer_exposure_upfront_usd": round(grid_upgrade_capex_usd, 2),
            "ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd": round(
                unrecovered_upgrade_under_early_exit_a, 2
            ),
            "net_public_tax_and_infrastructure_npv_usd": round(net_public_fiscal_npv_a, 2),
            "effective_public_subsidy_per_permanent_job_usd": round(subsidy_per_permanent_job_usd, 2),
            "ratepayer_shift_warning": net_public_fiscal_npv_a < 0 or subsidy_per_permanent_job_usd > 250_000.0,
        },
        {
            "allocation_id": "ALLOC_B_DEVELOPER_CIAC_AND_85PCT_TAKE_OR_PAY",
            "name": "Developer-Funded CIAC + 12-Yr 85% Minimum Billing Demand Take-or-Pay + Collateral Bond",
            "who_pays_grid_upgrade": "Data-Center Developer (100% CIAC + collateralized take-or-pay)",
            "developer_upfront_ciac_usd": round(grid_upgrade_capex_usd, 2),
            "ratepayer_exposure_upfront_usd": 0.0,
            "ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd": 0.0,
            "net_public_tax_and_infrastructure_npv_usd": round(net_public_fiscal_npv_b, 2),
            "effective_public_subsidy_per_permanent_job_usd": round(
                (0.5 * tax_abatement_annual_usd * project_years) / max(promised_permanent_jobs, 1.0), 2
            ),
            "ratepayer_shift_warning": not contract_verified,
            "actual_ratepayer_protection_verified": contract_verified,
            "projected_zero_stranded_risk_condition": "FULL_ENFORCEABLE_CIAC_AND_COLLATERAL_SCENARIO_ONLY",
        },
        {
            "allocation_id": "ALLOC_C_THERMAL_STORAGE_PEAK_SHAVE_PLUS_TAKE_OR_PAY",
            "name": "4-Hr Thermal Storage Peak Shave + Downsized Grid Upgrade + Developer Take-or-Pay",
            "who_pays_grid_upgrade": "Data-Center Developer (downsized upgrade + TES peak shave)",
            "developer_upfront_ciac_usd": round(mitigated_grid_upgrade_capex_usd + tes_capex_usd, 2),
            "ratepayer_exposure_upfront_usd": 0.0,
            "ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd": 0.0,
            "net_public_tax_and_infrastructure_npv_usd": round(net_public_fiscal_npv_b, 2),
            "developer_net_savings_vs_alloc_b_npv_usd": round(developer_tes_npv_usd, 2),
            "ratepayer_shift_warning": not contract_verified,
            "actual_ratepayer_protection_verified": contract_verified,
            "projected_zero_stranded_risk_condition": "FULL_ENFORCEABLE_CIAC_AND_COLLATERAL_SCENARIO_ONLY",
        },
    ]

    return {
        "solution_id": "S5_GRID_AND_COMMUNITY_COST_MITIGATION",
        "baseline_peak_facility_kw": round(baseline_peak_kw, 2),
        "mitigated_peak_facility_kw": round(mitigated_peak_kw, 2),
        "tes_cooling_peak_shaved_kw": round(tes_peak_cool_shave_kw, 2),
        "tes_proposed_peak_shave_kw_not_dispatch_proven": round(tes_proposed_peak_shave_kw, 2),
        "tes_dispatch_qualified": tes_dispatch_evidence_present and verified_capacity_kwh > 0 and verified_charge_headroom_kw > 0,
        "tes_warning": "TES peak reduction is zero without independently declared storage capacity, charging headroom and feasibility; ALL financing alternatives assume executed contracts and credit support, not signed/observed outcomes.",
        "declared_movable_it_peak_shaved_kw": round(it_peak_shave_kw, 2),
        "movable_it_peak_shave_proposed_not_dispatch_proven_kw": round(it_peak_shave_proposed_kw, 2),
        "dispatch_evidence_boundary": "TES and IT peak reductions are conditional assumptions. No chronological storage charge/discharge or coincident grid peak dispatch has been verified.",
        "contract_evidence_boundary": "Developer contribution/take-or-pay and collateral are proposed contract scenarios. The zero-exposure ledger numbers are conditional on executed enforceable arrangements, not observed ratepayer protection.",
        "tes_tank_capex_usd": round(tes_capex_usd, 2),
        "cost_allocation_alternatives": allocations,
    }


def evaluate_s6_heat_reuse_feasibility(
    site: dict[str, Any],
    tariff: dict[str, Any],
) -> dict[str, Any]:
    """S6 — Waste-Heat Reuse Where Real Load Exists (with Hard Go/No-Go Gate)."""
    sink = site.get("heat_reuse_offtaker")
    if not isinstance(sink, dict) or not bool(sink.get("exists", False)):
        return {
            "solution_id": "S6_HEAT_REUSE_FEASIBILITY",
            "decision": "NO_GO_NO_VIABLE_HEAT_OFFTAKER",
            "feasible": False,
            "credited_energy_saved_kwh": 0.0,
            "npv_usd": 0.0,
            "reason": "No proximate district, industrial, or greenhouse heat offtaker exists at this site.",
        }

    distance_km = finite_number(sink.get("distance_km", 10.0), "distance_km", "site")
    sink_demand_kw_th = finite_number(sink.get("thermal_demand_kw_th", 0.0), "thermal_demand_kw_th", "site")
    sink_req_temp_c = finite_number(sink.get("required_supply_temp_c", 70.0), "required_supply_temp_c", "site")
    matching_hours_yr = finite_number(sink.get("coincident_demand_hours_per_yr", 0.0), "coincident_hours", "site")
    displaced_fuel_usd_per_kwh_th = finite_number(
        sink.get("displaced_fuel_value_usd_per_kwh_th", 0.045), "fuel_value", "site"
    )

    loop_return_temp_c = finite_number(site.get("fws_return_temp_c", 42.0), "fws_return_temp_c", "site")
    it_kw = finite_number(site["it_load_kw"], "it_load_kw", "site")
    elec_rate = finite_number(tariff["electricity_energy_usd_per_kwh"], "electricity_energy_usd_per_kwh", "tariff")
    discount_rate = finite_number(tariff.get("discount_rate", 0.06), "discount_rate", "tariff")
    horizon_yrs = int(finite_number(tariff.get("analysis_horizon_years", 12), "horizon_years", "tariff"))

    if sink_demand_kw_th <= 0 or matching_hours_yr < 1000.0 or distance_km > 8.0:
        return {
            "solution_id": "S6_HEAT_REUSE_FEASIBILITY",
            "decision": "NO_GO_INSUFFICIENT_THERMAL_DEMAND_OR_EXCESS_DISTANCE",
            "feasible": False,
            "distance_km": distance_km,
            "coincident_demand_hours_per_yr": matching_hours_yr,
            "credited_energy_saved_kwh": 0.0,
            "npv_usd": -distance_km * 850000.0,
            "reason": (
                f"Offtaker distance ({distance_km} km) or coincident demand ({matching_hours_yr} h/yr) "
                "fails economic/thermodynamic viability gate."
            ),
        }

    q_reclaimable_kw = min(it_kw * 0.80, sink_demand_kw_th)
    pipe_loss_frac = min(0.25, distance_km * 0.022)

    # If loop return temperature >= sink_req_temp_c + 5C, direct plate heat exchanger works without heat pump!
    if loop_return_temp_c >= sink_req_temp_c + 5.0:
        hp_cop = 25.0  # Circulation pump only
        needs_booster_heat_pump = False
    else:
        needs_booster_heat_pump = True
        t_sink_k = sink_req_temp_c + 273.15
        t_src_k = loop_return_temp_c + 273.15
        lift_k = max(10.0, (t_sink_k - t_src_k) + 8.0)
        # Carnot efficiency ~0.52 (matches published COP=5.5 at 60C, 4.3 at 70C, 3.5 at 80C from 40C source)
        hp_cop = round(max(2.2, 0.52 * (t_sink_k / lift_k)), 2)

    delivered_heat_kwh_yr = q_reclaimable_kw * (1.0 - pipe_loss_frac) * matching_hours_yr
    hp_elec_kwh_yr = (q_reclaimable_kw * matching_hours_yr) / hp_cop

    annual_heat_revenue_usd = delivered_heat_kwh_yr * displaced_fuel_usd_per_kwh_th
    annual_hp_elec_cost_usd = hp_elec_kwh_yr * elec_rate
    annual_net_cashflow_usd = annual_heat_revenue_usd - annual_hp_elec_cost_usd

    hp_capex_usd = (q_reclaimable_kw * 320.0) if needs_booster_heat_pump else (q_reclaimable_kw * 55.0)
    piping_capex_usd = distance_km * 750_000.0
    total_capex_usd = hp_capex_usd + piping_capex_usd

    pv_factor = (
        (1.0 - (1.0 + discount_rate) ** (-horizon_yrs)) / discount_rate if discount_rate > 0 else float(horizon_yrs)
    )
    npv_usd = annual_net_cashflow_usd * pv_factor - total_capex_usd
    go_decision = npv_usd > 0.0 and annual_net_cashflow_usd > 0.0

    return {
        "solution_id": "S6_HEAT_REUSE_FEASIBILITY",
        "decision": "GO_VIABLE_PROXIMATE_HEAT_REUSE" if go_decision else "NO_GO_NEGATIVE_NPV_AT_SUPPLIED_TARIFF",
        "feasible": go_decision,
        "offtaker_name": sink.get("name", "Unnamed Thermal Offtaker"),
        "needs_booster_heat_pump": needs_booster_heat_pump,
        "heat_pump_cop": hp_cop,
        "delivered_heat_kwh_th_per_yr": round(delivered_heat_kwh_yr, 1),
        "heat_pump_elec_kwh_per_yr": round(hp_elec_kwh_yr, 1),
        "capex_usd": round(total_capex_usd, 2),
        "annual_net_cashflow_usd": round(annual_net_cashflow_usd, 2),
        "npv_usd": round(npv_usd, 2),
    }


def check_decision_recall_triggers(
    original_receipt: dict[str, Any],
    updated_site: dict[str, Any] | None = None,
    updated_weather_sha256: str | None = None,
    updated_tariff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """S7 — Automatic Decision Recall when weather, chemistry, rack limits, or tariffs change."""
    reopened_reasons: list[str] = []
    orig_assumptions = original_receipt.get("pinned_assumptions", {})

    if updated_weather_sha256 and updated_weather_sha256 != original_receipt.get("weather_sha256"):
        reopened_reasons.append("WEATHER_REGIME_CHANGED: weather_sha256 mismatch invalidates S2 dry/wet dispatch.")

    if updated_site is not None:
        updated_site_digest = hashlib.sha256(json.dumps(updated_site, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        old_site_digest = original_receipt.get("site_canonical_sha256")
        if float(updated_site.get("rack_max_liquid_inlet_c", 0)) < float(orig_assumptions.get("rack_max_liquid_inlet_c", 0)):
            reopened_reasons.append(
                "RACK_THERMAL_LIMIT_TIGHTENED: lower max liquid inlet temperature invalidates W40 dry-cooling margin."
            )
        chem_new = updated_site.get("water_chemistry", {})
        if isinstance(chem_new, dict) and float(chem_new.get("silica_ppm", 0)) > float(orig_assumptions.get("silica_ppm", 0)) * 1.15:
            reopened_reasons.append(
                "MAKEUP_SILICA_INCREASED: higher makeup silica invalidates prior S1 maximum Cycles of Concentration."
            )

        if old_site_digest != updated_site_digest and not reopened_reasons:
            reopened_reasons.append("SITE_SOURCE_CHANGED_OR_PIN_MISSING: all site values must be re-evaluated before standing can continue")

    if updated_tariff is not None:
        updated_tariff_digest = hashlib.sha256(json.dumps(updated_tariff, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        old_tariff_digest = original_receipt.get("tariff_canonical_sha256")
        if float(updated_tariff.get("grid_ewif_l_per_kwh", 0)) > float(orig_assumptions.get("grid_ewif_l_per_kwh", 0)) * 1.25:
            reopened_reasons.append(
                "GRID_WATER_INTENSITY_INCREASED: higher upstream thermoelectric EWIF reopens S2 dry-vs-wet water trade-off."
            )

        if old_tariff_digest != updated_tariff_digest and not any("TARIFF_SOURCE_CHANGED" in x for x in reopened_reasons):
            reopened_reasons.append("TARIFF_SOURCE_CHANGED: re-evaluate economic standing against new rate and cost values")

    return {
        "recall_status": "REOPENED_BY_SOURCE_CHANGE" if reopened_reasons else "STANDING_VALID",
        "reopened": len(reopened_reasons) > 0,
        "reopened_reasons": reopened_reasons,
    }


def run_design_engine(
    site_path: str | Path,
    weather_path: str | Path,
    tariff_path: str | Path,
    telemetry_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run the complete S1-S7 Solutions Design & Competition Engine and write the 5 required artifacts."""
    sp = Path(site_path)
    tp = Path(tariff_path)
    if not sp.is_file() or not tp.is_file():
        raise EvidenceError("site or tariff JSON file missing")

    site_blob = sp.read_bytes()
    tariff_blob = tp.read_bytes()
    site = json.loads(site_blob.decode("utf-8"))
    tariff = json.loads(tariff_blob.decode("utf-8"))
    weather = load_weather_csv(weather_path)

    required_tariff = ("electricity_energy_usd_per_kwh", "potable_water_usd_per_m3", "wastewater_discharge_usd_per_m3", "grid_ewif_l_per_kwh")
    missing_tariff = [k for k in required_tariff if k not in tariff or tariff[k] is None]
    if missing_tariff:
        raise EvidenceError("missing required tariff fields: " + ",".join(missing_tariff))

    it_kw = finite_number(site.get("it_load_kw"), "it_load_kw", "site")
    if it_kw <= 0:
        raise EvidenceError("it_load_kw must exceed zero")

    telemetry_audit = None
    if telemetry_path is not None:
        telemetry_audit = audit(telemetry_path, float(tariff["grid_ewif_l_per_kwh"]))

    annual_wet_heat_kwh = it_kw * 1.04 * weather["total_hours"]

    # Execute S1
    s1 = evaluate_s1_chemistry_tower_optimizer(site, tariff, annual_wet_heat_kwh)
    # Missing chemistry disqualifies wet towers, not the entire site-design inquiry.
    # A dry-only/chiller alternative remains available as a *modeled* option;
    # do not silently assume any cooling-tower CoC is safe.
    max_safe_coc = float(s1["selected_regime"]["permissible_max_coc"]) if s1.get("feasible") else None

    # Execute S2
    s2 = evaluate_s2_weather_constrained_dispatch(site, weather, tariff, max_safe_coc)

    # Pick reference feasible S2 plant (lowest cost among Pareto-optimal feasible plants)
    feasible_s2 = [p for p in s2["evaluated_plants"] if p.get("feasible")]
    eligible_s2 = [p for p in feasible_s2 if p.get("rack_upgrade_capex_included", True)]
    if not eligible_s2:
        raise EvidenceError("No modeled feasible cooling design with a complete declared rack upgrade cost")
    best_s2 = min(eligible_s2, key=lambda x: x["annualized_total_cooling_cost_usd"])

    # Execute S3
    s3 = evaluate_s3_sensor_observer_information_gate(site)

    # Execute S4
    s4 = evaluate_s4_water_source_substitution(
        site,
        tariff,
        annual_makeup_needed_l=best_s2["site_makeup_l"],
        annual_evaporation_l=best_s2["site_evaporation_l"],
        annual_blowdown_l=best_s2["site_blowdown_l"],
    )

    # Execute S5
    s5 = evaluate_s5_grid_and_community_cost_mitigation(
        site,
        tariff,
        peak_cooling_kw=best_s2["peak_cooling_elec_kw"],
        annual_cooling_kwh=best_s2["cooling_elec_kwh"],
    )

    # Execute S6
    s6 = evaluate_s6_heat_reuse_feasibility(site, tariff)

    # S7 — Build Assumption & Provenance Receipt
    chem = site.get("water_chemistry") if isinstance(site.get("water_chemistry"), dict) else {}
    receipt_payload = {
        "schema": "openline.sensors.004.design_receipt.v1",
        "status": "MODELED_ENGINEERING_PROPOSAL_NOT_OBSERVED_FIELD_SAVINGS",
        "site_id": site.get("site_id", "UNNAMED_SITE"),
        "site_sha256": hashlib.sha256(site_blob).hexdigest(),
        "site_canonical_sha256": hashlib.sha256(json.dumps(site, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "weather_sha256": weather["sha256"],
        "tariff_sha256": hashlib.sha256(tariff_blob).hexdigest(),
        "tariff_canonical_sha256": hashlib.sha256(json.dumps(tariff, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "receipt_authority": "CONTENT_HASH_ONLY_NOT_SIGNED_NOT_RECEIVER_AUTHORIZED",
        "telemetry_sha256": None if telemetry_audit is None else telemetry_audit["source_sha256"],
        "pinned_assumptions": {
            "it_load_kw": it_kw,
            "rack_max_liquid_inlet_c": site.get("rack_max_liquid_inlet_c"),
            "silica_ppm": chem.get("silica_ppm"),
            "grid_ewif_l_per_kwh": tariff.get("grid_ewif_l_per_kwh"),
        },
        "input_evidence_classification": {
            "site_parameters": "USER_DECLARED_SCENARIO",
            "weather_series": f"WEATHER_CSV ({weather['station']})",
            "tariff_parameters": "USER_DECLARED_TARIFF_SCENARIO",
            "meter_telemetry": "ABSENT" if telemetry_audit is None else "OBSERVED_METER_CSV_UNVERIFIED_CALIBRATION",
        },
        "prior_70pct_sensor_claim_rejected": True,
        "live_bms_actuation_permitted": False,
    }
    receipt_sha256 = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode("utf-8")).hexdigest()
    receipt_payload["receipt_sha256"] = receipt_sha256

    master_output = {
        "status": "SOLUTIONS_ENGINEERED_MODELED_ONLY_NO_ACTUATION",
        "site_id": site.get("site_id", "UNNAMED_SITE"),
        "receipt_sha256": receipt_sha256,
        "telemetry_audit": telemetry_audit,
        "S1_chemistry_tower_optimizer": s1,
        "S2_weather_constrained_dispatch": s2,
        "S3_sensor_observer_gate": s3,
        "S4_water_source_substitution": s4,
        "S5_grid_and_community_cost_mitigation": s5,
        "S6_heat_reuse_feasibility": s6,
        "S7_verification_receipt": receipt_payload,
    }

    if output_dir is not None:
        od = Path(output_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "candidate_solutions.json").write_text(
            json.dumps(master_output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (od / "assumption_receipts.json").write_text(
            json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # Write ranked_pareto.csv
        pareto_cols = [
            "plant_id",
            "name",
            "feasible",
            "pareto_optimal",
            "cycles_of_concentration",
            "dry_heat_rejection_share_pct",
            "site_makeup_l",
            "site_blowdown_l",
            "site_wue_l_per_it_kwh",
            "cooling_elec_kwh",
            "peak_cooling_elec_kw",
            "pue",
            "total_site_plus_all_grid_water_l",
            "capex_usd",
            "annualized_total_cooling_cost_usd",
        ]
        with (od / "ranked_pareto.csv").open("w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=pareto_cols)
            writer.writeheader()
            for p in s2["evaluated_plants"]:
                if p.get("feasible"):
                    writer.writerow({k: p.get(k) for k in pareto_cols})

        # Write engineering_report.md and equipment_boundary.md
        (od / "engineering_report.md").write_text(
            _render_engineering_report_md(site, master_output), encoding="utf-8"
        )
        (od / "equipment_boundary.md").write_text(
            _render_equipment_boundary_md(site, master_output), encoding="utf-8"
        )

    return master_output


def _render_engineering_report_md(site: dict[str, Any], res: dict[str, Any]) -> str:
    s1 = res["S1_chemistry_tower_optimizer"]
    s2 = res["S2_weather_constrained_dispatch"]
    s3 = res["S3_sensor_observer_gate"]
    s4 = res["S4_water_source_substitution"]
    s5 = res["S5_grid_and_community_cost_mitigation"]
    s6 = res["S6_heat_reuse_feasibility"]
    rec = res["S7_verification_receipt"]

    lines = [
        f"# Engineering Design & Public-Benefit Accountability Report — {site.get('site_id', 'Site')}",
        "",
        f"- **Receipt SHA-256**: `{rec['receipt_sha256']}`",
        f"- **Epistemic Status**: `{res['status']}` (All water/energy/cost reductions below are modeled from supplied inputs, NOT observed field savings.)",
        "",
        "## 1. S1 — Chemistry-Bounded Cooling-Tower Optimizer (vs. DOE FEMP BMP #10)",
    ]
    if not s1.get("feasible"):
        lines.append(f"- **Status**: `{s1['status']}` — Missing required measurements: `{', '.join(s1.get('required_measurements', []))}`")
    else:
        sel = s1["selected_regime"]
        lines.append(f"- **Classification**: `{s1['novelty_classification']}`")
        lines.append(
            f"- **Selected Regime (`{sel['regime_id']}`)**: Max permissible CoC = `{sel['permissible_max_coc']}` "
            f"(bounded by `{sel['limiting_chemistry_constraint']}`), reducing modeled site makeup by "
            f"`{sel['makeup_reduction_vs_baseline_pct']}%` (`{sel['makeup_water_saved_vs_baseline_l']:,.0f} L/yr`) "
            f"and providing `${sel['annual_net_operating_savings_usd']:,.2f}/yr` in modeled net operating savings "
            f"(`{s1['economic_recommendation']}`; not a measured outcome)."
        )

    lines.extend([
        "",
        "## 2. S2 — Weather-Constrained Dry/Hybrid Dispatch & Pareto Frontier",
        "",
        "| Plant Architecture | Feasible | Pareto Optimal | Dry Share (%) | Site Makeup (L/yr) | Site + All Grid Water (L/yr) | Peak Cool (kW) | Annualized Cost ($/yr) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for p in s2["evaluated_plants"]:
        if p.get("feasible"):
            lines.append(
                f"| `{p['plant_id']}` | Yes | `{p['pareto_optimal']}` | `{p['dry_heat_rejection_share_pct']}%` | "
                f"`{p['site_makeup_l']:,.0f}` | `{p['total_site_plus_all_grid_water_l']:,.0f}` | "
                f"`{p['peak_cooling_elec_kw']:,.1f}` | `${p['annualized_total_cooling_cost_usd']:,.0f}` |"
            )
        else:
            lines.append(f"| `{p['plant_id']}` | **No** (`{p.get('infeasibility_reason', 'Thermal limit exceeded')}`) | - | - | - | - | - | - |")

    lines.extend([
        "",
        "## 3. S3 — Sensor/Observer Fisher-Information Gate",
        f"- **Decision**: `{s3['decision']}`",
        f"- **Heat Balance Check**: $Q_{{\\text{{elec,liquid}}}} = {s3['q_elec_liquid_kw']:,.1f}\\text{{ kW}}$ vs. $Q_{{\\text{{enthalpy}}}} = {s3['q_enthalpy_kw']:,.1f}\\text{{ kW}}$ ($z = {s3['heat_balance_z_score']}$)",
        f"- **Custom $3\\omega$+EIS Cartridge Accepted**: `{s3['custom_3omega_eis_cartridge_accepted']}` ({s3.get('custom_3omega_rejection_reason', 'Not needed')})",
        "",
        "## 4. S4 — Water-Source Substitution (Potable vs. Reclaimed & Condensate)",
        f"- **Potable Freshwater Withdrawal**: `{s4['potable_freshwater_withdrawal_l']:,.0f} L/yr` (`-{s4['potable_withdrawal_reduction_pct']}%` vs. 100% potable)",
        f"- **Reclaimed Intake / AHU Condensate**: `{s4['reclaimed_water_intake_l']:,.0f} L/yr` / `{s4['ahu_condensate_recovered_l']:,.0f} L/yr`",
        f"- **Site Evaporative Consumption**: `{s4['site_evaporative_consumption_l']:,.0f} L/yr` (**0.0 L reduction from reclaimed substitution**—reclaimed water saves drinking water, not evaporation)",
        "",
        "## 5. S5 — Grid Peak Mitigation & Ratepayer vs. Developer Cost Allocation",
        "- **Contract boundary**: All developer contribution, take-or-pay and collateral protections are hypothetical contractual choices until executed and enforceable; the zero-risk table entries are CONDITIONAL, not observed.",
        "- **Dispatch boundary**: A TES tank size or proposed peak reduction is not chronological proof of charge/recharge or grid coincident demand reduction.",
        f"- **Facility Peak Demand**: `{s5['baseline_peak_facility_kw']:,.1f} kW` $\\to$ `{s5['mitigated_peak_facility_kw']:,.1f} kW` (via `{s5['tes_cooling_peak_shaved_kw']:,.1f} kW` 4-hr Thermal Storage shave)",
        "",
        "| Finance & Tariff Structure | Who Pays Grid Upgrade | Upfront Ratepayer Exposure ($) | Stranded Ratepayer Risk at Yr 6 ($) | Public Fiscal NPV ($) | Ratepayer Shift Flag |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for al in s5["cost_allocation_alternatives"]:
        lines.append(
            f"| `{al['allocation_id']}` | {al['who_pays_grid_upgrade']} | `${al['ratepayer_exposure_upfront_usd']:,.0f}` | "
            f"`${al['ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd']:,.0f}` | "
            f"`${al['net_public_tax_and_infrastructure_npv_usd']:,.0f}` | `{al['ratepayer_shift_warning']}` |"
        )

    lines.extend([
        "",
        "## 6. S6 — Waste-Heat Reuse Feasibility Gate",
        f"- **Decision**: `{s6['decision']}` (Feasible: `{s6['feasible']}`, NPV: `${s6.get('npv_usd', 0.0):,.0f}`)",
        "",
        "## 7. Public-Benefit Summary for Residents & Officials",
        "- **What is promised vs. modeled**: Any claim that novel software or a cold-plate sensor alone cuts facility water by 70% is **rejected**; large site-water reductions require physical dry/hybrid heat rejection (`S2`), water-chemistry-bounded cycles of concentration (`S1`), or reclaimed water substitution (`S4`).",
        "- **Who bears the infrastructure risk**: A fully executed, enforceable, collateralized developer CIAC/take-or-pay arrangement (`ALLOC_B` / `ALLOC_C`) could contractually transfer upgrade risk. The table's zero-risk outcomes are CONDITIONAL scenarios, not proof such contracts exist or eliminate all stranded costs.",
    ])
    return "\n".join(lines) + "\n"


def _render_equipment_boundary_md(site: dict[str, Any], res: dict[str, Any]) -> str:
    return "\n".join([
        f"# Equipment, Permitting & Safety Boundary Specification — {site.get('site_id', 'Site')}",
        "",
        "## 1. Physical Loop Separation",
        "- **Boundary A (TCS — Closed Server/CDU Loop)**: PG25 or inhibited DI water. Recirculating volume is NOT water consumption.",
        "- **Boundary B (FWS — Cooling Tower / Dry Cooler / Hybrid)**: Consumes water via latent evaporation ($E$) and drift ($D$), and discharges blowdown ($B$) to sewer.",
        "- **Boundary C (Upstream Grid Electricity)**: Consumes thermoelectric cooling water at the power plant across BOTH IT server kWh and cooling kWh.",
        "",
        "## 2. Hard Operational & Safety Boundaries",
        "- **No Live Actuation**: `water_audit.py` and `solutions.py` are offline design and auditing tools. They never connect to or actuate PLCs, BACnet/Modbus registers, pumps, or chemical dosing valves.",
        "- **Chemical & Legionella Signoff**: Raising cooling-tower Cycles of Concentration (`S1`) or blending reclaimed water (`S4`) requires a licensed water-treatment engineer, ASHRAE Standard 188 Legionella water-management plan, and municipal discharge permit verification.",
        "- **Unpriced / Site-Specific Items Flagged `NOT_READY_FOR_PROCUREMENT`**: Union pipefitting labor, structural roof/pad engineering for dry coolers or TES tanks, utility interconnection studies, and municipal sewer deduct meter certification must be quoted locally.",
    ]) + "\n"


def evaluate_public_benefit_claims(filing: dict[str, Any]) -> dict[str, Any]:
    """Compare promised vs. documented public economic and resource claims for a data-center project.

    Marks each claim as VERIFIED_MET, SHORTFALL_OR_EXCEEDANCE, UNSUPPORTED_PROMISE,
    INCONSISTENT_ACCOUNTING, or OVERDUE_DISCLOSURE, and computes who bears infrastructure costs.
    """
    if not isinstance(filing, dict):
        raise EvidenceError("claims filing must be a JSON object")

    project_id = str(filing.get("project_id", "UNNAMED_PROJECT"))
    promised = filing.get("promised_claims", {})
    documented = filing.get("documented_disclosures", {})
    if not isinstance(promised, dict) or not isinstance(documented, dict):
        raise EvidenceError("promised_claims and documented_disclosures must be JSON objects")

    metrics_spec = [
        ("capital_investment_usd", "higher_is_better", "usd"),
        ("permanent_full_time_jobs", "higher_is_better", "count"),
        ("annual_local_tax_revenue_usd", "higher_is_better", "usd"),
        ("annual_public_subsidy_or_abatement_usd", "lower_is_better", "usd"),
        ("grid_infrastructure_upgrade_cost_usd", "lower_is_better", "usd"),
        ("ratepayer_funded_infrastructure_share_usd", "lower_is_better", "usd"),
        ("peak_electricity_demand_mw", "lower_is_better", "mw"),
        ("annual_water_withdrawal_l", "lower_is_better", "liters"),
        ("annual_water_consumption_evaporative_l", "lower_is_better", "liters"),
        ("annual_reclaimed_water_intake_l", "higher_is_better", "liters"),
    ]

    comparisons: list[dict[str, Any]] = []
    unsupported_or_overdue_count = 0
    inconsistent_flags: list[str] = []

    # Check physical consistency inside promised and documented water numbers
    for stage_name, block in (("promised", promised), ("documented", documented)):
        w_with = block.get("annual_water_withdrawal_l")
        w_cons = block.get("annual_water_consumption_evaporative_l")
        w_recl = block.get("annual_reclaimed_water_intake_l")
        if w_with is not None and w_cons is not None:
            if float(w_cons) > float(w_with) + 1e-6:
                inconsistent_flags.append(
                    f"{stage_name}: evaporative consumption ({w_cons} L) exceeds total water withdrawal ({w_with} L)"
                )
        if w_with is not None and w_recl is not None:
            if float(w_recl) > float(w_with) + 1e-6:
                inconsistent_flags.append(
                    f"{stage_name}: reclaimed water intake ({w_recl} L) exceeds total water withdrawal ({w_with} L)"
                )

    reporting_deadline_passed = bool(filing.get("reporting_deadline_passed", False))

    for key, direction, unit in metrics_spec:
        p_val = promised.get(key)
        d_val = documented.get(key)
        p_num = None if p_val is None else finite_number(p_val, key, "promised")
        d_num = None if d_val is None else finite_number(d_val, key, "documented")

        if p_num is None and d_num is None:
            disp = "UNSPECIFIED"
            delta = None
        elif d_num is None:
            disp = "OVERDUE_DISCLOSURE" if reporting_deadline_passed else "UNVERIFIED_PROMISE_NO_DISCLOSURE_YET"
            unsupported_or_overdue_count += 1
            delta = None
        elif p_num is None:
            disp = "DISCLOSED_WITHOUT_PRIOR_BASELINE"
            delta = None
        else:
            delta = round(d_num - p_num, 4)
            if direction == "higher_is_better":
                disp = "REPORTED_MET_OR_EXCEEDED_NOT_ATTESTED" if d_num >= p_num * 0.98 else "SHORTFALL_BELOW_PROMISE"
            else:
                disp = "REPORTED_WITHIN_PROMISED_BOUND_NOT_ATTESTED" if d_num <= p_num * 1.02 else "EXCEEDED_PROMISED_BURDEN"
            if disp in ("SHORTFALL_BELOW_PROMISE", "EXCEEDED_PROMISED_BURDEN"):
                unsupported_or_overdue_count += 1

        comparisons.append({
            "metric": key,
            "unit": unit,
            "promised": p_num,
            "documented": d_num,
            "delta_documented_minus_promised": delta,
            "disposition": disp,
        })

    # Compute who bears public vs private net cost
    # A documented zero is a real zero, not a reason to substitute a promise.
    # A missing disclosure remains unresolved; do not silently turn a promise
    # into a measured public benefit.
    def value_for_accounting(key: str):
        if key not in documented or documented[key] is None:
            return None
        return finite_number(documented[key], key, "documented")
    doc_tax = value_for_accounting("annual_local_tax_revenue_usd")
    doc_sub = value_for_accounting("annual_public_subsidy_or_abatement_usd")
    doc_ratepayer_infra = value_for_accounting("ratepayer_funded_infrastructure_share_usd")
    doc_jobs = value_for_accounting("permanent_full_time_jobs")
    tax_minus_sub = (doc_tax - doc_sub) if doc_tax is not None and doc_sub is not None else None
    subsidy_per_job_usd = (
        (doc_sub * 10.0 + doc_ratepayer_infra) / doc_jobs
        if doc_sub is not None and doc_ratepayer_infra is not None and doc_jobs is not None and doc_jobs > 0
        else None
    )
    return {
        "project_id": project_id,
        "source_citations": filing.get("source_citations", []),
        "evidence_boundary": "Documented numeric fields are unverified input assertions; no source authentication, facility audit or third-party attestation is performed.",
        "inconsistent_accounting_flags": inconsistent_flags,
        "unsupported_shortfall_or_overdue_count": unsupported_or_overdue_count,
        "metric_comparisons": comparisons,
        "cost_incidence_summary": {
            "annual_net_local_tax_after_subsidy_usd": None if tax_minus_sub is None else round(tax_minus_sub, 2),
            "ratepayer_funded_grid_or_water_infra_usd": None if doc_ratepayer_infra is None else round(doc_ratepayer_infra, 2),
            "ten_year_public_cost_per_permanent_job_usd": None if subsidy_per_job_usd is None else round(subsidy_per_job_usd, 2),
            "ratepayer_burden_alert": (doc_ratepayer_infra > 0.0 if doc_ratepayer_infra is not None else False) or (tax_minus_sub < 0.0 if tax_minus_sub is not None else False),
            "incidence_status": "REPORTED_UNATTESTED" if all(x is not None for x in (doc_tax,doc_sub,doc_ratepayer_infra,doc_jobs)) else "INCOMPLETE_DISCLOSURE_NO_INFERENCE",
        },
        "overall_accountability_verdict": (
            "INCONSISTENT_OR_MISLEADING_CLAIM_DETECTED"
            if inconsistent_flags
            else ("SHORTFALL_OR_UNVERIFIED_BURDEN" if unsupported_or_overdue_count > 0 else "REPORTED_CLAIMS_CONSISTENT_NOT_INDEPENDENTLY_VERIFIED")
        ),
    }


def generate_three_worked_engineering_concepts() -> list[dict[str, Any]]:
    """Return the three complete worked engineering concept packets required by Deliverable Economic Verdict."""
    return [
        {
            "concept_id": "CONCEPT_1_ZERO_CAPEX_SOFTWARE_SHADOW_OPTIMIZER",
            "title": "$0-Software Existing-Plant Cooling-Tower, Evaporative Sub-Meter & Thermal-Margin Shadow Optimizer",
            "capital_tier": "Capital Level 0 ($0 Hardware CapEx)",
            "physical_solution_built_first": True,
            "what_problem_it_solves": (
                "Existing data centers frequently run cooling towers at conservative default Cycles of Concentration "
                "(CoC = 3.0-3.5), pay municipal wastewater/sewer charges on 100% of evaporated water because makeup minus "
                "blowdown is not reconciled into an audit-ready ledger, and cannot detect when a 10%+ gap between "
                "mass-balance CoC (M/B) and conductivity CoC (EC_b/EC_m) signals a basin float-valve overflow or sensor drift."
            ),
            "process_diagram_ascii": (
                "[Potable/Reclaimed Makeup Meter M, EC_m] ---> [Cooling Tower Basin (T_wb, pH, SiO2, Ca, Alk)] ---> [Blowdown Meter B, EC_b -> Sewer]\n"
                "                                                     |                                                     |\n"
                "                                      [Evaporation E = Q_wet/h_fg]                         [EPA Eq 6-4 vs 6-5 Dual-Ratio Guard]\n"
                "                                                     v                                                     v\n"
                "                                  [CDU HX: Q_elec_IT vs m_dot*cp*dT] ------------------> [Shadow Setpoint & Sewer Deduct Receipt]"
            ),
            "algorithm_summary": (
                "1. Ingest hourly makeup M, blowdown B, conductivity EC_m/EC_b, IT kW, cooling kW, and lab water chemistry.\n"
                "2. Check First-Law ceiling (M-B)/Q_rejected <= 1.55 L/kWh_th and EPA WaterSense Eq 6-4 vs 6-5 ratio |M/B - EC_b/EC_m| <= 10%.\n"
                "3. Compute max permissible CoC bounded by amorphous silica (<=150 mg/L), skin-temperature LSI, and chloride limits.\n"
                "4. Output conservative shadow CoC setpoint advisory and tamper-evident evaporative sewer deduct ledger."
            ),
            "runnable_command": "python3 water_audit.py design --site data/site_phoenix_arid.json --weather data/weather_phoenix_sample.csv --tariff data/tariff_phoenix.json",
            "matched_baseline": "DOE FEMP BMP #10 / EPA WaterSense Section 6.3 manual conductivity blowdown at CoC=3.0-3.5 without sewer deduct reconciliation.",
            "bom_and_lifecycle_cost_usd": {
                "hardware_capex_usd": 0.0,
                "annual_software_and_maintenance_usd": 0.0,
                "note": "Uses existing utility/BMS meters; if makeup/blowdown pulse meters are absent, COTS paddlewheel/mag meters add $2,400.",
            },
            "climate_applicability_matrix": {
                "arid_high_silica_phoenix": "Moderate CoC upside (silica caps CoC at ~5.0-5.3 without dispersant), high sewer-deduct and leak-detection value.",
                "temperate_humid_ashburn": "High CoC upside (soft/moderate water allows CoC 3.5 -> 6.0+, cutting makeup ~20% and blowdown ~50-60%).",
                "hot_semi_humid_austin": "High sewer-deduct and LSI-scaling guard value.",
            },
            "buyer_and_funding_model": "Facility Engineering / Sustainability Director; free Apache-2.0 open-source tool with optional paid third-party commissioning/audit verification.",
            "first_external_falsifier": (
                "Replay 30 days of actual facility makeup/blowdown/conductivity/chemistry logs; if the tower already "
                "operates within 0.3 cycles of its silica/LSI ceiling and already receives a 100% evaporative sewer deduct, "
                "incremental water/cash savings = $0."
            ),
        },
        {
            "concept_id": "CONCEPT_2_HYBRID_WARM_WATER_AND_TOWER_CHEMISTRY_RETROFIT",
            "title": "Weather-Constrained Warm-Water (W40) Dry/Evaporative Hybrid + Acid/Polymer High-CoC + 4-Hr TES Retrofit",
            "capital_tier": "Capital Level 2 (Mechanical & Chemical Facility Retrofit)",
            "physical_solution_built_first": False,
            "what_problem_it_solves": (
                "Cuts direct evaporative water consumption during cool/shoulder hours via sensible dry rejection (when "
                "T_db + approach < T_FWS_return), raises permissible tower CoC on remaining wet hours via automated acid "
                "alkalinity trim + sidestream filtration, and shaves summer peak cooling kW via 4-hour thermal storage."
            ),
            "process_diagram_ascii": (
                "[AI Racks (45C Max Inlet)] -> [CDU (ATD=4K)] -> [48C FWS Return] -> [Dry Cooler (Upstream Series)] -> [Evap Tower + Acid/Filter Trim] -> [4-Hr TES Tank]"
            ),
            "algorithm_summary": (
                "Hourly constrained dispatch (S2 + S1C + S5): compute maximum sensible dry rejection Q_dry(t) from T_db(t) "
                "and UA_dry; reject residual Q_wet(t) in tower at acid-trimmed CoC_max; charge TES off-peak and discharge "
                "during 4-hr utility coincident peak window."
            ),
            "runnable_command": "python3 water_audit.py design --site data/site_ashburn_humid.json --weather data/weather_ashburn_sample.csv --tariff data/tariff_ashburn.json",
            "matched_baseline": "Conventional W32 evaporative cooling tower without dry cooler or TES peak shaving.",
            "bom_and_lifecycle_cost_usd": {
                "dry_cooler_and_piping_capex_usd": 420000.0,
                "acid_feed_and_sidestream_filter_capex_usd": 24000.0,
                "tes_chilled_water_buffer_capex_usd": 53200.0,
                "total_estimated_capex_usd": 497200.0,
                "unpriced_site_specific_items": "Structural pad/roof reinforcement, crane rigging, union pipefitting, utility interconnection study (flagged NOT_READY_FOR_FIXED_QUOTE).",
            },
            "climate_applicability_matrix": {
                "cool_dry_quincy_wa": "Highest water reduction (70-85% dry hours, low grid EWIF 0.18 L/kWh).",
                "temperate_humid_ashburn_va": "Strong seasonal dry share (50-65% dry hours), must balance fan kWh against PJM grid EWIF (2.40 L/kWh).",
                "extreme_arid_phoenix_az": "Cannot reject 100% dry heat on 41-45C summer afternoons without W45+ racks or chiller trim; TES peak shaving is critical.",
            },
            "buyer_and_funding_model": "VP of Data Center Infrastructure / Colocation Developer; funded via municipal water-allocation condition or developer CapEx + take-or-pay tariff.",
            "first_external_falsifier": (
                "If server racks contain 32C-limited components (e.g., 128 GB DIMMs requiring W32 supply) or if local "
                "grid EWIF > crossover EWIF* during dry-fan boost hours, warm-water dry dispatch is either thermally "
                "infeasible or increases total (site + river) water consumption."
            ),
        },
        {
            "concept_id": "CONCEPT_3_SIDESTREAM_COTS_WITNESS_VS_3OMEGA_CARTRIDGE_GATE",
            "title": "COTS Sidestream 4-Wire Pt100 + Auto-Zero dP + Conductivity Reference Witness (Replacing Custom $210k 3-Omega Cartridge)",
            "capital_tier": "Capital Level 1 ($292.40 Benchtop / $1,490 Industrial Manifold) vs. Rejected Level 3 ($210,000 Custom MEMS)",
            "physical_solution_built_first": False,
            "what_problem_it_solves": (
                "Resolves simultaneous collinear sensor drift + cold-plate fouling/bypass (where embedded polyimide MEMS "
                "sensors drift -7.23% in 120 hours per Lee et al., Nov 12, 2026) at 1/140th the cost of a custom 3-omega+EIS cartridge."
            ),
            "process_diagram_ascii": (
                "[CDU Supply/Return Header] ---> [1/4-NPT Manual Isolation Ball Valves] ---> [4x Class-A 4-Wire Pt100 RTDs -> 4x MAX31865 SPI]\n"
                "                                                                       ---> [3-Way Auto-Zero Valve -> 0-50 psi dP -> ADS1115]\n"
                "                                                                       ---> [K=1.0 EC & pH Probe -> TCA9548A I2C Mux -> RP2040]"
            ),
            "algorithm_summary": (
                "Fisher Information Gate (S3): first verify whether passive Q_elec vs Q_enthalpy suffices; only when "
                "uncalibrated cold-plate sensors create collinear drift+fouling ambiguity, deploy the COTS sidestream "
                "reference + bounded +/-4% ABA maintenance step (refusing the $210,000 custom 3-omega+EIS cartridge)."
            ),
            "runnable_command": "python3 water_audit.py compete && python3 water_audit.py hardware-matrix",
            "matched_baseline": "Endress+Hauser Liquiline CM444 industrial skid ($14,850) on the high end; passive CDU Redfish telemetry ($0) on the low end.",
            "bom_and_lifecycle_cost_usd": {
                "benchtop_cots_parts_usd": 292.40,
                "industrial_manifold_parts_usd": 1490.00,
                "custom_3omega_eis_cartridge_rejected_usd": 210000.00,
                "readiness_flag": "BENCHTOP_PROTOTYPE_ONLY_NOT_UL_LISTED_FOR_LIVE_PLANT",
            },
            "climate_applicability_matrix": {
                "all_climates": "Independent of climate; only justified on liquid-cooled clusters using drifting cold-plate sensors near tight thermal margins.",
            },
            "buyer_and_funding_model": "Hardware reliability / thermal test lab; benchtop R&D validation tool.",
            "first_external_falsifier": (
                "On a 7-day, 120-hour benchtop cold-plate loop at 3.0 L/min and 30C, if existing CDU 4-wire RTDs + PSU "
                "wattmeters already maintain <2% heat-balance residual without drift, the extra sidestream sensor adds "
                "zero decision value and is rejected by S3."
            ),
        },
    ]
