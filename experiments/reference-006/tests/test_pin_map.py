import csv
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ManufacturerPinMap(unittest.TestCase):
  def test_48_pin_map_and_critical_spi_electrodes(self):
    with (ROOT/'design/AD5941_48_PIN_REVIEW_MAP.csv').open() as f:
      rows=list(csv.DictReader(f))
    self.assertEqual(len(rows),48)
    mp={int(x['pin_number']):x['manufacturer_mnemonic'] for x in rows}
    self.assertEqual(set(mp),set(range(1,49)))
    for pin,name in {7:'DNC',10:'DNC',24:'DNC',13:'DGND',15:'CS',16:'SCLK',17:'MOSI',18:'MISO',26:'IOVDD',30:'AVDD',37:'AIN2',38:'AIN1',39:'AIN0',43:'VREF_1V82',44:'AGND_REF',45:'SE0',46:'DE0',47:'CE0',48:'RE0'}.items():
      self.assertEqual(mp[pin],name)
  def test_exposed_pad_is_outside_48_lead_map(self):
    t=(ROOT/'design/THREE_ARM_INTERFACE.md').read_text().lower()
    self.assertIn('exposed pad',t)
if __name__=='__main__':unittest.main()
