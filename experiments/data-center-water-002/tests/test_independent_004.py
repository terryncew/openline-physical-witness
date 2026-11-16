"""Independent defects found during the GPT-6 verification of Sensors 004.
These are source-integrity tests, not field evidence or engineering certification.
"""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from solutions import (load_weather_csv,evaluate_s1_chemistry_tower_optimizer,
                       evaluate_s5_grid_and_community_cost_mitigation,
                       evaluate_public_benefit_claims)
from water_audit import EvidenceError
ROOT=Path(__file__).resolve().parents[1]

class Independent004Tests(unittest.TestCase):
    def setUp(self):
        self.site=json.loads((ROOT/'data/site_phoenix_arid.json').read_text())
        self.tariff=json.loads((ROOT/'data/tariff_phoenix.json').read_text())

    def test_overlap_weather_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'weather.csv'
            p.write_text('timestamp_utc,duration_h,dry_bulb_c,wet_bulb_c,source_station\n'
                         '2026-01-01T00:00:00Z,1800,40,23,CONSTRUCTED\n'
                         '2026-03-16T00:00:00Z,2400,33,19,CONSTRUCTED\n')
            with self.assertRaisesRegex(EvidenceError,'overlapping weather'):
                load_weather_csv(p)

    def test_example_weather_explicitly_constructed(self):
        for name in ('phoenix','ashburn'):
            w=load_weather_csv(ROOT/'data'/f'weather_{name}_sample.csv')
            self.assertEqual(w['weather_evidence_class'],'CONSTRUCTED_WEIGHTED_SEASONAL_BINS_NOT_HOURLY_OBSERVATIONS')
            self.assertEqual(w['total_hours'],8760)

    def test_high_silica_never_approves_coc_above_chemistry_ceiling(self):
        site=copy.deepcopy(self.site)
        site['water_chemistry']['silica_ppm']=200.0
        result=evaluate_s1_chemistry_tower_optimizer(site,self.tariff,87600000.)
        self.assertFalse(result['feasible'])
        self.assertEqual(result['status'],'ABSTAIN_NO_VALID_CHEMISTRY_SETPOINT')

    def test_thermal_storage_peak_shave_requires_dispatch_evidence(self):
        site=copy.deepcopy(self.site)
        site['has_existing_thermal_storage']=False
        result=evaluate_s5_grid_and_community_cost_mitigation(site,self.tariff,1200.,4800000.)
        self.assertEqual(result['tes_cooling_peak_shaved_kw'],0.)
        self.assertFalse(result['tes_dispatch_qualified'])
        self.assertEqual(result['tes_proposed_peak_shave_kw_not_dispatch_proven'],420.)
        site.update(declared_verified_tes_usable_capacity_kwh_th=400.,
                    declared_verified_offpeak_charge_headroom_kw=100.,
                    tes_dispatch_proven_feasible_for_climate=True)
        r2=evaluate_s5_grid_and_community_cost_mitigation(site,self.tariff,1200.,4800000.)
        self.assertEqual(r2['tes_cooling_peak_shaved_kw'],100.)

    def test_reported_numbers_do_not_become_verified_just_by_input(self):
        filing={'project_id':'constructed','promised_claims':{'permanent_full_time_jobs':50},
                'documented_disclosures':{'permanent_full_time_jobs':55},
                'source_citations':[]}
        got=evaluate_public_benefit_claims(filing)
        vals=[m['disposition'] for m in got['metric_comparisons'] if m['metric']=='permanent_full_time_jobs']
        self.assertEqual(vals,['REPORTED_MET_OR_EXCEEDED_NOT_ATTESTED'])
        self.assertIn('unverified input assertions',got['evidence_boundary'])

if __name__=='__main__':unittest.main()

class CredibilityAdversaries(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        self.site=json.loads((self.root/'data/site_phoenix_arid.json').read_text())
        self.tariff=json.loads((self.root/'data/tariff_phoenix.json').read_text())

    def test_unapproved_sewer_deduction_not_credited_as_savings(self):
        from solutions import evaluate_s1_chemistry_tower_optimizer
        original=evaluate_s1_chemistry_tower_optimizer(self.site,self.tariff,87600000.)
        self.assertTrue(original['feasible'])
        self.assertEqual(original['sewer_credit_eligibility'],'NO_SEWER_DEDUCT_CREDIT_ASSUMED')
        for op in original['pareto_chemistry_regimes']:
            self.assertEqual(op['sewer_deduct_status'],'NOT_CREDITED_PENDING_UTILITY_ELIGIBILITY')
        approved=copy.deepcopy(self.site)
        approved['municipal_evaporative_sewer_credit_approved']=True
        other=evaluate_s1_chemistry_tower_optimizer(approved,self.tariff,87600000.)
        byid={v['regime_id']:v for v in other['pareto_chemistry_regimes']}
        for op in original['pareto_chemistry_regimes']:
            self.assertGreater(byid[op['regime_id']]['annual_net_operating_savings_usd'],op['annual_net_operating_savings_usd'])

    def test_W40_rack_upgrade_not_given_free_approval_or_cost_rank(self):
        from solutions import evaluate_s2_weather_constrained_dispatch,load_weather_csv
        weather=load_weather_csv(self.root/'data/weather_phoenix_sample.csv')
        vals=evaluate_s2_weather_constrained_dispatch(self.site,weather,self.tariff,3.5)
        byid={v['plant_id']:v for v in vals['evaluated_plants']}
        w40=byid['P3_WARM_WATER_W40_HYBRID_DRY_WET']
        self.assertTrue(w40['requires_new_warm_water_racks'])
        self.assertFalse(w40['rack_upgrade_capex_included'])
        self.assertFalse(w40['pareto_optimal'])
        self.assertNotIn('P3_WARM_WATER_W40_HYBRID_DRY_WET',vals['pareto_frontier_plant_ids'])

    def test_change_to_other_site_parameter_invalidates_receipt(self):
        from solutions import run_design_engine,check_decision_recall_triggers
        r=run_design_engine(self.root/'data/site_phoenix_arid.json',
                            self.root/'data/weather_phoenix_sample.csv',
                            self.root/'data/tariff_phoenix.json')
        rec=r['S7_verification_receipt']
        self.assertFalse(check_decision_recall_triggers(rec,updated_site=self.site)['reopened'])
        changed=copy.deepcopy(self.site);changed['has_existing_dry_cooler']=True
        self.assertTrue(check_decision_recall_triggers(rec,updated_site=changed)['reopened'])
        self.assertTrue(check_decision_recall_triggers(rec,updated_tariff=self.tariff)['reopened'] is False)
        nt=copy.deepcopy(self.tariff);nt['electricity_energy_usd_per_kwh']=0.12
        self.assertTrue(check_decision_recall_triggers(rec,updated_tariff=nt)['reopened'])
        self.assertEqual(rec['receipt_authority'],'CONTENT_HASH_ONLY_NOT_SIGNED_NOT_RECEIVER_AUTHORIZED')

    def test_missing_disclosures_do_not_become_zero_or_promised_benefits(self):
        from solutions import evaluate_public_benefit_claims
        f={'promised_claims':{'annual_local_tax_revenue_usd':1_000_000.,'annual_public_subsidy_or_abatement_usd':100_000.,'ratepayer_funded_infrastructure_share_usd':5_000_000.,'permanent_full_time_jobs':50},'documented_disclosures':{}}
        r=evaluate_public_benefit_claims(f)
        self.assertIsNone(r['cost_incidence_summary']['annual_net_local_tax_after_subsidy_usd'])
        self.assertEqual(r['cost_incidence_summary']['incidence_status'],'INCOMPLETE_DISCLOSURE_NO_INFERENCE')
        f['documented_disclosures']={'annual_local_tax_revenue_usd':0.,'annual_public_subsidy_or_abatement_usd':0.,'ratepayer_funded_infrastructure_share_usd':0.,'permanent_full_time_jobs':1.}
        r=evaluate_public_benefit_claims(f)
        self.assertEqual(r['cost_incidence_summary']['annual_net_local_tax_after_subsidy_usd'],0.)
        self.assertEqual(r['cost_incidence_summary']['ratepayer_funded_grid_or_water_infra_usd'],0.)

    def test_unsigned_take_or_pay_not_a_protected_ratepayer_outcome(self):
        from solutions import evaluate_s5_grid_and_community_cost_mitigation
        r=evaluate_s5_grid_and_community_cost_mitigation(self.site,self.tariff,1000.,4e6)
        for item in r['cost_allocation_alternatives'][1:]:
            self.assertFalse(item['actual_ratepayer_protection_verified'])
            self.assertTrue(item['ratepayer_shift_warning'])
            self.assertIn('SCENARIO_ONLY',item['projected_zero_stranded_risk_condition'])
        self.assertIn('No chronological storage charge',r['dispatch_evidence_boundary'])

    def test_missing_public_economic_cost_parameters_fail_closed(self):
        from solutions import evaluate_s5_grid_and_community_cost_mitigation
        bad=copy.deepcopy(self.tariff)
        del bad['declared_grid_substation_upgrade_cost_usd']
        with self.assertRaisesRegex(EvidenceError,'invalid grid_upgrade_capex'):
            evaluate_s5_grid_and_community_cost_mitigation(self.site,bad,1000.,4e6)

    def test_unverified_sla_flex_gets_no_effective_peak_reduction(self):
        from solutions import evaluate_s5_grid_and_community_cost_mitigation
        s=copy.deepcopy(self.site)
        s['declared_movable_it_sla_fraction']=0.20
        r=evaluate_s5_grid_and_community_cost_mitigation(s,self.tariff,1000.,4e6)
        self.assertEqual(r['declared_movable_it_peak_shaved_kw'],0.)
        self.assertEqual(r['movable_it_peak_shave_proposed_not_dispatch_proven_kw'],2000.)

class FinalFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        self.site=json.loads((self.root/'data/site_phoenix_arid.json').read_text())
        self.tariff=json.loads((self.root/'data/tariff_phoenix.json').read_text())

    def test_missing_chemistry_wet_options_abstain_dry_option_remains(self):
        from solutions import run_design_engine
        s=copy.deepcopy(self.site)
        s.pop('water_chemistry')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'site.json';p.write_text(json.dumps(s))
            r=run_design_engine(p,self.root/'data/weather_phoenix_sample.csv',self.root/'data/tariff_phoenix.json')
        self.assertFalse(r['S1_chemistry_tower_optimizer']['feasible'])
        vals=r['S2_weather_constrained_dispatch']['evaluated_plants']
        self.assertTrue(all(not x['feasible'] for x in vals[:4]))
        self.assertTrue(vals[4]['feasible'])
        self.assertEqual(vals[4]['site_makeup_l'],0.)

    def test_false_string_cannot_claim_valid_treatment_approval(self):
        from solutions import evaluate_s1_chemistry_tower_optimizer
        s=copy.deepcopy(self.site)
        s['municipal_evaporative_sewer_credit_approved']='false'
        with self.assertRaisesRegex(EvidenceError,'JSON boolean'):
            evaluate_s1_chemistry_tower_optimizer(s,self.tariff,87600000.)

    def test_false_string_cannot_claim_verified_financial_guarantee(self):
        from solutions import evaluate_s5_grid_and_community_cost_mitigation
        s=copy.deepcopy(self.site)
        s['signed_collateralized_take_or_pay_contract_verified']='false'
        with self.assertRaisesRegex(EvidenceError,'JSON boolean'):
            evaluate_s5_grid_and_community_cost_mitigation(s,self.tariff,1000.,4e6)
