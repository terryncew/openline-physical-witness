import json, tempfile, unittest, math
from pathlib import Path
from water_audit import audit,evaluate_scenario,EvidenceError
ROOT=Path(__file__).parents[1]
class AuditTests(unittest.TestCase):
    def test_observed_audit_uses_metered_makeup(self):
        r=audit(ROOT/'data/constructed_example.csv')
        self.assertEqual(r['rows'],3);self.assertEqual(r['site_makeup_l'],4300)
        self.assertAlmostEqual(r['site_wue_makeup_l_per_it_kwh'],4300/3000,places=6)
        self.assertIsNone(r['source_electricity_water_l_scenario'])
        self.assertIn('NOT_VALIDATED_SAVINGS',r['status'])
    def test_grid_contribution_includes_it(self):
        r=audit(ROOT/'data/constructed_example.csv',1.5)
        self.assertEqual(r['source_electricity_water_l_scenario'],(3000+269)*1.5)
    def test_overlapping_intervals_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv'
            p.write_text('timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n2026-01-01T00:00:00Z,1,1000,10,5,1\n2026-01-01T00:30:00Z,1,1000,10,5,1\n')
            with self.assertRaisesRegex(EvidenceError,'overlapping metering intervals'):audit(p)
    def test_missing_data_gap_is_visible(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'gap.csv'
            p.write_text('timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n2026-01-01T00:00:00Z,1,1000,10,5,1\n2026-01-01T03:00:00Z,1,1000,10,5,1\n')
            self.assertEqual(audit(p)['uncovered_gap_hours_between_rows'],2)
    def test_bad_meter_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text('timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n2026-01-01T00:00:00Z,1,1000,10,1,2\n')
            with self.assertRaisesRegex(EvidenceError,'blowdown exceeds'):audit(p)
    def test_missing_columns_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text('timestamp_utc,it_kw\n2026-01-01T00:00:00Z,1000\n')
            with self.assertRaisesRegex(EvidenceError,'missing required columns'):audit(p)
    def test_duplicate_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';head='timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n'; row='2026-01-01T00:00:00Z,1,1000,10,5,1\n';p.write_text(head+row+row)
            with self.assertRaisesRegex(EvidenceError,'non-increasing'):audit(p)
    def test_nan_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text('timestamp_utc,duration_h,it_kw,cooling_kw,makeup_l,blowdown_l\n2026-01-01T00:00:00Z,1,NaN,10,5,1\n')
            with self.assertRaisesRegex(EvidenceError,'nonnegative finite'):audit(p)
    def test_matched_physics_zero_water_delta(self):
        o=json.loads((ROOT/'data/constructed_scenarios.json').read_text());o['candidate']=dict(o['baseline'])
        r=evaluate_scenario(o);self.assertEqual(r['site_makeup_delta_l_model'],0);self.assertTrue(r['same_heat_rejection_physics'])
    def test_dry_cooling_benefit_is_not_sensing_win(self):
        r=evaluate_scenario(json.loads((ROOT/'data/constructed_scenarios.json').read_text()))
        self.assertGreater(r['site_makeup_delta_l_model'],0)
        self.assertFalse(r['openline_attributable_water_savings_proven'])
        self.assertFalse(r['same_heat_rejection_physics'])
    def test_infeasible_coc_rejected(self):
        o=json.loads((ROOT/'data/constructed_scenarios.json').read_text());o['candidate']['cycles_of_concentration']=1
        with self.assertRaisesRegex(EvidenceError,'CoC'):evaluate_scenario(o)
    def test_negative_grid_impact_possible(self):
        o=json.loads((ROOT/'data/constructed_scenarios.json').read_text());o['shared']['grid_l_per_kwh']=100
        o['candidate']['cooling_elec_kw']=1000
        r=evaluate_scenario(o)
        self.assertGreater(r['site_makeup_delta_l_model'],0)
        self.assertLess(r['source_water_delta_l_model'],0)
if __name__=='__main__':unittest.main()
