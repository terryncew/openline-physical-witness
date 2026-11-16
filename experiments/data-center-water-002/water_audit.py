#!/usr/bin/env python3
"""Offline OpenLine Sensors water/energy audit. Standard library, read-only.

No actuation, optimization authority, or proven water-saving claims.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ("timestamp_utc", "duration_h", "it_kw", "cooling_kw", "makeup_l", "blowdown_l")
NUMERIC = REQUIRED[1:]

class EvidenceError(ValueError):
    pass

def finite_number(raw, name, row):
    try: val = float(raw)
    except (ValueError, TypeError): raise EvidenceError(f"row {row}: invalid {name}") from None
    if not math.isfinite(val) or val < 0:
        raise EvidenceError(f"row {row}: {name} must be nonnegative finite")
    return val

def parse_utc(s, row):
    try:
        d = datetime.fromisoformat(s.replace('Z','+00:00'))
    except (TypeError, ValueError): raise EvidenceError(f"row {row}: invalid ISO timestamp") from None
    if d.tzinfo is None: raise EvidenceError(f"row {row}: timezone required")
    return d.astimezone(timezone.utc)

def audit(path: str | Path, grid_intensity: float | None = None) -> dict:
    source = Path(path)
    if not source.is_file(): raise EvidenceError("CSV source missing")
    blob = source.read_bytes()
    if not blob: raise EvidenceError("empty CSV")
    if grid_intensity is not None and (not math.isfinite(grid_intensity) or grid_intensity < 0):
        raise EvidenceError("grid water intensity must be nonnegative and finite")
    rows=[]
    uncovered_gap_h=0.0
    with source.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in REQUIRED):
            raise EvidenceError("missing required columns: "+','.join(REQUIRED))
        previous=None
        previous_duration=0.0
        for i, raw in enumerate(reader,2):
            d=parse_utc(raw['timestamp_utc'],i)
            if previous is not None and d <= previous: raise EvidenceError(f"row {i}: non-increasing timestamp")
            v={k: finite_number(raw.get(k),k,i) for k in NUMERIC}
            if previous is not None:
                delta_h=(d-previous).total_seconds()/3600
                if delta_h+1e-7 < previous_duration: raise EvidenceError(f"row {i}: overlapping metering intervals")
                uncovered_gap_h+=max(0,delta_h-previous_duration)
            previous=d
            previous_duration=v['duration_h']
            if not 0 < v['duration_h'] <= 24: raise EvidenceError(f"row {i}: duration_h outside (0,24]")
            if v['makeup_l']+1e-9 < v['blowdown_l']:
                raise EvidenceError(f"row {i}: blowdown exceeds makeup; no negative evaporation inference")
            if v['it_kw']<=0:raise EvidenceError(f"row {i}: IT power must exceed zero")
            v['timestamp_utc']=d.isoformat()
            rows.append(v)
    if not rows: raise EvidenceError("no data rows")
    hours=sum(x['duration_h'] for x in rows)
    it=sum(x['it_kw']*x['duration_h'] for x in rows)
    cooling=sum(x['cooling_kw']*x['duration_h'] for x in rows)
    makeup=sum(x['makeup_l'] for x in rows)
    blowdown=sum(x['blowdown_l'] for x in rows)
    # Makeup - blowdown is *not* always true consumption: inventory changes, drift,
    # other discharges and unmetered sources can invalidate the proxy.
    estimate=makeup-blowdown
    return {
      'status':'MEASURED_INPUT_AUDIT_NOT_VALIDATED_SAVINGS',
      'source_sha256':hashlib.sha256(blob).hexdigest(), 'rows':len(rows),
      'period_start_utc': rows[0]['timestamp_utc'], 'period_end_utc':rows[-1]['timestamp_utc'],
      'measured_hours':round(hours,4),'uncovered_gap_hours_between_rows':round(uncovered_gap_h,4),'it_kwh':round(it,4),'cooling_kwh':round(cooling,4),
      'site_makeup_l':round(makeup,4),'blowdown_discharge_l':round(blowdown,4),
      'site_wue_makeup_l_per_it_kwh':round(makeup/it,6),
      'makeup_minus_blowdown_l_proxy_not_validated_consumption':round(estimate,4),
      'source_electricity_water_l_scenario':None if grid_intensity is None else round((it+cooling)*grid_intensity,4),
      'source_intensity_l_per_kwh_scenario':grid_intensity,
      'warnings':[
         'Makeup is site water intake, not net consumption; blowdown is discharge.',
         'Makeup-minus-blowdown assumes steady inventory and no unmetered water paths.',
         'Electricity water intensity, when supplied, is a user scenario, not site data.',
         'Gaps in input intervals are not extrapolated; inspect uncovered_gap_hours_between_rows.',
         'No control change or savings is inferred from these observations.',
         'Offline advisory only: not safe for live facility actuation.'
      ],
    }

def evaluate_scenario(obj: dict) -> dict:
    """Compute transparent tower-water scenario for two designs with a shared load.

    Evaporative tower E is an explicit INPUT coefficient, not a sensor invention.
    At steady state M=E*CoC/(CoC-1), B=E/(CoC-1); drift is assumed 0.
    """
    base=obj.get('baseline',{}); candidate=obj.get('candidate',{})
    shared=obj.get('shared',{})
    def req(d,k):
        try: x=float(d[k])
        except (KeyError,ValueError,TypeError): raise EvidenceError(f"missing or invalid {k}") from None
        if not math.isfinite(x) or x<0: raise EvidenceError(f"negative/nonfinite {k}")
        return x
    hours=req(shared,'hours'); load=req(shared,'rejected_heat_kw'); it=req(shared,'it_kw'); grid=req(shared,'grid_l_per_kwh')
    if hours<=0 or hours>8784 or it<=0: raise EvidenceError('invalid duration or IT load')
    def arm(d):
        dry=req(d,'dry_fraction');coc=req(d,'cycles_of_concentration');factor=req(d,'evap_l_per_kwh_rejected');power=req(d,'cooling_elec_kw')
        if not 0<=dry<=1 or coc<=1: raise EvidenceError('dry_fraction outside [0,1] or CoC<=1')
        evaporation=hours*load*(1-dry)*factor
        makeup=evaporation*coc/(coc-1)
        blowdown=evaporation/(coc-1)
        gridwater=hours*(it+power)*grid
        return {'dry_fraction':dry,'cycles_of_concentration':coc,'cooling_elec_kwh':round(hours*power,3),
                'evaporation_l_model':round(evaporation,3),'blowdown_l_model':round(blowdown,3),
                'site_makeup_l_model':round(makeup,3),'site_wue_l_per_it_kwh_model':round(makeup/(hours*it),6),
                'electricity_source_water_l_model':round(gridwater,3),
                'total_site_makeup_plus_electricity_water_l_model':round(makeup+gridwater,3)}
    a=arm(base);b=arm(candidate)
    water_diff=a['site_makeup_l_model']-b['site_makeup_l_model']
    same_physical=(base.get('dry_fraction')==candidate.get('dry_fraction') and base.get('cycles_of_concentration')==candidate.get('cycles_of_concentration') and base.get('evap_l_per_kwh_rejected')==candidate.get('evap_l_per_kwh_rejected'))
    return {'status':'ASSUMPTION_DRIVEN_SCENARIO_NOT_OBSERVED',
      'baseline':a,'candidate':b,'site_makeup_delta_l_model':round(water_diff,3),
      'source_water_delta_l_model':round(a['total_site_makeup_plus_electricity_water_l_model']-b['total_site_makeup_plus_electricity_water_l_model'],3),
      'same_heat_rejection_physics':same_physical,'openline_attributable_water_savings_proven':False,
      'warnings':['Scenario results depend on input equipment/configuration assumptions.',
       'A difference caused by dry_fraction or cycles is a plant design difference, not a new-sensor win.',
       'This simple model ignores thermal safety, water chemistry, weather, inventory and lifecycle impacts.',
       'No controls are proposed or executed.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('audit',help='audit observed CSV (no savings attribution)');a.add_argument('csv');a.add_argument('--grid-l-per-kwh',type=float)
    b=s.add_parser('scenario',help='compare explicit constructed water scenarios');b.add_argument('json')
    args=p.parse_args()
    try:
        result=audit(args.csv,args.grid_l_per_kwh) if args.command=='audit' else evaluate_scenario(json.loads(Path(args.json).read_text()))
    except (EvidenceError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'HOLD_INVALID_EVIDENCE','error':str(e)},indent=2));return 2
    print(json.dumps(result,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
