#!/usr/bin/env python3
"""Hard-gate the 005 addon as a conceptual schematic, never a build-ready board.

Outputs machine-readable evidence. Does not claim native CAD ERC or a vendor pinout check.
"""
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def check():
    schematic=(ROOT/'artifacts/otdb_apw_005_hunstat2_addon.kicad_sch').read_text()
    fw=(ROOT/'firmware/otdb_apw_005_rp2040_firmware.c').read_text()
    marker='(symbol "OTDB005:AD5941BCPZ_HUNSTAT2"'
    begin=schematic.find(marker)
    if begin < 0: return {'disposition':'HOLD','reason':'AD5941 symbol missing'}
    finish=schematic.find('\n    (symbol "OTDB005:',begin+len(marker))
    segment=schematic[begin:finish if finish>=0 else len(schematic)]
    pin_numbers=re.findall(r'\(number "([0-9]+)"',segment)
    unique_pins=len(set(pin_numbers))
    issues=[]
    if unique_pins != 48:
        issues.append(f'AD5941 48-LFCSP has only {unique_pins} symbol pin numbers; not a verified manufacturer pin map')
    if not (ROOT/'firmware/pico_sdk_integration.c').exists():
        issues.append('No RP2040 SDK/HAL acquisition, SPI, ADC, clock, DMA/PIO and flash image')
    if not any(ROOT.rglob('*.kicad_pcb')):
        issues.append('No routed PCB layout or manufacturable Gerber/assembly package')
    if not (ROOT/'artifacts/native_kicad_erc_verified.json').exists():
        issues.append('No native KiCad ERC independent verification receipt')
    if not (ROOT/'artifacts/physical_raw_data.csv').exists():
        issues.append('No measured physical fouling instrument data')
    return {'qualification':'RESEARCH DESIGN ONLY','disposition':'HOLD' if issues else 'REQUIRES_INDEPENDENT_REVIEW',
        'ad5941_symbol_unique_pin_count':unique_pins,'issues':issues}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--json',action='store_true');a=parser.parse_args()
    r=check(); print(json.dumps(r,indent=2))
