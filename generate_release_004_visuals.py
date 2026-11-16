#!/usr/bin/env python3
"""
OTDB-APW Release Repair 004 — Technical Visual Figures Generator (`generate_release_004_visuals.py`).
Generates:
  1. `artifacts/otdb_apw_rev_d_connected_afe_and_architecture.png`
  2. `artifacts/otdb_apw_rev_d_synthetic_scenarios_and_fair_baselines.png`
Explicitly distinguishes synthetic literature-inspired simulations from physical measurements.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def generate_all_release_004_figures(artifacts_dir: Path) -> dict[str, str]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Figure 1: OTDB-APW Rev D Connected AFE, Split Regulators & Pin-Type Matrix
    # =========================================================================
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16.5, 7.2), dpi=160, gridspec_kw={"width_ratios": [1.55, 1.0]})
    fig1.patch.set_facecolor("#F8FAFC")

    ax1.set_facecolor("#FFFFFF")
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.axis("off")
    ax1.set_title(
        "A. OTDB-APW Rev D Analog Front-End & Split-Regulator Architecture\n"
        "(39 BoM Components + 2 PWR_FLAGs, 204 Placed Pins Across 52 Nets)",
        fontsize=11,
        fontweight="bold",
        color="#0F172A",
        pad=10,
    )

    boxes = [
        (2, 68, 30, 27, "#EFF6FF", "#1D4ED8",
         "Split Power & Negative Rail\n"
         "• J2 (+5V_IN, #FLG01/#FLG02)\n"
         "• U7A ADP7118 (+3.3V_A, 15.1mA)\n"
         "• U7B ADP7118 (+3.3V_D, 17.8mA)\n"
         "• U8 ADM8829 (-4.93V_CP Inv)\n"
         "• U7C ADP7182 (-2.5V_AVSS, 3.65mA)"),
        (2, 34, 30, 28, "#F0FDF4", "#15803D",
         "Dual Single-Ch Wagner Nulling\n"
         "• U5 ADR4525B (+2.500V, 2ppm/K)\n"
         "• U3A AD5683RBRMZ (In-Phase, PC4)\n"
         "• U3B AD5683RBRMZ (Quad, PC5)\n"
         "• U6A/B ADA4522-2 (-0.10x Sum)\n"
         "• 1.907 uV/LSB Null Resolution"),
        (35, 53, 31, 42, "#FEFCE8", "#B45309",
         "MEMS Probe & Diff 3w Bridge\n"
         "• J1 8-Pin Gold Spring Header\n"
         "• 3.5x3.5mm Fused-Silica Die\n"
         "• 30nm Al2O3 / 30nm HfO2 ALD\n"
         "• R_REF Susumu 100R 0.01% 2ppm\n"
         "• U2 AD8421BRZ INA (G=100)\n"
         "• R_AAF/C_AAF (fc=159.2 kHz)"),
        (69, 53, 29, 42, "#F5F3FF", "#6D28D9",
         "Impedance & Lock-In DSP Core\n"
         "• U1 AD5941BCPZRL7 (48-LFCSP)\n"
         "  - 1w Drive CE0/RE0 & EIS\n"
         "  - ADC Window [1.078V, 1.122V]\n"
         "• U4 STM32G474CBT6 (LQFP-48)\n"
         "  - 170MHz Cortex-M4F CORDIC\n"
         "  - ANSI C99 Schur-FIM Witness"),
        (2, 4, 96, 25, "#FFF1F2", "#BE123C",
         "Gate 2 Electrical Qualification Status (Honest Epistemic Separation)\n"
         "• Programmatic Typed S-Expression ERC: PASS (0 errors across 52 nets; 4/4 injected faults caught)\n"
         "• Embedded Library Pin Types: 38 power_in, 5 power_out, 35 input, 22 output, 26 passive, 7 no_connect, 7 bidir\n"
         "• Explicit No-Connect Markers: 7/7 (U8 Pin 5, U7C Pin 4, U5 Pins 1,3,5,7,8) | Native kicad-cli: HOLD_NATIVE_KICAD_CLI_ABSENT\n"
         "• Rev D BoM (Modeled): USD 30.05 raw @ 1k | USD 74.50 packaged probe | USD 348.00 slip-stream node | USD 11,250 Phase-1 Pilot"),
    ]
    for x, y, w, h, fc, ec, text in boxes:
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=1.0", facecolor=fc, edgecolor=ec, linewidth=1.6
        )
        ax1.add_patch(rect)
        ax1.text(x + 1.2, y + h - 1.8, text, fontsize=7.5, color="#0F172A", va="top", ha="left", linespacing=1.30)

    # Panel B: Library Pin-Type Distribution & Power Budget
    ax2.set_facecolor("#FFFFFF")
    pin_types = ["power_in\n(38)", "input\n(35)", "passive\n(26)", "output\n(22)", "bidir\n(7)", "no_conn\n(7)", "power_out\n(5)"]
    counts = [38, 35, 26, 22, 7, 7, 5]
    colors = ["#2563EB", "#0891B2", "#64748B", "#16A34A", "#D97706", "#DC2626", "#7C3AED"]
    bars = ax2.barh(pin_types[::-1], counts[::-1], color=colors[::-1], edgecolor="#0F172A", height=0.6)
    ax2.set_xlim(0, 46)
    ax2.set_xlabel("Library Pin Count (Total = 140 Pins Across 12 Symbol Definitions)", fontsize=9.2, fontweight="bold")
    ax2.set_title(
        "B. Repaired KiCad 7/8 Library Pin-Type Distribution\n(Replaces Rev C 105 All-Bidirectional Placeholders)",
        fontsize=10.5,
        fontweight="bold",
        color="#0F172A",
        pad=10,
    )
    ax2.grid(axis="x", linestyle="--", alpha=0.4)
    for b in bars:
        w = b.get_width()
        ax2.text(w + 0.8, b.get_y() + b.get_height() / 2.0, f"{int(w)} pins", va="center", ha="left", fontsize=8.8, fontweight="bold")

    fig1.tight_layout(pad=1.8)
    fig1_path = artifacts_dir / "otdb_apw_rev_d_connected_afe_and_architecture.png"
    fig1.savefig(fig1_path, dpi=160)
    plt.close(fig1)

    # =========================================================================
    # Figure 2: LBNL- & Khaja-2026-Inspired Synthetic Scenarios & Negative Controls
    # =========================================================================
    fig2, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(16.5, 7.2), dpi=160)
    fig2.patch.set_facecolor("#F8FAFC")

    scenarios = [
        "S1: Constant-EC\nParticulate (CP=1.0x)\n[CONVENTIONAL WINS]",
        "S2: Synthetic Scaling\n+ Soluble CP (1.35-2.15x)\n[OTDB-APW WINS]",
        "S3: Synthetic Cake\nCompaction (phi=8-38%)\n[OTDB-APW WINS]",
        "S4: High-Water EPS\nHydrogel (42-58% H2O)\n[DEGRADED 13.4%]",
    ]
    otdb_means = [3.96, 8.17, 8.05, 13.42]
    b3_fusion_means = [0.67, 43.31, 32.69, 85.73]
    b2_thermal_means = [0.91, 36.58, 38.40, 74.20]
    b1_eis_means = [13.38, 49.18, 46.23, 88.10]

    x = np.arange(len(scenarios))
    w = 0.19
    ax_a.set_facecolor("#FFFFFF")
    r1 = ax_a.bar(x - 1.5 * w, otdb_means, w, label="OTDB-APW Rev D (5-State Gauss-Newton)", color="#1D4ED8", edgecolor="#0F172A")
    r2 = ax_a.bar(x - 0.5 * w, b3_fusion_means, w, label="B3: Calibrated Multi-Sensor Fusion (EIS+3w+dP+Flow+Pt1000)", color="#16A34A", edgecolor="#0F172A")
    r3 = ax_a.bar(x + 0.5 * w, b2_thermal_means, w, label="B2: Calibrated Single-Arm 3w + Flow + EC + Pt1000", color="#D97706", edgecolor="#0F172A")
    r4 = ax_a.bar(x + 1.5 * w, b1_eis_means, w, label="B1: Calibrated Multi-Freq EIS + DRT + Pt1000", color="#64748B", edgecolor="#0F172A")

    ax_a.set_ylabel("Mean Thickness Estimation Error (%)", fontsize=9.5, fontweight="bold")
    ax_a.set_title(
        "A. Literature-Inspired Synthetic Scenarios (N_cal=60 Frozen Before Holdout)\n"
        "[SYNTHETIC SIMULATION ONLY — 0 Beamline Files, 0 Wafers, 0 Wet-Lab Hours]",
        fontsize=10.0,
        fontweight="bold",
        color="#0F172A",
    )
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(scenarios, fontsize=8.1, fontweight="bold")
    ax_a.set_ylim(0, 112)
    ax_a.grid(axis="y", linestyle="--", alpha=0.4)
    ax_a.legend(loc="upper left", fontsize=7.8, framealpha=0.92)

    for bars_grp in (r1, r2, r3, r4):
        for b in bars_grp:
            val = b.get_height()
            ax_a.text(
                b.get_x() + b.get_width() / 2.0,
                val + 1.4,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=7.2,
                fontweight="bold",
            )

    # Panel B: 6 Negative-Control & Loss Regimes (NC1..NC6)
    ax_b.set_facecolor("#FFFFFF")
    nc_labels = [
        "NC1: >85um\nCake\n(dP: 1.14%)",
        "NC2: 18.2M\nUPW\n(EC: 0.85%)",
        "NC3: <150nm\nFilm\n(QCM: 3.4%)",
        "NC4: Oil\nEmulsion\n(Unsteady)",
        "NC5: Fouled\nRef Arm\n(B3: 7.72%!)",
        "NC6: ALD\nPinhole\n(Shunt<45k)",
    ]
    otdb_nc_forced = [78.40, 100.0, 41.25, 64.80, 71.17, 82.10]
    conv_nc_best = [1.14, 0.85, 3.40, 15.0, 7.72, 12.0]

    x_nc = np.arange(len(nc_labels))
    w_nc = 0.34
    b_otdb = ax_b.bar(x_nc - w_nc / 2, otdb_nc_forced, w_nc, label="OTDB-APW Rev D Error If Forced (Before Abstention)", color="#DC2626", edgecolor="#0F172A")
    b_conv = ax_b.bar(x_nc + w_nc / 2, conv_nc_best, w_nc, label="Best Conventional Specialist / Multi-Sensor Baseline", color="#0EA5E9", edgecolor="#0F172A")

    ax_b.set_ylabel("Mean Error If Forced (%)", fontsize=9.5, fontweight="bold")
    ax_b.set_title(
        "B. 6 Negative-Control & Loss Regimes Where Conventional Wins or OTDB Abstains\n"
        "(Includes NC5 Unflagged Partial Reference-Arm Fouling Loss: 71.2% vs B3 7.7%)",
        fontsize=10.0,
        fontweight="bold",
        color="#0F172A",
    )
    ax_b.set_xticks(x_nc)
    ax_b.set_xticklabels(nc_labels, fontsize=8.0, fontweight="bold")
    ax_b.set_ylim(0, 125)
    ax_b.grid(axis="y", linestyle="--", alpha=0.4)
    ax_b.legend(loc="upper right", fontsize=8.0, framealpha=0.92)

    tags = ["Abstains\n20/20", "Abstains\n20/20", "Loss\n(18/20 Abs)", "Abstains\n20/20", "LOSS!\n(0/20 Abs)", "Abstains\n19/20"]
    for idx, b in enumerate(b_otdb):
        val = b.get_height()
        ax_b.text(
            b.get_x() + b.get_width() / 2.0,
            val + 1.5,
            f"{val:.1f}%\n{tags[idx]}",
            ha="center",
            va="bottom",
            fontsize=6.9,
            fontweight="bold",
            color="#991B1B",
        )
    for b in b_conv:
        val = b.get_height()
        ax_b.text(
            b.get_x() + b.get_width() / 2.0,
            val + 1.5,
            f"{val:.2f}%",
            ha="center",
            va="bottom",
            fontsize=7.2,
            fontweight="bold",
            color="#0369A1",
        )

    fig2.tight_layout(pad=1.8)
    fig2_path = artifacts_dir / "otdb_apw_rev_d_synthetic_scenarios_and_fair_baselines.png"
    fig2.savefig(fig2_path, dpi=160)
    plt.close(fig2)

    return {
        "architecture_figure": "artifacts/otdb_apw_rev_d_connected_afe_and_architecture.png",
        "benchmarks_figure": "artifacts/otdb_apw_rev_d_synthetic_scenarios_and_fair_baselines.png",
    }


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    res = generate_all_release_004_figures(base / "artifacts")
    print(res)
