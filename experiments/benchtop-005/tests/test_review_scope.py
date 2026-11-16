import json
import pathlib
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ReviewScope(unittest.TestCase):
    def test_bom_is_not_a_quotation(self):
        bom=json.loads((ROOT/'data/BOM_MODEL_ONLY_005.json').read_text())
        self.assertIsNone(bom['under_300_usd_feasible'])
        self.assertIsNone(bom['cost_summary_usd']['total_complete_rig_option_b_micrux_glass_ide_usd'])
        self.assertIn('NOT VERIFIED',bom['commercial_micrux_upgrade_option_b']['price_status'])
    def test_model_replays_exact_source_values(self):
        recorded=json.loads((ROOT/'data/SNR_MODEL_ONLY_005.json').read_text())
        p=subprocess.run([sys.executable,str(ROOT/'models/reproduce_snr_model.py')],capture_output=True,text=True,check=True)
        generated=json.loads(p.stdout)
        recorded.pop('model_only_not_measured')
        recorded.pop('data_qualification')
        self.assertEqual(generated,recorded)
    def test_hardware_claims_are_held(self):
        text=(ROOT/'VALIDATION_HOLDS.md').read_text()
        for requirement in ['NOT BUILD-READY','Native CAD','No fabrication','partial reference fouling']:
            self.assertIn(requirement,text)

if __name__=='__main__':unittest.main()
