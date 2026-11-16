import json
import math
import tempfile
import unittest
from pathlib import Path

from water_audit import (
    EvidenceError,
    audit,
    evaluate_matched_plant_sensor_competition,
    evaluate_pre_hardware_sensor_matrix,
    evaluate_scenario,
    classify_static_mems_threshold,
)

ROOT = Path(__file__).parents[1]


class AuditTests(unittest.TestCase):
    # --- Original 12 PR #6 Tests (Preserved Unmodified) ---
    def test_observed_audit_uses_metered_makeup(self):
        r = audit(ROOT / "data/constructed_example.csv")
        self.assertEqual(r["rows"], 3)
        self.assertEqual(r["site_makeup_l"], 4300)
        self.assertAlmostEqual(r["site_wue_makeup_l_per_it_kwh"], 4300 / 3000, places=6)
        self.assertIsNone(r["source_electricity_water_l_scenario"])
        self.assertIn("NOT_VALIDATED_SAVINGS", r["status"])

    def test_grid_contribution_includes_it(self):
        r = audit(ROOT / "data/constructed_example.csv", 1.5)
        self.assertEqual(r["source_electricity_water_l_scenario"], (3000 + 269) * 1.5)

    def test_overlapping_intervals_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,1000,10,5,1\n"
                "2026-01-01T00:30:00Z,1,1000,10,5,1\n"
            )
            with self.assertRaisesRegex(EvidenceError, "overlapping metering intervals"):
                audit(p)

    def test_missing_data_gap_is_visible(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "gap.csv"
            p.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,1000,10,5,1\n"
                "2026-01-01T03:00:00Z,1,1000,10,5,1\n"
            )
            self.assertEqual(audit(p)["uncovered_gap_hours_between_rows"], 2)

    def test_bad_meter_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,1000,10,1,2\n"
            )
            with self.assertRaisesRegex(EvidenceError, "blowdown exceeds"):
                audit(p)

    def test_missing_columns_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("timestamp_utc,it_kw\n2026-01-01T00:00:00Z,1000\n")
            with self.assertRaisesRegex(EvidenceError, "missing required columns"):
                audit(p)

    def test_duplicate_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            head = "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
            row = "2026-01-01T00:00:00Z,1,1000,10,5,1\n"
            p.write_text(head + row + row)
            with self.assertRaisesRegex(EvidenceError, "non-increasing"):
                audit(p)

    def test_nan_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,NaN,10,5,1\n"
            )
            with self.assertRaisesRegex(EvidenceError, "nonnegative finite"):
                audit(p)

    def test_matched_physics_zero_water_delta(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["candidate"] = dict(o["baseline"])
        r = evaluate_scenario(o)
        self.assertEqual(r["site_makeup_delta_l_model"], 0)
        self.assertTrue(r["same_heat_rejection_physics"])

    def test_dry_cooling_benefit_is_not_sensing_win(self):
        r = evaluate_scenario(json.loads((ROOT / "data/constructed_scenarios.json").read_text()))
        self.assertGreater(r["site_makeup_delta_l_model"], 0)
        self.assertFalse(r["openline_attributable_water_savings_proven"])
        self.assertFalse(r["same_heat_rejection_physics"])

    def test_infeasible_coc_rejected(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["candidate"]["cycles_of_concentration"] = 1
        with self.assertRaisesRegex(EvidenceError, "CoC"):
            evaluate_scenario(o)

    def test_negative_grid_impact_possible(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["shared"]["grid_l_per_kwh"] = 100
        o["candidate"]["cooling_elec_kw"] = 1000
        r = evaluate_scenario(o)
        self.assertGreater(r["site_makeup_delta_l_model"], 0)
        self.assertLess(r["source_water_delta_l_model"], 0)

    # --- 16 New Red-to-Green Tests (Sensors 003 Falsifiers, User CSV Adapter & Competition) ---
    def test_boolean_inputs_rejected_in_scenario_and_audit(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["shared"]["hours"] = True
        with self.assertRaisesRegex(EvidenceError, "boolean"):
            evaluate_scenario(o)
        with self.assertRaisesRegex(EvidenceError, "grid water intensity"):
            audit(ROOT / "data/constructed_example.csv", True)

    def test_ragged_csv_extra_or_missing_columns_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p_extra = Path(d) / "extra.csv"
            p_extra.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,1000,85,1580,330,EXTRA_UNQUOTED\n"
            )
            with self.assertRaisesRegex(EvidenceError, "ragged CSV row"):
                audit(p_extra)

            p_short = Path(d) / "short.csv"
            p_short.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,1000,85,1580\n"
            )
            with self.assertRaisesRegex(EvidenceError, "ragged CSV row"):
                audit(p_short)

    def test_csv_formula_injection_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "inj.csv"
            p.write_text(
                "timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n"
                "2026-01-01T00:00:00Z,1,=1000+1,85,1580,330\n"
            )
            with self.assertRaisesRegex(EvidenceError, "invalid it_kw"):
                audit(p)

    def test_unphysical_thermodynamic_evaporation_coefficient_rejected(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["baseline"]["evap_l_per_kwh_rejected"] = 500.0
        with self.assertRaisesRegex(EvidenceError, "thermodynamic range"):
            evaluate_scenario(o)

    def test_drift_displaces_blowdown_and_rejects_infeasible_drift(self):
        o = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        o["candidate"]["drift_l_per_kwh_rejected"] = 0.05
        r = evaluate_scenario(o)
        # Drift leaves at circulating concentration, reducing required blowdown while keeping makeup constant
        self.assertGreater(r["candidate"]["drift_l_model"], 0)
        self.assertEqual(r["candidate"]["site_makeup_l_model"], 7154000.0)
        self.assertLess(r["candidate"]["blowdown_l_model"], 1022000.0)

        o["candidate"]["drift_l_per_kwh_rejected"] = 0.50  # Exceeds E/(CoC-1) at CoC=7
        with self.assertRaisesRegex(EvidenceError, "infeasible drift"):
            evaluate_scenario(o)

    def test_orthogonal_attribution_decomposition_sums_to_total_delta(self):
        r = evaluate_scenario(json.loads((ROOT / "data/constructed_scenarios.json").read_text()))
        attr = r["attribution_decomposition_l_model"]
        total_attrib = (
            attr["dry_cooling_plant_attributed_delta_l"]
            + attr["coc_chemistry_attributed_delta_l"]
            + attr["evap_coeff_attributed_delta_l"]
            + attr["sensor_only_attributable_delta_l"]
        )
        self.assertAlmostEqual(total_attrib, r["site_makeup_delta_l_model"], places=3)
        self.assertEqual(attr["sensor_only_attributable_delta_l"], 0.0)
        self.assertGreater(attr["dry_cooling_plant_attributed_delta_l"], attr["coc_chemistry_attributed_delta_l"])

    def test_user_csv_adapter_units_reclaimed_and_anomaly_flags(self):
        r = audit(
            ROOT / "data/newcomer_utility_export_gal.csv",
            1.65,
            column_map={
                "timestamp_utc": "interval_start_utc",
                "duration_h": "hours",
                "it_kw": "it_load_mw",
                "cooling_kw": "cooling_load_mw",
                "makeup_l": "tower_makeup_gal",
                "blowdown_l": "tower_blowdown_gal",
                "reclaimed_l": "reclaimed_makeup_gal",
            },
            water_unit="gal",
            power_unit="mw",
            grid_intensity_range=(0.18, 1.65, 2.40),
        )
        self.assertEqual(r["rows"], 3)
        self.assertGreater(r["reclaimed_makeup_l"], 0.0)
        self.assertGreater(r["potable_makeup_l"], 0.0)
        self.assertEqual(r["covered_window_end_utc"], "2026-02-01T03:00:00+00:00")
        # Row 3 in newcomer_utility_export_gal.csv has an intentional basin leak / thermodynamic ceiling exceedance
        self.assertGreaterEqual(r["physics_anomaly_count"], 1)
        self.assertEqual(r["physics_anomalies"][0]["code"], "THERMODYNAMIC_EVAP_CEILING_EXCEEDED")
        self.assertIn("source_electricity_water_uncertainty_band_l", r)

    def test_matched_plant_competition_incumbent_ties_outside_collinear_regime(self):
        comp = evaluate_matched_plant_sensor_competition()
        self.assertEqual(comp["status"], "COMPUTATIONAL_CONTROLLED_SCENARIO_UNVALIDATED_IN_FIELD")
        self.assertTrue(comp["plant_hardware_held_identical"])
        # Prove strong passive FDD ties active ABA on >=98% of non-collinear trials
        self.assertGreaterEqual(comp["incumbent_b_ties_candidate_c_on_non_collinear_regimes_pct"], 98.0)
        res = comp["results_by_strategy"]
        self.assertGreater(
            res["Candidate_C_Guarded_Active_ABA_Perturbation"]["collinear_confounder_recall_pct"],
            res["Incumbent_B_Competent_Passive_Energy_Balance_FDD"]["collinear_confounder_recall_pct"] + 70.0,
        )

    # GPT-6 independent adversarial release probes: discovered against RC 0.2.
    def test_evaporation_coefficient_over_physical_ceiling_rejected(self):
        obj = json.loads((ROOT / "data/constructed_scenarios.json").read_text())
        obj["candidate"]["evap_l_per_kwh_rejected"] = 2.30
        with self.assertRaisesRegex(EvidenceError, "thermodynamic range"):
            evaluate_scenario(obj)
        # Finite constructed evaporation below the generous 1.55 L/kWh ceiling is allowed.
        obj["candidate"]["evap_l_per_kwh_rejected"] = 1.50
        self.assertTrue(evaluate_scenario(obj)["openline_attributable_water_savings_proven"] is False)

    def test_static_comparator_never_receives_fault_or_oracle_label(self):
        # Comparator contract has two observed measurements only; the evaluator
        # cannot supply hidden 'reg' or 'fouled' ground truth to the decision.
        self.assertEqual(classify_static_mems_threshold(4.38, 3.0), "normal_clean")
        self.assertEqual(classify_static_mems_threshold(4.70, 3.0), "physical_fouling_only")
        with self.assertRaises(TypeError):
            classify_static_mems_threshold(4.70, 3.0, "physical_fouling_only")

    def test_pre_hardware_matrix_marks_unvalidated_hardware_not_ready(self):
        mat = evaluate_pre_hardware_sensor_matrix()
        by_id = {m["option_id"]: m for m in mat}
        self.assertEqual(by_id["OPT_4_CUSTOM_3OMEGA_EIS_CARTRIDGE"]["verdict"], "REJECT_CAPITAL_EXPENDITURE")
        self.assertIn("NOT_READY", by_id["OPT_1_COTS_PT100_DP_EC_BENCH_KIT"]["readiness_status"])


if __name__ == "__main__":
    unittest.main()
