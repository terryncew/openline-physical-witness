import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_readiness import check

class HardwareReadiness(unittest.TestCase):
 def test_false_build_ready_blocked(self):
  report=check()
  self.assertEqual(report['disposition'],'HOLD')
  self.assertLess(report['ad5941_symbol_unique_pin_count'],48)
  self.assertGreaterEqual(len(report['issues']),4)
 def test_hardware_raw_evidence_absent(self):
  self.assertFalse((ROOT/'artifacts/physical_raw_data.csv').exists())
  self.assertFalse(any(ROOT.rglob('*.kicad_pcb')))
