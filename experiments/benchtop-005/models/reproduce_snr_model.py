#!/usr/bin/env python3
"""Exploratory model with assumed physical parameters, NOT measured sensor performance."""
from __future__ import annotations
import json
import math
import numpy as np

def run_snr_and_reference_falsifier() -> dict:
    """
    Computes assumed-parameter signal-to-noise (SNR) projections for commodity
    Vishay PTS060301B100RP100 0603 Pt100 SMD RTDs on the HunStat2 + OTDB-005
    bridge at f_1w = 1.0 Hz and 8.0 Hz, AND runs a seeded synthetic parameter
    falsification of the Dual-AD8421 (U2A Diff + U2B Ref) + Dual-IDE reference-
    contamination detector across symmetric and partial reference-arm fouling.
    """
    # Physical constants of Vishay PTS060301B100RP100 (100 Ohm Pt100 0603 RTD)
    r0_ohm = 100.0
    alpha_pt = 0.003850  # K^-1 (3850 ppm/K)
    r_top_ohm = 100.0    # Susumu RG1608N-101-D-T5 100 Ohm 2-10 ppm/K
    i_rms_a = 0.0120     # 12.0 mA RMS per branch (24.0 mA total bridge RMS)
    p_rms_w = (i_rms_a ** 2) * r0_ohm  # 14.4 mW average heating per Pt100 element
    # Active footprint of 0603 RTD (1.55 mm x 0.85 mm = 1.3175e-6 m^2; effective thermal transfer area A_eff = 2.4e-6 m^2 including solder fillets)
    a_eff_m2 = 2.4e-6
    k_caco3 = 2.18       # W/(m*K) calcite thermal conductivity
    k_water = 0.606      # W/(m*K) water at 25 C

    # Thermal penetration depth delta_th = sqrt(D_th / (pi * f_2w))
    # Water D_th = 1.43e-7 m^2/s; Alumina substrate D_th = 8.5e-6 m^2/s
    # At f_1w = 1.0 Hz (f_2w = 2.0 Hz): delta_th_water = 151 um
    # At f_1w = 8.0 Hz (f_2w = 16.0 Hz): delta_th_water = 53.3 um
    # For a solid CaCO3 film of thickness d_f (0 to 30 um) on the glass-passivated RTD surface,
    # the added series thermal impedance is Delta Z_th(d_f) = (d_f / (k_caco3 * A_eff)) * attenuation_factor(f_1w)
    # where attenuation_factor accounts for the 0603 alumina substrate heat-spreading shunting factor (eta_spread = 0.28 at 1 Hz, 0.19 at 8 Hz)
    eta_spread_1hz = 0.28
    eta_spread_8hz = 0.19

    # 3w voltage sensitivity per meter of CaCO3 thickness:
    # V_3w = 0.5 * I_peak * R0 * alpha_pt * Delta_T_2w
    # With I_rms = 12 mA (I_peak = 16.97 mA), P_2w_amp = 0.5 * I_peak^2 * R0 = 14.4 mW:
    # d(Delta_T_2w)/d(d_f) = P_2w_amp * eta_spread / (k_caco3 * A_eff)
    dT2w_ddf_1hz = (p_rms_w * eta_spread_1hz) / (k_caco3 * a_eff_m2)  # K / m
    dT2w_ddf_8hz = (p_rms_w * eta_spread_8hz) / (k_caco3 * a_eff_m2)  # K / m

    # Bridge midpoint 3w voltage (pre-in-amp, RMS):
    # Bridge divider factor = R_top / (R_top + R0) = 0.5
    dv3w_ddf_preamp_1hz = 0.5 * i_rms_a * r0_ohm * alpha_pt * dT2w_ddf_1hz  # V_rms / m
    dv3w_ddf_preamp_8hz = 0.5 * i_rms_a * r0_ohm * alpha_pt * dT2w_ddf_8hz  # V_rms / m

    gain_inamp = 100.0
    # Convert to uV_rms per um of CaCO3 scale:
    uv_preamp_per_um_1hz = dv3w_ddf_preamp_1hz * 1e6 * 1e-6
    uv_preamp_per_um_8hz = dv3w_ddf_preamp_8hz * 1e6 * 1e-6

    # Noise Floor Calculation (Referred to Bridge Midpoint Input, RTI):
    # 1. Johnson-Nyquist thermal noise of bridge (two 100-Ohm arms in parallel = 50 Ohm each side -> 100 Ohm total differential source impedance):
    #    e_n_bridge = sqrt(4 * k_B * T * 100 Ohm) = 1.29 nV/rtHz
    # 2. AD8421BRZ input voltage noise at G=100 (3 Hz to 24 Hz):
    #    e_n_inamp = 3.2 nV/rtHz (with 1/f corner at 1 Hz -> ~4.1 nV/rtHz at 3 Hz, 3.3 nV/rtHz at 24 Hz)
    # 3. AD8421BRZ input current noise: i_n = 200 fA/rtHz * 50 Ohm = 0.01 nV/rtHz (negligible)
    # 4. AD5941 16-bit SAR ADC + Sinc3/DFT quantization noise referred to AD8421 input (G=100):
    #    ADC full-scale = 1.82 V, 16-bit LSB = 27.8 uV; oversampled at 512 Hz -> 22.1 nV/rtHz at ADC input -> 0.22 nV/rtHz RTI
    # 5. Drive DAC (AD5683R) residual 3rd-harmonic / common-mode bridge mismatch (0.05% Susumu + software digital trim to 50 ppm):
    #    Gives a coherent baseline offset of ~0.42 uV RTI (calibrated out during t=0 clean baseline tare),
    #    with thermal/flow drift jitter of sigma_flow_rti = 0.085 uV RMS over a 10-second lock-in window (ENBW = 0.05 Hz).
    en_total_1hz_nv_rthz = math.sqrt(1.29**2 + 4.10**2 + 0.22**2)  # ~4.30 nV/rtHz at f_3w = 3 Hz
    en_total_8hz_nv_rthz = math.sqrt(1.29**2 + 3.30**2 + 0.22**2)  # ~3.55 nV/rtHz at f_3w = 24 Hz

    t_int_s = 10.0  # 10-second synchronous lock-in integration window
    enbw_hz = 1.0 / (2.0 * t_int_s)  # 0.05 Hz two-sided equivalent noise bandwidth
    electronic_noise_rti_uv_1hz = (en_total_1hz_nv_rthz * math.sqrt(enbw_hz)) * 1e-3
    electronic_noise_rti_uv_8hz = (en_total_8hz_nv_rthz * math.sqrt(enbw_hz)) * 1e-3

    # Dominant noise in flowing water is hydrodynamic convective flicker on the unshielded Sense RTD:
    # Differential bridge rejection reduces common-mode flow flicker by ~28 dB (25x), leaving
    # sigma_hydro_rti = 0.110 uV RMS at 1 Hz and 0.068 uV RMS at 8 Hz (higher frequency confines thermal wave closer to surface).
    sigma_total_rti_uv_1hz = math.sqrt(electronic_noise_rti_uv_1hz**2 + 0.110**2)
    sigma_total_rti_uv_8hz = math.sqrt(electronic_noise_rti_uv_8hz**2 + 0.068**2)

    thickness_grid_um = [0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0]
    snr_table = []
    for d_um in thickness_grid_um:
        sig_1hz_uv = uv_preamp_per_um_1hz * d_um
        sig_8hz_uv = uv_preamp_per_um_8hz * d_um
        snr_1hz_linear = sig_1hz_uv / sigma_total_rti_uv_1hz
        snr_8hz_linear = sig_8hz_uv / sigma_total_rti_uv_8hz
        snr_table.append({
            "caco3_thickness_um": d_um,
            "dv3w_rti_1hz_uv_rms": round(sig_1hz_uv, 4),
            "dv3w_adc_input_g100_1hz_mv_rms": round(sig_1hz_uv * gain_inamp / 1000.0, 4),
            "snr_1hz_linear": round(snr_1hz_linear, 2),
            "snr_1hz_db": round(20.0 * math.log10(max(snr_1hz_linear, 1e-6)), 2),
            "dv3w_rti_8hz_uv_rms": round(sig_8hz_uv, 4),
            "dv3w_adc_input_g100_8hz_mv_rms": round(sig_8hz_uv * gain_inamp / 1000.0, 2),
            "snr_8hz_linear": round(snr_8hz_linear, 2),
            "snr_8hz_db": round(20.0 * math.log10(max(snr_8hz_linear, 1e-6)), 2),
            "exceeds_3sigma_detection_floor": bool(snr_1hz_linear >= 3.0 and snr_8hz_linear >= 3.0),
            "exceeds_10sigma_quantification_floor": bool(snr_1hz_linear >= 10.0 and snr_8hz_linear >= 10.0),
        })

    # Minimum detectable thickness (3-sigma and 10-sigma):
    lod_3sigma_um_1hz = 3.0 * sigma_total_rti_uv_1hz / uv_preamp_per_um_1hz
    loq_10sigma_um_1hz = 10.0 * sigma_total_rti_uv_1hz / uv_preamp_per_um_1hz
    lod_3sigma_um_8hz = 3.0 * sigma_total_rti_uv_8hz / uv_preamp_per_um_8hz
    loq_10sigma_um_8hz = 10.0 * sigma_total_rti_uv_8hz / uv_preamp_per_um_8hz

    # ========================================================================
    # 3. DUAL-AD8421 (U2A + U2B) + IDE_REF REFERENCE-CONTAMINATION FALSIFIER
    # ========================================================================
    # A previous computational assessment suggested a possible reference-channel gap:
    # - A hardware channel gap: Rev D only digitized U2A (v3w_diff = Sense - Ref),
    #   not v3w_ref independently.
    # - A low-ratio blind spot: partial reference fouling (2% to 10% of sense fouling)
    #   went undetected.
    # In this unbuilt design, we propose U2B (AD8421BRZ measuring BRIDGE_MID_REF vs Susumu fixed divider -> AIN2)
    # AND TMUX1108 routing of IDE_REF into AD5941 EIS.
    # Model-only: these calculations do not establish the physical fault-coverage curve.
    rng = np.random.default_rng(20260505)
    n_trials_per_level = 100
    ref_fouling_levels = [
        ("0pct_Clean_Reference", 0.00),
        ("2pct_Micro_Leak_Reference", 0.02),
        ("5pct_Trace_Leak_Reference", 0.05),
        ("10pct_Minor_Leak_Reference", 0.10),
        ("20pct_Moderate_Leak_Reference", 0.20),
        ("35pct_Partial_Bypass_Reference", 0.35),
        ("60pct_Severe_Bypass_Reference", 0.60),
        ("100pct_Symmetric_CommonMode_Failure", 1.00),
    ]

    # Notice what happens in U2B (single-ended Reference RTD vs fixed Susumu divider):
    # Unlike U2A (which cancels ambient temperature T_amb and flow fluctuations between Sense & Ref RTDs),
    # U2B compares a Pt100 RTD (3850 ppm/K) against a fixed Susumu resistor (2 ppm/K)!
    # While the 1w DC/fundamental shifts with T_amb, the 3w harmonic on U2B is modulated by
    # convective flow fluctuations (uncompensated single-ended hydrodynamic flicker sigma_u2b_rti = 0.34 uV RMS)
    # plus ambient thermal gradient drift!
    sigma_u2b_rti_uv = 0.340  # 3.1x noisier than differential U2A because U2B lacks a wet thermal partner!
    u2b_threshold_uv = 3.5 * sigma_u2b_rti_uv  # 1.19 uV RTI (corresponds to ~1.25 um of CaCO3 on Reference arm)

    ref_gate_results = []
    for label, ratio in ref_fouling_levels:
        d_sense_um = rng.uniform(8.0, 22.0, size=n_trials_per_level)
        d_ref_um = ratio * d_sense_um
        # Simulated signals with physical hydrodynamic + electronic noise
        v3w_diff_uv = uv_preamp_per_um_1hz * (d_sense_um - d_ref_um) + rng.normal(0.0, sigma_total_rti_uv_1hz, size=n_trials_per_level)
        v3w_ref_u2b_uv = uv_preamp_per_um_1hz * d_ref_um + rng.normal(0.0, sigma_u2b_rti_uv, size=n_trials_per_level)
        # Also IDE_REF capacitive shift relative to temperature-compensated NaCl conductivity curve (sigma_ide_ref = 0.45 um equiv)
        d_ref_ide_est_um = d_ref_um + rng.normal(0.0, 0.42, size=n_trials_per_level)

        # Dual-channel hardware fault detector triggers if:
        # (a) |v3w_ref_u2b_uv| > u2b_threshold_uv (1.19 uV RTI, ~1.25 um scale on Ref RTD), OR
        # (b) |d_ref_ide_est_um| > 1.35 um on IDE_REF
        flagged = (np.abs(v3w_ref_u2b_uv) > u2b_threshold_uv) | (np.abs(d_ref_ide_est_um) > 1.35)
        n_flagged = int(np.sum(flagged))

        # Uncorrected thickness estimation error if unflagged:
        d_est_uncorrected_um = v3w_diff_uv / uv_preamp_per_um_1hz
        rel_err_uncorrected_pct = float(np.mean(np.abs(d_est_uncorrected_um - d_sense_um) / d_sense_um) * 100.0)

        ref_gate_results.append({
            "scenario": label,
            "ref_to_sense_fouling_ratio": ratio,
            "mean_sense_thickness_um": round(float(np.mean(d_sense_um)), 2),
            "mean_ref_thickness_um": round(float(np.mean(d_ref_um)), 2),
            "trials": n_trials_per_level,
            "hardware_u2b_plus_ideref_flagged_count": n_flagged,
            "detection_rate_pct": round(100.0 * n_flagged / n_trials_per_level, 1),
            "uncorrected_differential_mae_pct": round(rel_err_uncorrected_pct, 2),
        })

    # ========================================================================
    # 4. PHYSICAL VS CONVENTIONAL BASELINE FALSIFIER SIMULATION (N=120 RUNS)
    # ========================================================================
    # Compare:
    # - Baseline_EIS_RTD_Flow (HunStat2 4-freq EIS + Pt100 RTD + Flow meter, 3w disabled)
    # - OTDB_APW_005_Active (HunStat2 4-freq EIS + Dual-AD8421 3w Thermal Bridge + Flow)
    # Across two simulated benchtop regimes:
    # Regime 1: Pure CaCO3 crystallization fouling (0 to 25 um) at fixed/swept T (22-30 C) and flow (30-60 mL/min)
    # Regime 2: Orthogonal Confounder Sweep — Soluble NaCl conductivity step (10 mM -> 20 mM) + T (22 -> 30 C) + Flow (30 -> 60 mL/min) concurrent with CaCO3 scaling (0 to 25 um)
    n_bench = 120
    d_true_r1 = rng.uniform(0.0, 25.0, size=n_bench)
    # In Regime 1 (known ionic background), calibrated 4-freq EIS + RTD + Flow is slightly cleaner than 3w thermal because capacitive/double-layer SNR is higher than 0603 RTD thermal spreading:
    d_pred_baseline_r1 = d_true_r1 + rng.normal(0.0, 0.32, size=n_bench)
    d_pred_otdb_r1 = d_true_r1 + rng.normal(0.0, 0.58, size=n_bench)

    # In Regime 2 (unannounced 10 mM -> 20 mM NaCl ionic strength step + 22->30 C + 30->60 mL/min flow),
    # electrical impedance experiences a bulk- vs boundary-layer conductivity shift that mimics or masks mineral scale (~4.8 um equivalent bias),
    # whereas the 3w thermal impedance of the solid CaCO3 layer on the glass-passivated Pt100 RTD is insensitive to bulk NaCl molarity (k_water changes by <0.2% between 10 mM and 20 mM NaCl!):
    d_true_r2 = rng.uniform(2.0, 25.0, size=n_bench)
    nacl_step_bias_um = rng.uniform(-5.2, 5.8, size=n_bench)
    d_pred_baseline_r2 = d_true_r2 + nacl_step_bias_um + rng.normal(0.0, 0.45, size=n_bench)
    d_pred_otdb_r2 = d_true_r2 + 0.08 * nacl_step_bias_um + rng.normal(0.0, 0.65, size=n_bench)

    rmse_base_r1 = float(np.sqrt(np.mean((d_pred_baseline_r1 - d_true_r1) ** 2)))
    rmse_otdb_r1 = float(np.sqrt(np.mean((d_pred_otdb_r1 - d_true_r1) ** 2)))
    rmse_base_r2 = float(np.sqrt(np.mean((d_pred_baseline_r2 - d_true_r2) ** 2)))
    rmse_otdb_r2 = float(np.sqrt(np.mean((d_pred_otdb_r2 - d_true_r2) ** 2)))

    return {
        "document_id": "SNR_AND_REFERENCE_CONTAMINATION_FALSIFIER_005",
        "transducer_part": "Vishay Beyschlag PTS060301B100RP100 (100 Ohm Pt100 0603 SMD RTD on Alumina with Glass Passivation)",
        "bridge_drive_parameters": {
            "i_branch_rms_ma": 12.0,
            "i_bridge_total_rms_ma": 24.0,
            "p_element_avg_mw": 14.4,
            "f_1w_primary_hz": 1.0,
            "f_3w_primary_hz": 3.0,
            "f_1w_fast_hz": 8.0,
            "f_3w_fast_hz": 24.0,
            "inamp_gain": 100.0,
            "lockin_integration_window_s": 10.0,
            "enbw_hz": 0.05,
        },
        "sensitivity_and_noise_summary": {
            "sensitivity_preamp_1hz_uv_per_um": round(uv_preamp_per_um_1hz, 4),
            "sensitivity_adc_g100_1hz_mv_per_um": round(uv_preamp_per_um_1hz * gain_inamp / 1000.0, 4),
            "sensitivity_preamp_8hz_uv_per_um": round(uv_preamp_per_um_8hz, 4),
            "sensitivity_adc_g100_8hz_mv_per_um": round(uv_preamp_per_um_8hz * gain_inamp / 1000.0, 4),
            "electronic_noise_rti_1hz_uv_rms": round(electronic_noise_rti_uv_1hz, 5),
            "total_hydrodynamic_plus_electronic_noise_rti_1hz_uv_rms": round(sigma_total_rti_uv_1hz, 4),
            "total_hydrodynamic_plus_electronic_noise_rti_8hz_uv_rms": round(sigma_total_rti_uv_8hz, 4),
            "limit_of_detection_3sigma_1hz_um": round(lod_3sigma_um_1hz, 3),
            "limit_of_quantification_10sigma_1hz_um": round(loq_10sigma_um_1hz, 3),
            "limit_of_detection_3sigma_8hz_um": round(lod_3sigma_um_8hz, 3),
            "limit_of_quantification_10sigma_8hz_um": round(loq_10sigma_um_8hz, 3),
        },
        "snr_vs_thickness_table": snr_table,
        "reference_contamination_hardware_falsifier": {
            "hardware_witness_proposed": "Added U2B (second AD8421BRZ, G=100) measuring BRIDGE_MID_REF against a 2 ppm/K Susumu RG1608 fixed divider into AD5941 AIN2, plus TMUX1108 routing of IDE_REF into AD5941 EIS port.",
            "u2b_single_ended_noise_rti_uv_rms": sigma_u2b_rti_uv,
            "u2b_3p5sigma_alarm_threshold_uv_rti": round(u2b_threshold_uv, 3),
            "minimum_detectable_reference_scale_thickness_um": 1.25,
            "sub_micron_blind_spot_remains": True,
            "operational_deployment_prohibition": "PROHIBITED without periodic clean-flush tare or mechanical isolation verification: while U2B + IDE_REF catches >=96% of reference contamination when d_f,ref >= 1.25 um (>=20% leak ratio), trace reference contamination below 1.0 um (2% to 10% leak ratio, 0.2 to 1.0 um on Ref RTD) produces single-ended 3w shifts below U2B's uncompensated convective noise floor (0.34 uV RTI), yielding only 1.0% to 48.0% detection. Autonomous operational deployment remains prohibited until physical dual-channel isolation is validated on the bench.",
            "scenario_results": ref_gate_results,
        },
        "benchtop_regime_comparison_predictions": {
            "regime_1_single_salt_scaling_rmse_um": {
                "hunstat2_eis_rtd_flow_baseline_rmse_um": round(rmse_base_r1, 3),
                "otdb_apw_005_3w_plus_eis_rmse_um": round(rmse_otdb_r1, 3),
                "winner": "HunStat2_EIS_RTD_Flow_Baseline (3w thermal adds convective variance without needed orthogonality when ionic composition is fixed)"
            },
            "regime_2_orthogonal_nacl_conductivity_confounder_rmse_um": {
                "hunstat2_eis_rtd_flow_baseline_rmse_um": round(rmse_base_r2, 3),
                "otdb_apw_005_3w_plus_eis_rmse_um": round(rmse_otdb_r2, 3),
                "winner": "OTDB_APW_005_Active (3w solid-film phonon bottleneck is invariant to 10->20 mM NaCl bulk conductivity steps that confound EIS)"
            },
            "decisive_physical_falsifier_rule": "If across N >= 12 paired gravimetric/profilometric CaCO3 runs with a 10 mM -> 20 mM NaCl confounder step, adding the 3w thermal bridge fails to reduce thickness RMSE by at least 35% (p < 0.01) over HunStat2 4-frequency EIS + Pt100 RTD + flow sensing alone, REJECT the OTDB-APW thermal bridge complexity permanently."
        }
    }


if __name__ == "__main__":
    print(json.dumps(run_snr_and_reference_falsifier(), indent=2))
