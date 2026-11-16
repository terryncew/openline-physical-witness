"""Comprehensive Test Suite for OpenLine Sensors 004 Solutions Design Engine (`solutions.py`).

Verifies:
- All 7 concrete engineering solutions (S1 through S7) and 5 required output files
- All 11 non-negotiable adversarial tests from the Sensors 004 Replacement Directive
- Independent cross-climate transfer (Phoenix Arid High-Silica -> Ashburn Humid High-EWIF)
- Public-benefit promised-vs-documented claim verification and ratepayer shift detection
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from solutions import (
    check_decision_recall_triggers,
    evaluate_public_benefit_claims,
    evaluate_s1_chemistry_tower_optimizer,
    evaluate_s2_weather_constrained_dispatch,
    evaluate_s3_sensor_observer_information_gate,
    evaluate_s4_water_source_substitution,
    evaluate_s5_grid_and_community_cost_mitigation,
    evaluate_s6_heat_reuse_feasibility,
    generate_three_worked_engineering_concepts,
    load_weather_csv,
    run_design_engine,
)
from water_audit import EvidenceError

ROOT = Path(__file__).resolve().parents[1]


class Solutions004Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.phx_site = json.loads((ROOT / "data/site_phoenix_arid.json").read_text(encoding="utf-8"))
        self.phx_tariff = json.loads((ROOT / "data/tariff_phoenix.json").read_text(encoding="utf-8"))
        self.phx_weather = load_weather_csv(ROOT / "data/weather_phoenix_sample.csv")

        self.ash_site = json.loads((ROOT / "data/site_ashburn_humid.json").read_text(encoding="utf-8"))
        self.ash_tariff = json.loads((ROOT / "data/tariff_ashburn.json").read_text(encoding="utf-8"))
        self.ash_weather = load_weather_csv(ROOT / "data/weather_ashburn_sample.csv")

    # 1. Hot climate where dry cooling cannot reject heat at permitted loop temperatures
    def test_01_hot_climate_dry_cooling_cannot_reject_heat_at_permitted_loop_temp(self) -> None:
        site_w32 = copy.deepcopy(self.phx_site)
        site_w32["rack_max_liquid_inlet_c"] = 32.0
        site_w32["allows_warm_water_w40_rack_upgrade"] = False
        s2 = evaluate_s2_weather_constrained_dispatch(site_w32, self.phx_weather, self.phx_tariff, max_safe_coc=5.0)
        by_id = {p["plant_id"]: p for p in s2["evaluated_plants"]}
        # W40 plant must be marked infeasible when racks are limited to 32C and upgrade is disallowed
        self.assertFalse(by_id["P3_WARM_WATER_W40_HYBRID_DRY_WET"]["feasible"])
        # On the 43C summer peak bin (index 0), P2 (28C FWS supply, 36C return) has 0.0 kW dry rejection!
        p2_summer_bin = by_id["P2_HYBRID_DRY_WET_AT_CURRENT_RACK_LIMIT"]["hourly_dispatch_preview"][0]
        self.assertGreaterEqual(p2_summer_bin["dry_bulb_c"], 41.0)
        self.assertEqual(p2_summer_bin["q_dry_kw"], 0.0)

    # 2. Low water quality where high CoC would scale
    def test_02_low_water_quality_caps_coc_against_scaling(self) -> None:
        bad_water_site = copy.deepcopy(self.phx_site)
        bad_water_site["water_chemistry"]["silica_ppm"] = 52.0  # Very high silica! 150 / 52 = 2.88 max CoC
        bad_water_site["water_chemistry"]["calcium_hardness_ppm_as_caco3"] = 340.0
        s1 = evaluate_s1_chemistry_tower_optimizer(bad_water_site, self.phx_tariff, annual_wet_heat_kwh_th=87_600_000)
        self.assertTrue(s1["feasible"])
        for reg in s1["pareto_chemistry_regimes"]:
            self.assertLessEqual(reg["permissible_max_coc"], 3.40)

    # 3. Apparently greener zero-evap design with higher upstream power-generation water
    def test_03_greener_zero_evap_design_increases_upstream_grid_water(self) -> None:
        high_ewif_tariff = copy.deepcopy(self.phx_tariff)
        high_ewif_tariff["grid_ewif_l_per_kwh"] = 4.5  # Coal/thermoelectric heavy basin
        s2 = evaluate_s2_weather_constrained_dispatch(self.phx_site, self.phx_weather, high_ewif_tariff, max_safe_coc=6.0)
        by_id = {p["plant_id"]: p for p in s2["evaluated_plants"]}
        p3_w40 = by_id["P3_WARM_WATER_W40_HYBRID_DRY_WET"]
        p4_zero_evap = by_id["P4_ZERO_EVAP_DRY_PLUS_CHILLER_RETROFIT"]
        # P4 has 0 site makeup water, but its high chiller kWh causes HIGHER total (site + grid) water than P3!
        self.assertEqual(p4_zero_evap["site_makeup_l"], 0.0)
        self.assertGreater(
            p4_zero_evap["total_site_plus_all_grid_water_l"],
            p3_w40["total_site_plus_all_grid_water_l"],
        )

    # 4. Reclaimed water reduces potable intake but not net evaporation
    def test_04_reclaimed_water_reduces_potable_not_evaporation(self) -> None:
        s4 = evaluate_s4_water_source_substitution(
            self.phx_site,
            self.phx_tariff,
            annual_makeup_needed_l=60_000_000.0,
            annual_evaporation_l=48_000_000.0,
            annual_blowdown_l=12_000_000.0,
        )
        self.assertGreater(s4["potable_withdrawal_reduction_l"], 30_000_000.0)
        self.assertEqual(s4["evaporative_consumption_reduction_from_reclaimed_substitution_l"], 0.0)
        self.assertEqual(s4["site_evaporative_consumption_l"], 48_000_000.0)

    # 5. Cracked/delayed/biased sensor and simultaneous correlated failures
    def test_05_biased_sensor_and_epa_dual_ratio_leak_mismatch_detected(self) -> None:
        leak_site = copy.deepcopy(self.phx_site)
        # Conductivity ratio says CoC = 1800 / 450 = 4.0, but metered M/B = 2200 / 400 = 5.5 (>10% discrepancy!)
        leak_site["water_chemistry"]["makeup_conductivity_us_cm"] = 450.0
        leak_site["water_chemistry"]["blowdown_conductivity_us_cm"] = 1800.0
        leak_site["water_chemistry"]["metered_makeup_l_sample"] = 2200.0
        leak_site["water_chemistry"]["metered_blowdown_l_sample"] = 400.0
        s1 = evaluate_s1_chemistry_tower_optimizer(leak_site, self.phx_tariff, annual_wet_heat_kwh_th=87_600_000)
        self.assertTrue(s1["epa_watersense_eq64_eq65_leak_or_drift_mismatch_detected"])

    # 6. Strong conventional instruments tie or beat novel observer (and custom 3-omega rejected)
    def test_06_strong_conventional_instruments_refuse_extra_hardware(self) -> None:
        well_instrumented = copy.deepcopy(self.phx_site)
        well_instrumented["has_calibrated_redundant_cdu_rtds"] = True
        well_instrumented["has_autozero_differential_pressure"] = True
        well_instrumented["uses_uncalibrated_flexible_coldplate_mems"] = False
        s3 = evaluate_s3_sensor_observer_information_gate(well_instrumented)
        self.assertEqual(s3["decision"], "REFUSE_NEW_HARDWARE_EXISTING_TELEMETRY_SUFFICES")
        self.assertIsNone(s3["selected_intervention"])
        self.assertFalse(s3["custom_3omega_eis_cartridge_accepted"])

        # Even when collinear drift risk IS present, COTS or ABA beats the $210k 3-omega cartridge!
        s3_collinear = evaluate_s3_sensor_observer_information_gate(self.phx_site)
        self.assertFalse(s3_collinear["custom_3omega_eis_cartridge_accepted"])

    # 7. No legitimate heat user within an economically feasible distance
    def test_07_heat_reuse_rejected_without_viable_proximate_offtaker(self) -> None:
        # Phoenix has no heat reuse offtaker
        s6_phx = evaluate_s6_heat_reuse_feasibility(self.phx_site, self.phx_tariff)
        self.assertFalse(s6_phx["feasible"])
        self.assertEqual(s6_phx["decision"], "NO_GO_NO_VIABLE_HEAT_OFFTAKER")

        # Distant offtaker (15 km away) must also be rejected
        far_site = copy.deepcopy(self.ash_site)
        far_site["heat_reuse_offtaker"]["distance_km"] = 15.0
        s6_far = evaluate_s6_heat_reuse_feasibility(far_site, self.ash_tariff)
        self.assertFalse(s6_far["feasible"])
        self.assertIn("NO_GO", s6_far["decision"])

        # Proximate Ashburn greenhouse/district heating offtaker (1.2 km, 4200 h/yr) passes
        s6_ash = evaluate_s6_heat_reuse_feasibility(self.ash_site, self.ash_tariff)
        self.assertTrue(s6_ash["feasible"])
        self.assertEqual(s6_ash["decision"], "GO_VIABLE_PROXIMATE_HEAT_REUSE")

    # 8. Capital cost outweighs resource savings at supplied tariff
    def test_08_capital_cost_outweighs_resource_savings_at_low_tariff(self) -> None:
        cheap_water_tariff = copy.deepcopy(self.ash_tariff)
        cheap_water_tariff["potable_water_usd_per_m3"] = 0.25
        cheap_water_tariff["wastewater_discharge_usd_per_m3"] = 0.25
        s2 = evaluate_s2_weather_constrained_dispatch(self.ash_site, self.ash_weather, cheap_water_tariff, max_safe_coc=6.0)
        by_id = {p["plant_id"]: p for p in s2["evaluated_plants"]}
        # $950k full dry + chiller retrofit (P4) costs far more per year than low-CapEx tower optimization (P1)
        self.assertGreater(
            by_id["P4_ZERO_EVAP_DRY_PLUS_CHILLER_RETROFIT"]["annualized_total_cooling_cost_usd"],
            by_id["P1_S1_TOWER_OPTIMIZER_ONLY"]["annualized_total_cooling_cost_usd"] + 80_000.0,
        )

    # 9. Ratepayer shifting hidden under an attractive jobs/tax number
    def test_09_ratepayer_shifting_exposed_in_s5_and_claims_engine(self) -> None:
        s5 = evaluate_s5_grid_and_community_cost_mitigation(
            self.phx_site, self.phx_tariff, peak_cooling_kw=1200.0, annual_cooling_kwh=4_800_000.0
        )
        allocs = {a["allocation_id"]: a for a in s5["cost_allocation_alternatives"]}
        # Conventional socialized upgrade (ALLOC_A) flags ratepayer shift and negative public NPV
        self.assertTrue(allocs["ALLOC_A_CONVENTIONAL_SOCIALIZED_TARIFF_AND_ABATEMENT"]["ratepayer_shift_warning"])
        self.assertLess(
            allocs["ALLOC_A_CONVENTIONAL_SOCIALIZED_TARIFF_AND_ABATEMENT"]["net_public_tax_and_infrastructure_npv_usd"],
            0.0,
        )
        # Developer CIAC + 85% take-or-pay (ALLOC_B and ALLOC_C) reduces ratepayer stranded exposure to $0
        self.assertEqual(
            allocs["ALLOC_B_DEVELOPER_CIAC_AND_85PCT_TAKE_OR_PAY"]["ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd"],
            0.0,
        )
        self.assertEqual(
            allocs["ALLOC_C_THERMAL_STORAGE_PEAK_SHAVE_PLUS_TAKE_OR_PAY"]["ratepayer_stranded_cost_if_50pct_underramp_or_yr6_exit_usd"],
            0.0,
        )

        # Also test public claims filing evaluator
        claims_filing = json.loads((ROOT / "data/public_claims_filing_sample.json").read_text(encoding="utf-8"))
        c_res = evaluate_public_benefit_claims(claims_filing)
        self.assertTrue(c_res["cost_incidence_summary"]["ratepayer_burden_alert"])
        self.assertGreater(c_res["unsupported_shortfall_or_overdue_count"], 0)

    # 10. Missing price/weather/chemistry triggers qualified result or abstention
    def test_10_missing_chemistry_or_tariff_triggers_abstention_or_error(self) -> None:
        no_chem_site = copy.deepcopy(self.phx_site)
        del no_chem_site["water_chemistry"]["silica_ppm"]
        s1 = evaluate_s1_chemistry_tower_optimizer(no_chem_site, self.phx_tariff, annual_wet_heat_kwh_th=87_600_000)
        self.assertEqual(s1["status"], "ABSTAIN_REQUIRED_MEASUREMENTS_MISSING")
        self.assertFalse(s1["feasible"])
        self.assertIn("silica_ppm", s1["required_measurements"])

        with tempfile.TemporaryDirectory() as d:
            bad_tariff = Path(d) / "bad_tariff.json"
            bad_tariff.write_text(json.dumps({"electricity_energy_usd_per_kwh": 0.08}), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "missing required tariff fields"):
                run_design_engine(
                    ROOT / "data/site_phoenix_arid.json",
                    ROOT / "data/weather_phoenix_sample.csv",
                    bad_tariff,
                )

    # 11. Prior 70% simulation credit rejected & Decision Recall reopens on source change
    def test_11_prior_70pct_claim_rejected_and_decision_recall_reopens(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d) / "design_out"
            res = run_design_engine(
                ROOT / "data/site_phoenix_arid.json",
                ROOT / "data/weather_phoenix_sample.csv",
                ROOT / "data/tariff_phoenix.json",
                telemetry_path=ROOT / "data/constructed_example.csv",
                output_dir=out_dir,
            )
            self.assertTrue(res["S7_verification_receipt"]["prior_70pct_sensor_claim_rejected"])
            for req_file in (
                "candidate_solutions.json",
                "ranked_pareto.csv",
                "engineering_report.md",
                "assumption_receipts.json",
                "equipment_boundary.md",
            ):
                self.assertTrue((out_dir / req_file).is_file(), f"Missing output file: {req_file}")

            # Verify Decision Recall triggers when rack thermal limit tightens or silica spikes
            tighter_site = copy.deepcopy(self.phx_site)
            tighter_site["rack_max_liquid_inlet_c"] = 32.0
            tighter_site["water_chemistry"]["silica_ppm"] = 45.0
            recall = check_decision_recall_triggers(res["S7_verification_receipt"], updated_site=tighter_site)
            self.assertTrue(recall["reopened"])
            self.assertEqual(recall["recall_status"], "REOPENED_BY_SOURCE_CHANGE")
            self.assertEqual(len(recall["reopened_reasons"]), 2)

    # 12. Independent transfer across climate/load profiles + Three Worked Concepts verification
    def test_12_cross_climate_transfer_and_worked_concepts(self) -> None:
        res_phx = run_design_engine(
            ROOT / "data/site_phoenix_arid.json",
            ROOT / "data/weather_phoenix_sample.csv",
            ROOT / "data/tariff_phoenix.json",
        )
        res_ash = run_design_engine(
            ROOT / "data/site_ashburn_humid.json",
            ROOT / "data/weather_ashburn_sample.csv",
            ROOT / "data/tariff_ashburn.json",
        )
        # Ashburn (softer water, 14 ppm silica) permits higher S1 CoC than Phoenix (28 ppm silica)
        coc_phx = res_phx["S1_chemistry_tower_optimizer"]["selected_regime"]["permissible_max_coc"]
        coc_ash = res_ash["S1_chemistry_tower_optimizer"]["selected_regime"]["permissible_max_coc"]
        self.assertGreater(coc_ash, coc_phx)

        concepts = generate_three_worked_engineering_concepts()
        self.assertEqual(len(concepts), 3)
        self.assertTrue(concepts[0]["physical_solution_built_first"])


if __name__ == "__main__":
    unittest.main()
