"""Publication boundary checks; these are not physical tests."""
import pathlib,subprocess,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class PublicationBounds(unittest.TestCase):
    def test_math_counterexamples_executable(self):
        p=subprocess.run([sys.executable,str(ROOT/'models/observability_certificate.py')],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('3 arms conditional',p.stdout)
    def test_scope_and_holds_are_explicit(self):
        b=(ROOT/'README.md').read_text()
        self.assertIn('No manufactured sensor',b)
        self.assertIn('NOT', (ROOT/'design/THREE_ARM_INTERFACE.md').read_text())
        self.assertIn('unregistered', (ROOT/'design/LAB_HANDOFF.md').read_text().lower())
    def test_hardware_gate_remains_hold(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/hardware_hold.py')],capture_output=True,text=True,check=True)
        self.assertIn('"hardware_disposition": "HOLD"',p.stdout)
if __name__=='__main__':unittest.main()
