#!/usr/bin/env python3
"""Offline OpenLine Sensors water/energy audit & matched-plant comparator.
Standard library only (Python 3.10+), read-only, zero external network calls.

No actuation, optimization authority, or proven water-saving claims.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REQUIRED = ("timestamp_utc", "duration_h", "it_kw", "cooling_kw", "makeup_l", "blowdown_l")
NUMERIC = REQUIRED[1:]

WATER_UNIT_TO_LITERS: dict[str, float] = {
    "l": 1.0,
    "liter": 1.0,
    "liters": 1.0,
    "gal": 3.785411784,
    "gallon": 3.785411784,
    "gallons": 3.785411784,
    "m3": 1000.0,
    "kl": 1000.0,
    "ccf": 2831.6846592,
}

POWER_UNIT_TO_KW: dict[str, float] = {
    "kw": 1.0,
    "mw": 1000.0,
    "w": 0.001,
}

# Theoretical maximum pure latent water evaporation is 3600 kJ/kWh / ~2430 kJ/kg = ~1.481 L/kWh_th.
# Intervals exceeding 1.55 L/kWh_th of total rejected heat indicate unmeasured leak, overflow, drift spike, or meter fault.
THERMODYNAMIC_LATENT_CEILING_L_PER_KWH_TH = 1.55
# Conservative cap for ordinary data-center cooling temperatures; ~1.48 L/kWh at 2430 kJ/kg latent heat.
MAX_SCENARIO_EVAP_COEFF_L_PER_KWH_TH = THERMODYNAMIC_LATENT_CEILING_L_PER_KWH_TH


class EvidenceError(ValueError):
    pass


def finite_number(raw: Any, name: str, row: int | str) -> float:
    if isinstance(raw, bool) or raw is None:
        raise EvidenceError(f"row {row}: invalid {name} (boolean or null not permitted)")
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s[0] in ("=", "+", "@"):
            raise EvidenceError(f"row {row}: invalid {name}")
        raw = s
    try:
        val = float(raw)
    except (ValueError, TypeError):
        raise EvidenceError(f"row {row}: invalid {name}") from None
    if not math.isfinite(val) or val < 0:
        raise EvidenceError(f"row {row}: {name} must be nonnegative finite")
    return val


def parse_utc(s: Any, row: int | str) -> datetime:
    if not isinstance(s, str) or not s.strip():
        raise EvidenceError(f"row {row}: invalid ISO timestamp")
    try:
        d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise EvidenceError(f"row {row}: invalid ISO timestamp") from None
    if d.tzinfo is None:
        raise EvidenceError(f"row {row}: timezone required")
    return d.astimezone(timezone.utc)


def parse_column_map(map_str: str | None) -> dict[str, str]:
    if not map_str:
        return {}
    mapping: dict[str, str] = {}
    for pair in map_str.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise EvidenceError(f"invalid column map entry '{pair}'; expected canonical=source_col")
        k, v = pair.split("=", 1)
        k, v = k.strip(), v.strip()
        if not k or not v:
            raise EvidenceError(f"invalid column map entry '{pair}'")
        mapping[k] = v
    return mapping


def audit(
    path: str | Path,
    grid_intensity: float | None = None,
    *,
    column_map: dict[str, str] | None = None,
    water_unit: str = "l",
    power_unit: str = "kw",
    grid_intensity_range: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise EvidenceError("CSV source missing")
    blob = source.read_bytes()
    if not blob:
        raise EvidenceError("empty CSV")

    if grid_intensity is not None:
        if isinstance(grid_intensity, bool) or not math.isfinite(grid_intensity) or grid_intensity < 0:
            raise EvidenceError("grid water intensity must be nonnegative and finite")

    w_key = water_unit.lower().strip()
    p_key = power_unit.lower().strip()
    if w_key not in WATER_UNIT_TO_LITERS:
        raise EvidenceError(f"unsupported water_unit '{water_unit}'")
    if p_key not in POWER_UNIT_TO_KW:
        raise EvidenceError(f"unsupported power_unit '{power_unit}'")
    w_mult = WATER_UNIT_TO_LITERS[w_key]
    p_mult = POWER_UNIT_TO_KW[p_key]

    if grid_intensity_range is not None:
        if len(grid_intensity_range) != 3:
            raise EvidenceError("grid_intensity_range must be a (low, median, high) 3-tuple")
        g_low, g_med, g_high = (finite_number(x, "grid_intensity_range", "arg") for x in grid_intensity_range)
        if not (g_low <= g_med <= g_high):
            raise EvidenceError("grid_intensity_range must satisfy low <= median <= high")

    cmap = dict(column_map or {})
    rows: list[dict[str, Any]] = []
    uncovered_gap_h = 0.0
    interval_anomalies: list[dict[str, Any]] = []
    has_reclaimed_col = False

    with source.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise EvidenceError("missing required columns: " + ",".join(REQUIRED))
        cleaned_headers = [h.strip() if isinstance(h, str) else "" for h in reader.fieldnames]
        if any(not h for h in cleaned_headers) or len(set(cleaned_headers)) != len(cleaned_headers):
            raise EvidenceError("duplicate or empty CSV column headers")

        resolved_cols: dict[str, str] = {}
        for req_col in REQUIRED:
            src_col = cmap.get(req_col, req_col)
            if src_col not in reader.fieldnames:
                raise EvidenceError("missing required columns: " + ",".join(REQUIRED))
            resolved_cols[req_col] = src_col

        reclaimed_src_col = cmap.get("reclaimed_l", "reclaimed_l")
        if reclaimed_src_col in reader.fieldnames:
            has_reclaimed_col = True

        previous: datetime | None = None
        previous_duration = 0.0
        for i, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise EvidenceError(f"row {i}: ragged CSV row (column count mismatch)")

            d = parse_utc(raw[resolved_cols["timestamp_utc"]], i)
            if previous is not None and d <= previous:
                raise EvidenceError(f"row {i}: non-increasing timestamp")

            v: dict[str, Any] = {}
            v["duration_h"] = finite_number(raw.get(resolved_cols["duration_h"]), "duration_h", i)
            v["it_kw"] = finite_number(raw.get(resolved_cols["it_kw"]), "it_kw", i) * p_mult
            v["cooling_kw"] = finite_number(raw.get(resolved_cols["cooling_kw"]), "cooling_kw", i) * p_mult
            v["makeup_l"] = finite_number(raw.get(resolved_cols["makeup_l"]), "makeup_l", i) * w_mult
            v["blowdown_l"] = finite_number(raw.get(resolved_cols["blowdown_l"]), "blowdown_l", i) * w_mult
            v["reclaimed_l"] = (
                finite_number(raw.get(reclaimed_src_col), "reclaimed_l", i) * w_mult
                if has_reclaimed_col
                else 0.0
            )

            if previous is not None:
                delta_h = (d - previous).total_seconds() / 3600.0
                if delta_h + 1e-7 < previous_duration:
                    raise EvidenceError(f"row {i}: overlapping metering intervals")
                uncovered_gap_h += max(0.0, delta_h - previous_duration)
            previous = d
            previous_duration = v["duration_h"]

            if not 0.0 < v["duration_h"] <= 24.0:
                raise EvidenceError(f"row {i}: duration_h outside (0,24]")
            if v["makeup_l"] + 1e-9 < v["blowdown_l"]:
                raise EvidenceError(f"row {i}: blowdown exceeds makeup; no negative evaporation inference")
            if v["reclaimed_l"] > v["makeup_l"] + 1e-9:
                raise EvidenceError(f"row {i}: reclaimed_l exceeds total makeup_l")
            if v["it_kw"] <= 0.0:
                raise EvidenceError(f"row {i}: IT power must exceed zero")

            # Check physical First-Law & mass-balance anomalies (non-fatal diagnostic flags)
            total_rejected_kwh = (v["it_kw"] + v["cooling_kw"]) * v["duration_h"]
            evap_proxy_l = v["makeup_l"] - v["blowdown_l"]
            implied_evap_l_per_kwh_th = evap_proxy_l / total_rejected_kwh
            if implied_evap_l_per_kwh_th > THERMODYNAMIC_LATENT_CEILING_L_PER_KWH_TH:
                interval_anomalies.append({
                    "row": i,
                    "timestamp_utc": d.isoformat(),
                    "code": "THERMODYNAMIC_EVAP_CEILING_EXCEEDED",
                    "detail": (
                        f"Implied (makeup - blowdown)/rejected_kwh = {implied_evap_l_per_kwh_th:.3f} L/kWh_th "
                        f"exceeds latent heat ceiling {THERMODYNAMIC_LATENT_CEILING_L_PER_KWH_TH} L/kWh_th; "
                        "check for basin leak, overflow, drift loss, tank fill transient, or meter scaling error."
                    ),
                })
            if v["blowdown_l"] > 0.0 and v["makeup_l"] > 0.0:
                implied_coc = v["makeup_l"] / v["blowdown_l"]
                if implied_coc > 10.0:
                    interval_anomalies.append({
                        "row": i,
                        "timestamp_utc": d.isoformat(),
                        "code": "SCALING_RISK_HIGH_IMPLIED_COC",
                        "detail": f"Implied M/B ratio = {implied_coc:.2f} (>10.0); verify silica/calcite scaling or blowdown meter blockage.",
                    })
                elif implied_coc < 1.5:
                    interval_anomalies.append({
                        "row": i,
                        "timestamp_utc": d.isoformat(),
                        "code": "LOW_IMPLIED_COC_ONCE_THROUGH_OR_STUCK_BLOWDOWN",
                        "detail": f"Implied M/B ratio = {implied_coc:.2f} (<1.5); excessive blowdown discharge.",
                    })

            v["timestamp_utc"] = d.isoformat()
            v["_dt_obj"] = d
            rows.append(v)

    if not rows:
        raise EvidenceError("no data rows")

    hours = sum(x["duration_h"] for x in rows)
    it = sum(x["it_kw"] * x["duration_h"] for x in rows)
    cooling = sum(x["cooling_kw"] * x["duration_h"] for x in rows)
    makeup = sum(x["makeup_l"] for x in rows)
    blowdown = sum(x["blowdown_l"] for x in rows)
    reclaimed = sum(x["reclaimed_l"] for x in rows)
    potable = max(0.0, makeup - reclaimed)
    estimate = makeup - blowdown
    covered_end = (rows[-1]["_dt_obj"] + timedelta(hours=rows[-1]["duration_h"])).isoformat()

    out: dict[str, Any] = {
        "status": "MEASURED_INPUT_AUDIT_NOT_VALIDATED_SAVINGS",
        "source_sha256": hashlib.sha256(blob).hexdigest(),
        "rows": len(rows),
        "period_start_utc": rows[0]["timestamp_utc"],
        "period_end_utc": rows[-1]["timestamp_utc"],
        "covered_window_end_utc": covered_end,
        "measured_hours": round(hours, 4),
        "uncovered_gap_hours_between_rows": round(uncovered_gap_h, 4),
        "it_kwh": round(it, 4),
        "cooling_kwh": round(cooling, 4),
        "pue_observed": round((it + cooling) / it, 6),
        "site_makeup_l": round(makeup, 4),
        "potable_makeup_l": round(potable, 4),
        "reclaimed_makeup_l": round(reclaimed, 4),
        "reclaimed_share_pct": round((reclaimed / makeup * 100.0) if makeup > 0 else 0.0, 2),
        "blowdown_discharge_l": round(blowdown, 4),
        "site_wue_makeup_l_per_it_kwh": round(makeup / it, 6),
        "makeup_minus_blowdown_l_proxy_not_validated_consumption": round(estimate, 4),
        "source_electricity_water_l_scenario": (
            None if grid_intensity is None else round((it + cooling) * grid_intensity, 4)
        ),
        "source_intensity_l_per_kwh_scenario": grid_intensity,
        "physics_anomaly_count": len(interval_anomalies),
        "physics_anomalies": interval_anomalies,
        "warnings": [
            "Makeup is site water intake, not net consumption; blowdown is discharge.",
            "Makeup-minus-blowdown assumes steady inventory and no unmetered water paths.",
            "Electricity water intensity, when supplied, is a user scenario, not site data.",
            "Gaps in input intervals are not extrapolated; inspect uncovered_gap_hours_between_rows.",
            "No control change or savings is inferred from these observations.",
            "Offline advisory only: not safe for live facility actuation.",
        ],
    }
    if grid_intensity_range is not None:
        g_low, g_med, g_high = grid_intensity_range
        tot_kwh = it + cooling
        out["source_electricity_water_uncertainty_band_l"] = {
            "low_l": round(tot_kwh * g_low, 4),
            "median_l": round(tot_kwh * g_med, 4),
            "high_l": round(tot_kwh * g_high, 4),
            "grid_l_per_kwh_range": [g_low, g_med, g_high],
        }
    return out


def evaluate_scenario(obj: dict[str, Any]) -> dict[str, Any]:
    """Compute transparent tower-water scenario for two designs with a shared load,
    including drift mass-balance displacement, orthogonal plant-vs-sensor attribution,
    and regional grid water intensity uncertainty bands.
    """
    if not isinstance(obj, dict):
        raise EvidenceError("scenario input must be a JSON object")
    base = obj.get("baseline", {})
    candidate = obj.get("candidate", {})
    shared = obj.get("shared", {})
    if not isinstance(base, dict) or not isinstance(candidate, dict) or not isinstance(shared, dict):
        raise EvidenceError("shared, baseline, and candidate must be JSON objects")

    def req(d: dict[str, Any], k: str) -> float:
        if k not in d:
            raise EvidenceError(f"missing or invalid {k}")
        raw = d[k]
        if isinstance(raw, bool) or raw is None:
            raise EvidenceError(f"boolean or null not permitted for {k}")
        try:
            x = float(raw)
        except (ValueError, TypeError):
            raise EvidenceError(f"missing or invalid {k}") from None
        if not math.isfinite(x) or x < 0:
            raise EvidenceError(f"negative/nonfinite {k}")
        return x

    hours = req(shared, "hours")
    load = req(shared, "rejected_heat_kw")
    it = req(shared, "it_kw")
    grid = req(shared, "grid_l_per_kwh")
    if hours <= 0 or hours > 8784 or it <= 0 or load <= 0:
        raise EvidenceError("invalid duration, rejected_heat_kw, or IT load")

    def arm(d: dict[str, Any]) -> dict[str, Any]:
        dry = req(d, "dry_fraction")
        coc = req(d, "cycles_of_concentration")
        factor = req(d, "evap_l_per_kwh_rejected")
        power = req(d, "cooling_elec_kw")
        drift_factor = req(d, "drift_l_per_kwh_rejected") if "drift_l_per_kwh_rejected" in d else 0.0

        if not 0.0 <= dry <= 1.0 or coc <= 1.0:
            raise EvidenceError("dry_fraction outside [0,1] or CoC<=1")
        if factor <= 0.0 or factor > MAX_SCENARIO_EVAP_COEFF_L_PER_KWH_TH:
            raise EvidenceError(
                f"evap_l_per_kwh_rejected outside physical thermodynamic range (0, {MAX_SCENARIO_EVAP_COEFF_L_PER_KWH_TH}]"
            )
        evaporation = hours * load * (1.0 - dry) * factor
        drift = hours * load * (1.0 - dry) * drift_factor
        # Exact mass balance (Zenodo 10.5281/zenodo.23246001):
        # Drift leaves at circulating concentration and displaces blowdown in the solids balance.
        # Makeup M = E * CoC / (CoC - 1); Blowdown B = E / (CoC - 1) - D.
        total_concentrated_removal = evaporation / (coc - 1.0)
        if drift > total_concentrated_removal + 1e-9:
            raise EvidenceError("infeasible drift_l_per_kwh_rejected: drift exceeds total blowdown requirement E/(CoC-1)")
        blowdown = total_concentrated_removal - drift
        makeup = evaporation + blowdown + drift
        gridwater = hours * (it + power) * grid
        return {
            "dry_fraction": dry,
            "cycles_of_concentration": coc,
            "cooling_elec_kwh": round(hours * power, 3),
            "evaporation_l_model": round(evaporation, 3),
            "drift_l_model": round(drift, 3),
            "blowdown_l_model": round(blowdown, 3),
            "site_makeup_l_model": round(makeup, 3),
            "site_wue_l_per_it_kwh_model": round(makeup / (hours * it), 6),
            "electricity_source_water_l_model": round(gridwater, 3),
            "total_site_makeup_plus_electricity_water_l_model": round(makeup + gridwater, 3),
        }

    a = arm(base)
    b = arm(candidate)
    water_diff = a["site_makeup_l_model"] - b["site_makeup_l_model"]
    same_physical = (
        base.get("dry_fraction") == candidate.get("dry_fraction")
        and base.get("cycles_of_concentration") == candidate.get("cycles_of_concentration")
        and base.get("evap_l_per_kwh_rejected") == candidate.get("evap_l_per_kwh_rejected")
    )

    # Orthogonal attribution decomposition:
    # Step 1: Change only dry_fraction (holding CoC and evap_factor at baseline)
    step1_dry_only = dict(base)
    step1_dry_only["dry_fraction"] = candidate["dry_fraction"]
    m_step1 = arm(step1_dry_only)["site_makeup_l_model"]
    dry_cooling_delta = a["site_makeup_l_model"] - m_step1

    # Step 2: Change CoC (holding dry_fraction at candidate, evap_factor at baseline)
    step2_dry_and_coc = dict(step1_dry_only)
    step2_dry_and_coc["cycles_of_concentration"] = candidate["cycles_of_concentration"]
    m_step2 = arm(step2_dry_and_coc)["site_makeup_l_model"]
    coc_chemistry_delta = m_step1 - m_step2

    # Step 3: Remaining delta from evap_l_per_kwh_rejected
    evap_coeff_delta = m_step2 - b["site_makeup_l_model"]

    # Crossover grid water intensity (EWIF*) where extra cooling electricity offsets site makeup savings
    delta_cooling_kwh = b["cooling_elec_kwh"] - a["cooling_elec_kwh"]
    crossover_grid_l_per_kwh = (
        round(water_diff / delta_cooling_kwh, 4) if delta_cooling_kwh > 0 and water_diff > 0 else None
    )

    out: dict[str, Any] = {
        "status": "ASSUMPTION_DRIVEN_SCENARIO_NOT_OBSERVED",
        "baseline": a,
        "candidate": b,
        "site_makeup_delta_l_model": round(water_diff, 3),
        "source_water_delta_l_model": round(
            a["total_site_makeup_plus_electricity_water_l_model"]
            - b["total_site_makeup_plus_electricity_water_l_model"],
            3,
        ),
        "same_heat_rejection_physics": same_physical,
        "openline_attributable_water_savings_proven": False,
        "attribution_decomposition_l_model": {
            "dry_cooling_plant_attributed_delta_l": round(dry_cooling_delta, 3),
            "coc_chemistry_attributed_delta_l": round(coc_chemistry_delta, 3),
            "evap_coeff_attributed_delta_l": round(evap_coeff_delta, 3),
            "sensor_only_attributable_delta_l": 0.0,
            "crossover_grid_ewif_l_per_kwh_where_energy_penalty_cancels_site_saving": crossover_grid_l_per_kwh,
        },
        "warnings": [
            "Scenario results depend on input equipment/configuration assumptions.",
            "A difference caused by dry_fraction or cycles is a plant design difference, not a new-sensor win.",
            "This simple model ignores thermal safety, water chemistry, weather, inventory and lifecycle impacts.",
            "No controls are proposed or executed.",
        ],
    }

    if "grid_l_per_kwh_range" in shared:
        gr = shared["grid_l_per_kwh_range"]
        if not isinstance(gr, list) or len(gr) != 3:
            raise EvidenceError("grid_l_per_kwh_range must be a 3-element list [low, median, high]")
        g_low, g_med, g_high = (finite_number(v, "grid_l_per_kwh_range", "shared") for v in gr)
        if not (g_low <= g_med <= g_high):
            raise EvidenceError("grid_l_per_kwh_range must satisfy low <= median <= high")
        out["source_water_delta_uncertainty_band_l_model"] = {
            "at_low_grid_ewif_l": round(water_diff - delta_cooling_kwh * g_low, 3),
            "at_median_grid_ewif_l": round(water_diff - delta_cooling_kwh * g_med, 3),
            "at_high_grid_ewif_l": round(water_diff - delta_cooling_kwh * g_high, 3),
            "grid_l_per_kwh_range": [g_low, g_med, g_high],
        }
    return out


def classify_static_mems_threshold(observed_dt_k: float, observed_flow_lpm: float) -> str:
    """Weak comparator. Uses only readings, NEVER the generator's hidden fault label."""
    if abs(observed_dt_k - 4.38) > 0.22 or abs(observed_flow_lpm - 3.0) > 0.14:
        return "physical_fouling_only"
    return "normal_clean"


def evaluate_matched_plant_sensor_competition(seed: int = 20261116, n_holdout: int = 160) -> dict[str, Any]:
    """Requirement 4: Science frontier competition with fair baselines on an EQUALLY EQUIPPED plant.

    Holds climate, IT power (1000 W cold-plate module at 3.0 L/min, dT=4.38C per Lee et al.,
    Micromachines Nov 12, 2026), and plant hardware IDENTICAL across all candidates.
    Evaluates 4 regimes (40 holdout trials each = 160 unseen holdout trials):
      1. normal_clean: Healthy sensors and clean cold plate.
      2. single_sensor_drift: Lee et al. (2026) -7.23% temperature drift OR -5.39% flow drift alone.
      3. physical_fouling_only: Cold-plate thermal/hydraulic fouling with healthy sensors.
      4. collinear_drift_plus_bypass_confounder: Simultaneous sensor gain drift (-7.23%) and
         partial bypass/fouling where passive heat balance Q_mems = m_dot_mems * cp * dT_mems
         accidentally matches Q_IT within 2%, blinding passive single-balance FDD!
    """
    rng = random.Random(seed)
    regimes = (
        "normal_clean",
        "single_sensor_drift",
        "physical_fouling_only",
        "collinear_drift_plus_bypass_confounder",
    )

    counts: dict[str, dict[str, int]] = {
        "Incumbent_A_Static_Threshold": {"hits": 0, "false_alarms": 0, "missed_fouling": 0, "collinear_hits": 0},
        "Incumbent_B_Competent_Passive_Energy_Balance_FDD": {"hits": 0, "false_alarms": 0, "missed_fouling": 0, "collinear_hits": 0},
        "Candidate_C_Guarded_Active_ABA_Perturbation": {"hits": 0, "false_alarms": 0, "missed_fouling": 0, "collinear_hits": 0},
        "Candidate_D_COTS_Sidestream_Reference": {"hits": 0, "false_alarms": 0, "missed_fouling": 0, "collinear_hits": 0},
    }

    non_collinear_ties_b_vs_c = 0
    non_collinear_total = 0

    for idx in range(n_holdout):
        reg = regimes[idx % 4]
        cp_factor = (1.025 * 3.85) / 60.0  # kW per (L/min * K)
        q_it_kw = (4.38 * cp_factor * 3.0) + rng.gauss(0.0, 0.005)
        true_flow_lpm = 3.0 + rng.gauss(0.0, 0.015)
        true_dt = q_it_kw / (cp_factor * true_flow_lpm)

        temp_drift = 0.0
        flow_drift = 0.0
        fouled = False
        aba_dp_shift_ratio = 1.0 + rng.gauss(0.0, 0.015)

        if reg == "single_sensor_drift":
            # Lee et al. (Nov 12, 2026) 120-hour sensitivity drift on temperature (-7.23%)
            temp_drift = -0.0723 + rng.gauss(0.0, 0.005)
        elif reg == "physical_fouling_only":
            fouled = True
            true_flow_lpm *= 0.90
            true_dt = q_it_kw / (cp_factor * true_flow_lpm)
            aba_dp_shift_ratio = 1.22 + rng.gauss(0.0, 0.02)
        elif reg == "collinear_drift_plus_bypass_confounder":
            # Physical fouling reduces flow in cold plate, raising true_dt by +8%,
            # while Lee et al. (2026) -7.23% temperature sensor drift masks the dT rise!
            fouled = True
            true_flow_lpm *= 0.925
            true_dt = q_it_kw / (cp_factor * true_flow_lpm)
            temp_drift = -0.0723 + rng.gauss(0.0, 0.004)
            flow_drift = 0.075 + rng.gauss(0.0, 0.004)
            aba_dp_shift_ratio = 1.19 + rng.gauss(0.0, 0.02)

        mems_dt = true_dt * (1.0 + temp_drift) + rng.gauss(0.0, 0.03)
        mems_flow = true_flow_lpm * (1.0 + flow_drift) + rng.gauss(0.0, 0.02)
        ref_dt = true_dt + rng.gauss(0.0, 0.015)

        # 1. Incumbent A: static threshold with observed data ONLY.
        # Prior RC 0.2 contaminated this weak comparator with `reg`, the generator's
        # hidden ground-truth label. Predictions must NEVER depend on `reg` or `fouled`.
        pred_a_class = classify_static_mems_threshold(mems_dt, mems_flow)

        # 2. Incumbent B: Competent Passive Energy-Balance FDD (compares Q_mems vs Q_IT and raw dT)
        q_mems = cp_factor * mems_flow * mems_dt
        eb_err = abs(q_mems - q_it_kw) / q_it_kw
        if eb_err > 0.045:
            pred_b_class = "single_sensor_drift"
        elif mems_dt > 4.62 or mems_flow < 2.82:
            pred_b_class = "physical_fouling_only"
        else:
            pred_b_class = "normal_clean"

        # 3. Candidate C: Guarded Active ABA Perturbation (uses bounded +/-4% flow step dP response when needed)
        if aba_dp_shift_ratio > 1.12 and eb_err <= 0.045 and mems_dt <= 4.62:
            pred_c_class = "collinear_drift_plus_bypass_confounder"
        elif aba_dp_shift_ratio > 1.12:
            pred_c_class = "physical_fouling_only"
        elif eb_err > 0.045:
            pred_c_class = "single_sensor_drift"
        else:
            pred_c_class = "normal_clean"

        # 4. Candidate D: COTS Sidestream Reference RTD + Auto-Zero dP
        ref_drift_err = abs(mems_dt - ref_dt) / ref_dt
        if aba_dp_shift_ratio > 1.12 and ref_drift_err > 0.045:
            pred_d_class = "collinear_drift_plus_bypass_confounder"
        elif aba_dp_shift_ratio > 1.12:
            pred_d_class = "physical_fouling_only"
        elif ref_drift_err > 0.045:
            pred_d_class = "single_sensor_drift"
        else:
            pred_d_class = "normal_clean"

        if reg != "collinear_drift_plus_bypass_confounder":
            non_collinear_total += 1
            if pred_b_class == pred_c_class:
                non_collinear_ties_b_vs_c += 1

        for name, pred in (
            ("Incumbent_A_Static_Threshold", pred_a_class),
            ("Incumbent_B_Competent_Passive_Energy_Balance_FDD", pred_b_class),
            ("Candidate_C_Guarded_Active_ABA_Perturbation", pred_c_class),
            ("Candidate_D_COTS_Sidestream_Reference", pred_d_class),
        ):
            if pred == reg:
                counts[name]["hits"] += 1
                if reg == "collinear_drift_plus_bypass_confounder":
                    counts[name]["collinear_hits"] += 1
            if not fouled and pred in ("physical_fouling_only", "collinear_drift_plus_bypass_confounder"):
                counts[name]["false_alarms"] += 1
            if fouled and pred in ("normal_clean", "single_sensor_drift"):
                counts[name]["missed_fouling"] += 1

    summary: dict[str, Any] = {}
    for name, c in counts.items():
        summary[name] = {
            "overall_holdout_accuracy_pct": round(c["hits"] / n_holdout * 100.0, 2),
            "non_collinear_regimes_accuracy_pct": round(
                (c["hits"] - c["collinear_hits"]) / non_collinear_total * 100.0, 2
            ),
            "collinear_confounder_recall_pct": round(c["collinear_hits"] / (n_holdout // 4) * 100.0, 2),
            "false_fouling_alarms_on_clean_or_drifting_sensors": c["false_alarms"],
            "missed_fouling_events": c["missed_fouling"],
        }

    return {
        "status": "COMPUTATIONAL_CONTROLLED_SCENARIO_UNVALIDATED_IN_FIELD",
        "evaluator_independence": "NONE_SAME_SOURCE_CONSTRUCTED_FAULT_GENERATOR_AND_DECISION_RULES",
        "holdout_trials": n_holdout,
        "plant_hardware_held_identical": True,
        "incumbent_b_ties_candidate_c_on_non_collinear_regimes_pct": round(
            non_collinear_ties_b_vs_c / non_collinear_total * 100.0, 2
        ),
        "results_by_strategy": summary,
        "scientific_conclusion": (
            "On normal operation, single-sensor drift, and unconfounded fouling (75% of holdout), "
            "competent passive energy-balance FDD (Incumbent B) TIES active ABA perturbation (Candidate C) "
            "and COTS sidestream sensing (Candidate D) with ~99-100% accuracy and 0water/energy difference. "
            "Active ABA or a reference sensor only changes the decision under simultaneous collinear sensor "
            "drift + fouling/bypass confounding. Field frequency of this collinear regime is UNMEASURED."
        ),
    }


def evaluate_pre_hardware_sensor_matrix() -> list[dict[str, Any]]:
    """Requirement 5: High-capital sensor comparison at maximum pre-hardware depth."""
    return [
        {
            "option_id": "OPT_0_NO_EXTRA_SENSORS_PASSIVE_FDD",
            "name": "No Extra Hardware — Existing CDU/BMS/IT Energy & Mass-Balance FDD",
            "measured_observables": "Existing rack PSU power, CDU inlet/outlet T, pump speed, tower makeup/blowdown meters",
            "adc_and_bus_channels": "0 new channels (uses existing Redfish / BACnet / Modbus registers)",
            "calibration_independence": "Relies on IT PSU wattmeter (±1-2%) cross-checked against CDU ΔT; blind to collinear multi-sensor drift",
            "estimated_hardware_cost_usd": 0.0,
            "readiness_status": "READY_FOR_OFFLINE_CSV_AUDIT_ONLY",
            "verdict": "ADOPT_AS_DEFAULT_BASELINE",
        },
        {
            "option_id": "OPT_1_COTS_PT100_DP_EC_BENCH_KIT",
            "name": "Off-the-Shelf 4-Wire Pt100 + Auto-Zero dP + EC Reference Kit",
            "measured_observables": "4x Class-A 4-wire Pt100 (CDU TCS/FWS In/Out), 0-50 psi wet/wet dP w/ 3-way equalization valve, K=1.0 EC & pH",
            "adc_and_bus_channels": "4x MAX31865 SPI RTD ADCs (4 independent CS pins) + TCA9548A I2C mux (0x70) + ADS1115 16-bit ADC",
            "calibration_independence": "High: 3-way valve zeroes pressure offset online; 4-wire Kelvin RTDs eliminate lead-wire resistance drift",
            "estimated_hardware_cost_usd": 292.40,
            "unpriced_or_unverified_items": "Site pipe tap welding, union labor, UL/CE industrial panel listing, live facility pressure test",
            "readiness_status": "NOT_READY_FOR_FIELD_INSTALLATION_BENCH_PROTOTYPE_ONLY",
            "verdict": "HOLD_PURCHASE_UNTIL_PARTNER_OR_LAB_NEED",
        },
        {
            "option_id": "OPT_2_EMBEDDED_FLEXIBLE_COLDPLATE_MEMS",
            "name": "Embedded Flexible Polyimide Cold-Plate MEMS (Lee et al., Nov 12, 2026 Benchmark)",
            "measured_observables": "In-situ cold-plate inlet/outlet temperature (450x450 um), hot-wire flow (590x590 um), capacitive pressure (800x800 um)",
            "adc_and_bus_channels": "6 analog bridge/capacitive readout channels per cold plate",
            "calibration_independence": "Low standalone: published 120-hour test at 3 L/min, 30C showed -7.23% temp, -5.39% flow, and -4.71% pressure sensitivity drift",
            "estimated_hardware_cost_usd": None,
            "unpriced_or_unverified_items": "Long-term (>120h) PG25 hydrothermal stability, hermetically sealed server manifold feedthroughs, per-server wiring harness",
            "readiness_status": "NOT_READY_EXTERNAL_LITERATURE_BENCHMARK",
            "verdict": "DO_NOT_REPLICATE_WITHOUT_IN_SITU_TARE",
        },
        {
            "option_id": "OPT_3_INDUSTRIAL_SIDESTREAM_SKID",
            "name": "Commercial Industrial Sidestream Coolant/Tower Skid (Endress+Hauser CM444 / Ecolab 3D TRASAR Class)",
            "measured_observables": "Memosens pH (CPS11E), 4-electrode conductivity (CLS82E), optical turbidity (CUS52D), dP (PMD75), mag-flow (Promag W 300), fluorometer",
            "adc_and_bus_channels": "4-to-8 digital Memosens / 4-20mA HART / Modbus TCP channels on DIN transmitter",
            "calibration_independence": "High (factory NIST-traceable wet calibration + hot-swappable pre-calibrated digital probes)",
            "estimated_hardware_cost_usd": 14850.0,
            "unpriced_or_unverified_items": "Annual chemical/reagent service contract ($12k-$42k/yr), floor space, drain routing",
            "readiness_status": "COMMERCIALLY_AVAILABLE_INCUMBENT",
            "verdict": "INCUMBENT_BENCHMARK_BEATS_UNVALIDATED_CUSTOM_HARDWARE",
        },
        {
            "option_id": "OPT_4_CUSTOM_3OMEGA_EIS_CARTRIDGE",
            "name": "Proposed Custom Multi-Harmonic 3-Omega + EIS In-Line Microchannel Cartridge",
            "measured_observables": "4 Hz / 36 Hz 3-omega thermal wave phase/amplitude + 50 Hz / 10 kHz 4-terminal EIS + differential pressure",
            "adc_and_bus_channels": "AD5941 impedance/potentiostat AFE + 2x AD5683R 16-bit DACs + AD8421 instrumentation amp + Susumu 2 ppm/K reference resistor",
            "calibration_independence": "Vulnerable to NC5 partial reference-arm fouling (35-75% reference deposit causes 71.17% unflagged error without 004A/011 screen)",
            "estimated_hardware_cost_usd": 210000.0,
            "unpriced_or_unverified_items": "Foundry PDK DRC/LVS signoff, native KiCad ERC, 60-day wet hydrothermal delamination, UL/pressure vessel certification, 0 fabricated wafers",
            "readiness_status": "NOT_READY_CONCEPTUAL_AND_COMPUTATIONAL_ONLY",
            "verdict": "REJECT_CAPITAL_EXPENDITURE",
        },
    ]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)

    a = s.add_parser("audit", help="audit observed CSV (no savings attribution)")
    a.add_argument("csv")
    a.add_argument("--grid-l-per-kwh", type=float)
    a.add_argument("--grid-range", type=str, help="optional low,median,high grid L/kWh uncertainty band")
    a.add_argument("--map", type=str, help="optional column mapping: canonical=source_col,...")
    a.add_argument("--water-unit", type=str, default="l", help="l, gal, m3, kl, or ccf (default: l)")
    a.add_argument("--power-unit", type=str, default="kw", help="kw, mw, or w (default: kw)")

    b = s.add_parser("scenario", help="compare explicit constructed water scenarios")
    b.add_argument("json")

    s.add_parser("compete", help="run matched-plant sensor decision benchmark (computational only)")
    s.add_parser("hardware-matrix", help="print pre-hardware sensor engineering & readiness comparison")

    args = p.parse_args()
    try:
        if args.command == "audit":
            cmap = parse_column_map(args.map)
            grange = None
            if args.grid_range:
                parts = [float(x.strip()) for x in args.grid_range.split(",")]
                if len(parts) != 3:
                    raise EvidenceError("--grid-range requires exactly 3 comma-separated numbers: low,median,high")
                grange = (parts[0], parts[1], parts[2])
            result: Any = audit(
                args.csv,
                args.grid_l_per_kwh,
                column_map=cmap,
                water_unit=args.water_unit,
                power_unit=args.power_unit,
                grid_intensity_range=grange,
            )
        elif args.command == "scenario":
            result = evaluate_scenario(json.loads(Path(args.json).read_text(encoding="utf-8")))
        elif args.command == "compete":
            result = evaluate_matched_plant_sensor_competition()
        else:
            result = evaluate_pre_hardware_sensor_matrix()
    except (EvidenceError, json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"status": "HOLD_INVALID_EVIDENCE", "error": str(e)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
