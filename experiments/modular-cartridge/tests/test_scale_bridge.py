import unittest,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(BASE/'cad'),str(BASE/'cost')]
from cartridge_geometry import Cartridge,screen,svg_plan
from economics import Assumptions,threshold

class ScaleBoundaries(unittest.TestCase):
    def test_nominal_compression_envelope(self):
        v=screen(Cartridge());self.assertTrue(v['geometry_screen_pass'])
        self.assertGreaterEqual(v['gasket_crush_fraction_min'],0.15)
        self.assertLessEqual(v['gasket_crush_fraction_max'],0.35)
    def test_thinner_stop_fails(self):
        p=Cartridge(hard_stop_nominal_mm=0.5)
        self.assertFalse(screen(p)['geometry_screen_pass'])
    def test_channels_too_close_fails(self):
        p=Cartridge(channel_pitch_mm=11.0,channels=(-11.,0.,11.))
        self.assertFalse(screen(p)['geometry_screen_pass'])
    def test_cookie_cutter_svg_contains_all_three(self):
        s=svg_plan(Cartridge())
        for x in ('S — depositing','R — reference','G — guard'):
            self.assertIn(x,s)
    def test_cost_model_never_claims_unmeasured_roi(self):
        o=threshold(Assumptions())
        self.assertEqual(o['disposition'],'HOLD_NO_FIELD_ECONOMICS')
        self.assertGreater(o['annual_benefit_needed_for_target_margin_usd'],0)
    def test_cost_cannot_be_approved_by_fake_savings(self):
        o=threshold(Assumptions(measured_annual_benefit_usd=10000))
        self.assertEqual(o['disposition'],'HOLD_NO_FIELD_ECONOMICS')
    def test_cost_drops_with_longer_cartridge_life(self):
        short=threshold(Assumptions(cartridge_service_life_days=15))
        long=threshold(Assumptions(cartridge_service_life_days=90))
        self.assertGreater(short['annualized_incremental_cost_usd'],long['annualized_incremental_cost_usd'])
    def test_independent_geometry_proof_obligations(self):
        from dataclasses import replace
        nominal=Cartridge()
        mutants={
            "bolt outside plate":replace(nominal,bolt_locations=((60.,60.),)+nominal.bolt_locations[1:]),
            "alignment outside plate":replace(nominal,alignment_locations=((120.,120.),)+nominal.alignment_locations[1:]),
            "negative lid thickness":replace(nominal,lid_thickness_mm=-3),
            "zero coupon width":replace(nominal,coupon_width_mm=0),
            "zero channel length":replace(nominal,channel_length_mm=0),
            "channel outside gasket cavity":replace(nominal,channel_length_mm=80),
            "port larger than channel":replace(nominal,port_diameter_mm=9),
            "nonfinite tolerance":replace(nominal,stop_tol_mm=float('nan')),
        }
        for name,mutant in mutants.items():
            with self.subTest(name=name):
                self.assertFalse(screen(mutant)['geometry_screen_pass'])

    def test_malformed_inputs_fail_closed_without_crash_or_nan_receipts(self):
        from dataclasses import replace
        from json import dumps
        nominal=Cartridge()
        cases=[
            replace(nominal,gasket_nominal_mm=0),
            replace(nominal,channels=()),
            replace(nominal,bolt_locations=()),
            replace(nominal,gasket_nominal_mm=float('nan')),
            replace(nominal,outer_x_mm=-1),
            replace(nominal,channels=(-21.,float('inf'),21.)),
        ]
        for case in cases:
            with self.subTest(case=case):
                result=screen(case)
                self.assertFalse(result['geometry_screen_pass'])
                dumps(result,allow_nan=False)

    def test_refinement_corner_envelope(self):
        # Independent obligation under increasingly adverse gasket/stop tolerance.
        from dataclasses import replace
        p=Cartridge()
        for tol in (0.0,0.02,0.05):
            with self.subTest(tol=tol):
                q=screen(replace(p,gasket_tol_mm=tol,stop_tol_mm=tol))
                self.assertTrue(q['geometry_screen_pass'])
        self.assertFalse(screen(replace(p,gasket_tol_mm=0.20,stop_tol_mm=0.20))['geometry_screen_pass'])

    def test_no_negative_inputs(self):
        with self.assertRaises(ValueError):threshold(Assumptions(replaceable_cartridge_cost_usd=-1))

if __name__=='__main__':unittest.main()
