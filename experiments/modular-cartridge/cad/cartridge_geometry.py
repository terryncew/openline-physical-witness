"""Parametric drawing + optional STEP/STL export of a LOW-PRESSURE REVIEW fixture.

Research model only, not a pressure vessel, medical/industrial instrument, or machining sign-off.
Uses only Python standard library for geometric checks and SVG; optional cadquery for STEP.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import json, math

@dataclass(frozen=True)
class Cartridge:
    outer_x_mm: float=92.0
    outer_y_mm: float=82.0
    base_thickness_mm: float=6.0
    lid_thickness_mm: float=8.0
    channel_length_mm: float=64.0
    channel_width_mm: float=9.0
    channel_lid_depth_mm: float=0.8
    channel_pitch_mm: float=21.0
    gasket_window_length_mm: float=67.0
    gasket_window_width_mm: float=11.0
    gasket_nominal_mm: float=1.0
    hard_stop_nominal_mm: float=0.75
    gasket_tol_mm: float=0.05
    stop_tol_mm: float=0.05
    coupon_length_mm: float=16.0
    coupon_width_mm: float=10.0
    coupon_pocket_depth_mm: float=0.7
    port_diameter_mm: float=2.2
    bolt_clearance_mm: float=4.2
    channels: tuple[float,...]=(-21.0,0.0,21.0)
    bolt_locations: tuple[tuple[float,float],...]=((-38.,-32.),(-38.,32.),(38.,-32.),(38.,32.))
    alignment_locations: tuple[tuple[float,float],...]=((20.,35.),(-20.,-35.))


def screen(p: Cartridge) -> dict:
    """Checks necessary geometry + robust compression at corners of stated dimension bands.

    Not a measured seal or leak guarantee. Positive clearance means 2D layout only.
    """
    lows=[]
    for thick in (p.gasket_nominal_mm-p.gasket_tol_mm,p.gasket_nominal_mm+p.gasket_tol_mm):
        for stop in (p.hard_stop_nominal_mm-p.stop_tol_mm,p.hard_stop_nominal_mm+p.stop_tol_mm):
            lows.append((thick-stop)/thick)
    margin_to_edge=(p.outer_y_mm/2-max(abs(y) for y in p.channels)-p.gasket_window_width_mm/2)
    channel_gap=p.channel_pitch_mm-p.gasket_window_width_mm
    def hole_avoids_channel(x,y,r):
        for cy in p.channels:
            dx=max(abs(x)-p.gasket_window_length_mm/2,0)
            dy=max(abs(y-cy)-p.gasket_window_width_mm/2,0)
            if math.hypot(dx,dy)<r+1.0: return False
        return True
    all_holes_avoid_channels=all(hole_avoids_channel(x,y,p.bolt_clearance_mm/2) for x,y in p.bolt_locations) and all(hole_avoids_channel(x,y,1.5) for x,y in p.alignment_locations)
    # Distance to horizontal limits; sign checks only, NOT full hole-vs-window collision checking
    rules={
        "nominal_gasket_compression_15_to_35pct":0.15 <= (p.gasket_nominal_mm-p.hard_stop_nominal_mm)/p.gasket_nominal_mm <= 0.35,
        "worst_case_gasket_compression_15_to_35pct":min(lows)>=0.15 and max(lows)<=0.35,
        "positive_channel_separation_mm":channel_gap>=5.0,
        "window_fits_cartridge":p.gasket_window_length_mm<p.outer_x_mm-12 and margin_to_edge>8,
        "coupon_inside_window":p.coupon_length_mm<p.gasket_window_length_mm and p.coupon_width_mm<p.gasket_window_width_mm,
        "port_inside_channel":p.port_diameter_mm < p.channel_width_mm/2,
        "hole_edges_clear_of_channel_windows_by_1mm":all_holes_avoid_channels,
        "three_distinct_channels":tuple(p.channels)==(-p.channel_pitch_mm,0.,p.channel_pitch_mm),
    }
    return {"geometry_screen_pass":all(rules.values()), "checks":rules,
      "gasket_crush_fraction_min":round(min(lows),6), "gasket_crush_fraction_max":round(max(lows),6),
      "gasket_crush_fraction_nominal":round((p.gasket_nominal_mm-p.hard_stop_nominal_mm)/p.gasket_nominal_mm,6),
      "gasket_land_between_channels_mm":channel_gap,
      "cautions":["Not a seal qualification. Tolerance bands are engineer assumptions, not supplier guarantees.",
        "Hard stops must be physically independent of gasket relaxation.",
        "Creep, thermal expansion, membrane swelling, fluid pressure and chemical compatibility unmeasured.",
        "Guard branch fluid chemistry/hydrodynamics cannot be assumed equal to sense branch."]}


def svg_plan(p:Cartridge)->str:
    scale=6.; width=(p.outer_x_mm+18)*scale; height=(p.outer_y_mm+20)*scale
    def X(v):return round((v+p.outer_x_mm/2+9)*scale,2)
    def Y(v):return round((v+p.outer_y_mm/2+10)*scale,2)
    a=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}">',
       '<rect width="100%" height="100%" fill="#fcfcfb"/>',
       f'<rect x="{X(-p.outer_x_mm/2)}" y="{Y(-p.outer_y_mm/2)}" width="{p.outer_x_mm*scale}" height="{p.outer_y_mm*scale}" rx="18" fill="#ecf2f3" stroke="#0b3643" stroke-width="2"/>']
    labels=['S — depositing','R — reference','G — guard']
    for y,label in zip(p.channels,labels):
        a.append(f'<rect x="{X(-p.gasket_window_length_mm/2)}" y="{Y(y-p.gasket_window_width_mm/2)}" width="{p.gasket_window_length_mm*scale}" height="{p.gasket_window_width_mm*scale}" rx="6" fill="#d7e9ee" stroke="#246076" stroke-width="2"/>')
        a.append(f'<rect x="{X(-p.coupon_length_mm/2)}" y="{Y(y-p.coupon_width_mm/2)}" width="{p.coupon_length_mm*scale}" height="{p.coupon_width_mm*scale}" rx="3" fill="{"#dfbb8e" if y==p.channels[0] else "#c8d2d4"}" stroke="#55666e" stroke-width="2"/>')
        for x in (-p.channel_length_mm/2+3,p.channel_length_mm/2-3):
            a.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{p.port_diameter_mm*scale/2}" fill="#fff" stroke="#276071" stroke-width="2"/>')
        a.append(f'<text x="{X(-p.gasket_window_length_mm/2+1.7)}" y="{Y(y)-9}" font-family="Arial,sans-serif" font-size="11" text-anchor="start" fill="#14383e">{label}</text>')
    for x,y in p.bolt_locations:a.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{p.bolt_clearance_mm*scale/2}" fill="white" stroke="#0b3643" stroke-width="2"/>')
    for x,y in p.alignment_locations:a.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="7" fill="#f7a760" stroke="#a85e21" stroke-width="1.8"/>')
    a.append(f'<text x="{width/2}" y="{height-10}" fill="#3a5059" text-anchor="middle" font-family="Arial" font-size="15">92 × 82 mm review fixture · S/R/G independently plumbed · dimensions are provisional</text>')
    a.append('</svg>')
    return '\n'.join(a)+'\n'


def export_optional_step(p:Cartridge,outdir:Path)->str:
    try:import cadquery as cq
    except ImportError:return 'SKIP: cadquery not installed; SVG + geometry still available'
    # Explicit design model; not a manufacturability/fab signoff
    lid=cq.Workplane('XY').box(p.outer_x_mm,p.outer_y_mm,p.lid_thickness_mm, centered=(True,True,False))
    base=cq.Workplane('XY').box(p.outer_x_mm,p.outer_y_mm,p.base_thickness_mm, centered=(True,True,False)).translate((0,0,-p.base_thickness_mm))
    gasket=cq.Workplane('XY').box(p.outer_x_mm,p.outer_y_mm,p.hard_stop_nominal_mm,centered=(True,True,False))
    for y in p.channels:
        cutter=cq.Workplane('XY').box(p.channel_length_mm,p.channel_width_mm,p.channel_lid_depth_mm,centered=(True,True,False)).translate((0,y,0))
        lid=lid.cut(cutter)
        cavity=cq.Workplane('XY').box(p.gasket_window_length_mm,p.gasket_window_width_mm,p.hard_stop_nominal_mm+0.2,centered=(True,True,False)).translate((0,y,-0.1))
        gasket=gasket.cut(cavity)
        pocket=cq.Workplane('XY').box(p.coupon_length_mm,p.coupon_width_mm,p.coupon_pocket_depth_mm,centered=(True,True,False)).translate((0,y,-p.coupon_pocket_depth_mm))
        base=base.cut(pocket)
        for x in [-p.channel_length_mm/2+3,p.channel_length_mm/2-3]:
            port=cq.Workplane('XY').center(x,y).circle(p.port_diameter_mm/2).extrude(p.lid_thickness_mm+1)
            lid=lid.cut(port)
    for x,y in p.bolt_locations:
        cut=cq.Workplane('XY').center(x,y).circle(p.bolt_clearance_mm/2).extrude(p.base_thickness_mm+p.lid_thickness_mm+2).translate((0,0,-p.base_thickness_mm-1))
        lid=lid.cut(cut);base=base.cut(cut);gasket=gasket.cut(cut)
    for x,y in p.alignment_locations:
        cut=cq.Workplane('XY').center(x,y).circle(1.5).extrude(p.base_thickness_mm+p.lid_thickness_mm+2).translate((0,0,-p.base_thickness_mm-1))
        lid=lid.cut(cut);base=base.cut(cut);gasket=gasket.cut(cut)
    for label,shape in [('lid_review',lid),('base_review',base),('gasket_compressed_review',gasket)]:
        cq.exporters.export(shape,str(outdir/(label+'.step')))
    return 'Generated 3 STEP review solids; NOT manufacturer qualified or approved for pressure use'


def main():
    out=Path(__file__).resolve().parent/'generated';out.mkdir(exist_ok=True)
    p=Cartridge();q=screen(p)
    (out/'PARAMETERS.json').write_text(json.dumps(asdict(p),indent=2)+'\n')
    (out/'GEOMETRY_SCREEN.json').write_text(json.dumps(q,indent=2)+'\n')
    (out/'cartridge_plan.svg').write_text(svg_plan(p))
    print(json.dumps(q,indent=2));print(export_optional_step(p,out))
    if not q['geometry_screen_pass']:raise SystemExit(2)
if __name__=='__main__':main()
