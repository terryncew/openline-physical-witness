"""Cost threshold calculator. Assumptions are inputs, NOT vendor quotes or savings.
No claims about ROI without actual field baseline measurement.
"""
from dataclasses import asdict,dataclass
import json,argparse

@dataclass(frozen=True)
class Assumptions:
    reusable_reader_cost_usd:float=200.0
    reader_service_life_years:float=3.0
    replaceable_cartridge_cost_usd:float=20.0
    cartridge_service_life_days:float=30.0
    installation_usd_per_year:float=120.0
    calibration_maintenance_usd_per_year:float=180.0
    required_margin_fraction:float=0.25
    baseline_measured:bool=False
    qualified_vendor_quotes:bool=False
    measured_annual_benefit_usd:float|None=None

def threshold(a:Assumptions):
    for v in (a.reusable_reader_cost_usd,a.reader_service_life_years,a.replaceable_cartridge_cost_usd,a.cartridge_service_life_days,a.installation_usd_per_year,a.calibration_maintenance_usd_per_year):
        if not isinstance(v,(int,float)) or v<0:raise ValueError('Inputs must be nonnegative')
    if a.reader_service_life_years<=0 or a.cartridge_service_life_days<=0 or not 0<=a.required_margin_fraction<1:raise ValueError('Invalid lifetime or margin')
    annual=(a.reusable_reader_cost_usd/a.reader_service_life_years+365*a.replaceable_cartridge_cost_usd/a.cartridge_service_life_days+a.installation_usd_per_year+a.calibration_maintenance_usd_per_year)
    required=annual/(1-a.required_margin_fraction)
    validated=a.baseline_measured and a.qualified_vendor_quotes and a.measured_annual_benefit_usd is not None
    return {'annualized_incremental_cost_usd':round(annual,2),
            'annual_benefit_needed_for_target_margin_usd':round(required,2),
            'disposition':'BENEFIT_TESTABLE' if validated else 'HOLD_NO_FIELD_ECONOMICS',
            'scope':'hypothetical screening assumptions, not pricing or measured savings',
            'inputs':asdict(a),
            'reason': 'Only real vendor quotes, field comparison and quantified avoided cost can support production economics.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',help='JSON Assumptions override');ns=ap.parse_args()
    x=Assumptions(**json.load(open(ns.input))) if ns.input else Assumptions()
    print(json.dumps(threshold(x),indent=2))
