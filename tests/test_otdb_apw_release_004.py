#!/usr/bin/env python3
"""
OTDB-APW Release Repair 004 — Comprehensive Unit Test Suite (`tests/test_otdb_apw_release_004.py`).
Compatible with both standard `python3` and optimized `python3 -O` (uses `self.assertTrue` / `self.assertEqual`
rather than bare `assert` statements so `-O` never strips checks).
Eliminates the Rev C assertion that required a conventional baseline to score >80% error.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fair_baselines_and_synthetic_scenarios_004 import run_fair_baselines_and_synthetic_scenarios
from first_principles_physics_audit import run_first_principles_physics_attack
from kicad_rev_d_afe_and_strict_erc_004 import run_all_gate2_electrical_verifications
from repaired_physics_and_competitors import (
    RepairedBoundaryState,
    RepairedOTDBAPWPhysicsEngine,
)
from reproducible_sdi_and_worker_b_004 import (
    generate_foundry_and_manufacturability_report,
    run_reproducible_sdi_and_worker_b_004,
)
from verify_deterministic_outputs_004 import (
    audit_cleanroom_hygiene,
    verify_regenerated_outputs,
    verify_source_manifest,
)


class TestOTDBAPWRelease004(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root_dir = ROOT_DIR
        cls.artifacts_dir = cls.root_dir / "artifacts"
        cls.build_dir = cls.root_dir / "build_outputs"
        cls.build_dir.mkdir(parents=True, exist_ok=True)

    def test_01_first_principles_and_schur_fim_identifiability(self) -> None:
        audit = run_first_principles_physics_attack()
        self.assertEqual(len(audit["discovered_flaws_and_corrections"]), 8)
        eng = RepairedOTDBAPWPhysicsEngine()
        st = RepairedBoundaryState(5.0e-6, 0.25, 0.005, 1.5)
        wit = eng.compute_marginalized_fisher_witness(st)
        self.assertGreater(wit["schur_marginalized_fisher_min_eigenvalue"], 300.0)
        self.assertTrue(wit["identifiable_after_nuisance_marginalization"])

    def test_02_gate2_kicad_rev_d_typed_pins_split_regulators_and_strict_erc(self) -> None:
        res = run_all_gate2_electrical_verifications(self.build_dir, self.build_dir)
        sch = res["schematic_and_netlist"]
        self.assertEqual(sch["symbol_count"], 41)
        self.assertEqual(sch["bom_component_count"], 39)
        self.assertEqual(sch["library_pin_count"], 140)
        self.assertEqual(sch["placed_instance_pin_count"], 204)
        self.assertEqual(sch["wire_count"], 197)
        self.assertEqual(sch["no_connect_count"], 7)
        self.assertEqual(sch["electrical_net_count"], 52)

        pin_types = sch["library_pin_type_counts"]
        self.assertEqual(pin_types["power_in"], 38)
        self.assertEqual(pin_types["power_out"], 5)
        self.assertEqual(pin_types["input"], 35)
        self.assertEqual(pin_types["output"], 22)
        self.assertEqual(pin_types["passive"], 26)
        self.assertEqual(pin_types["no_connect"], 7)
        self.assertEqual(pin_types["bidirectional"], 7)

        erc = res["strict_typed_erc"]
        self.assertTrue(erc["erc_passed"])
        self.assertEqual(erc["erc_error_count"], 0)
        self.assertTrue(res["negative_erc_fault_injection"]["all_negative_erc_controls_passed"])
        self.assertTrue(res["power_and_signal_path"]["power_rails"]["adp7182_vin_within_spec_below_minus_2p7v"])
        self.assertTrue(res["power_and_signal_path"]["signal_path"]["zero_saturation_verified"])

    def test_03_gate3_gate4_fair_calibrated_baselines_and_negative_controls(self) -> None:
        res = run_fair_baselines_and_synthetic_scenarios(self.build_dir, self.build_dir)
        contract = res["frozen_benchmark_contract"]
        self.assertEqual(contract["raw_beamline_files_ingested"], 0)
        self.assertEqual(contract["wafers_fabricated"], 0)
        self.assertEqual(contract["wet_lab_hours"], 0)

        s1 = res["scenarios"]["S1_KHAJA_2026_INSPIRED_CONSTANT_EC_PARTICULATE"]
        # In S1 (Constant-EC Particulate without soluble CP), calibrated conventional baselines B2/B3 win or tie!
        self.assertLess(s1["b3_matched_budget_multisensor_fusion"]["mean_pct"], s1["otdb_apw_rev_d"]["mean_pct"])
        self.assertLess(s1["b1_calibrated_4freq_eis_drt_pt1000"]["mean_pct"], 25.0)

        s2 = res["scenarios"]["S2_LBNL_INSPIRED_SYNTHETIC_SCALING_WITH_SOLUBLE_CP"]
        # In S2 (Synthetic scaling under unmeasured 1.35x-2.15x soluble CP), OTDB-APW Rev D outperforms
        self.assertLess(s2["otdb_apw_rev_d"]["mean_pct"], 12.0)
        self.assertLess(
            s2["otdb_apw_rev_d"]["mean_pct"],
            s2["b3_matched_budget_multisensor_fusion"]["mean_pct"],
        )

        # In NC5 (Fouled Reference Arm), conventional B3 multi-sensor fusion wins over OTDB-APW!
        nc5 = res["negative_controls_and_loss_regimes"]["NC5_FOULED_REFERENCE_ARM_ASYMMETRIC_SHEAR"]
        self.assertLess(nc5["b3_multisensor_fusion_mean_error_pct"], nc5["otdb_apw_mean_error_pct_if_forced"])

    def test_04_reproducible_sdi_c99_firmware_and_worker_b_inheritance(self) -> None:
        fab = generate_foundry_and_manufacturability_report(self.build_dir, self.build_dir)
        self.assertTrue(fab["mems_geometric_drc_passed"])
        self.assertTrue(fab["peek_stl_watertight"])
        self.assertEqual(len(fab["declared_process_holds"]), 6)

        res = run_reproducible_sdi_and_worker_b_004(self.root_dir, self.build_dir, self.build_dir)
        sdi = res["sdi_report"]
        self.assertTrue(sdi["negative_control_420um_cake_demonstration"]["otdb_apw_abstained"])
        self.assertLess(
            sdi["negative_control_420um_cake_demonstration"]["conventional_delta_p_rel_error_pct"],
            5.0,
        )
        wb = res["worker_b_report"]
        self.assertTrue(wb["all_inheritance_and_boundary_checks_passed"])

    def test_05_gate5_cleanroom_hygiene_license_and_zero_control_chars(self) -> None:
        hyg = audit_cleanroom_hygiene(self.root_dir)
        self.assertTrue(hyg["cleanroom_hygiene_passed"], msg=f"Hygiene violations: {hyg['violations']}")
        self.assertLessEqual(hyg["abstract_word_count"], 200)
        self.assertGreaterEqual(hyg["abstract_word_count"], 80)

    def test_06_immutable_source_manifest_and_deterministic_outputs(self) -> None:
        src_check = verify_source_manifest(self.root_dir, "SHA256SUMS_SOURCE.txt")
        self.assertTrue(src_check["passed"], msg=f"Source manifest mismatches: {src_check['mismatches']}")
        out_check = verify_regenerated_outputs(self.root_dir)
        self.assertTrue(out_check["all_within_tolerance"], msg=f"Output diffs: {out_check['tolerance_diffs']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
