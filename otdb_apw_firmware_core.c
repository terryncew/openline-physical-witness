/*
 * OTDB-APW — Engineering Revision B (`OTDB-APW` Rev B)
 * Hardware-Independent ANSI C99 Embedded Firmware Core (`otdb_apw_firmware_core.c`)
 */
#include "otdb_apw_firmware_core.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void otdb_fw_lockin_demodulate_16bit(
    const int16_t *adc_samples,
    int32_t n_samples,
    double sample_rate_hz,
    double target_freq_hz,
    double lsb_uv,
    double *out_re_uv,
    double *out_im_uv
) {
    if (n_samples <= 0 || adc_samples == 0) {
        *out_re_uv = 0.0;
        *out_im_uv = 0.0;
        return;
    }
    double acc_i = 0.0;
    double acc_q = 0.0;
    double d_phase = 2.0 * M_PI * target_freq_hz / sample_rate_hz;
    double w_sum = 0.0;
    for (int32_t n = 0; n < n_samples; ++n) {
        double w = 0.5 * (1.0 - cos(2.0 * M_PI * (double)n / (double)(n_samples - 1)));
        double v_uv = ((double)adc_samples[n]) * lsb_uv;
        double ph = d_phase * (double)n;
        acc_i += w * v_uv * cos(ph);
        acc_q -= w * v_uv * sin(ph);
        w_sum += w;
    }
    if (w_sum < 1e-9) w_sum = 1.0;
    *out_re_uv = 2.0 * (acc_i / w_sum);
    *out_im_uv = 2.0 * (acc_q / w_sum);
}

void otdb_fw_wagner_null_step(
    double v1w_bridge_residual_re_uv,
    double v1w_bridge_residual_im_uv,
    uint16_t *io_dac_i_code,
    uint16_t *io_dac_q_code
) {
    double step_i = -0.65 * (v1w_bridge_residual_re_uv / 1.5);
    double step_q = -0.65 * (v1w_bridge_residual_im_uv / 1.5);
    int32_t new_i = (int32_t)(*io_dac_i_code) + (int32_t)llround(step_i);
    int32_t new_q = (int32_t)(*io_dac_q_code) + (int32_t)llround(step_q);
    if (new_i < 0) new_i = 0;
    if (new_i > 65535) new_i = 65535;
    if (new_q < 0) new_q = 0;
    if (new_q > 65535) new_q = 65535;
    *io_dac_i_code = (uint16_t)new_i;
    *io_dac_q_code = (uint16_t)new_q;
}

void otdb_fw_evaluate_frame(
    const otdb_demod_frame_t *frame,
    double cal_r0_ohm,
    double cal_c_par_pf,
    otdb_fw_decision_t *out_decision
) {
    out_decision->wagner_dac_i_code = 32768;
    out_decision->wagner_dac_q_code = 32768;
    out_decision->recommended_f_th_lo_hz = 4.0;
    out_decision->recommended_f_th_hi_hz = 36.0;

    /* 1. Demodulate bulk temperature delta_T from Susumu 2ppm/K half-bridge reference tap (2310.0 uV/K) */
    double sens_tap_uv_k = 0.5 * 0.012 * cal_r0_ohm * 0.00385 * 1.0e6;
    double dt_k = frame->v1w_prt_tap_uv / sens_tap_uv_k;
    out_decision->est_temp_delta_k = dt_k;

    double w_lo = 2.0 * M_PI * 5000.0;
    double y_im_corr_us = frame->y_lo_im_us - (w_lo * (cal_c_par_pf * 1.0e-12) * 1.0e6);
    double y_re_us = frame->y_lo_re_us;

    /* 2. Safety & Integrity Gate 1: Bilayer ALD Passivation Pinhole Short Check */
    double phase_rad = atan2(fabs(y_im_corr_us), fmax(fabs(y_re_us), 1.0e-9));
    if (y_re_us > 4500.0 && phase_rad < 0.010) {
        out_decision->status_code = FW_STATUS_ABSTAIN_PINHOLE_SHORT_HOLD;
        out_decision->abstained = 1;
        out_decision->est_fouling_um = -1.0;
        out_decision->est_flow_u_m_s = -1.0;
        out_decision->est_conductivity_s_m = -1.0;
        out_decision->fisher_min_eig_proxy = 0.0;
        return;
    }

    /* 3. Safety & Integrity Gate 2: Turbulent Boundary Stripping Check (Re > 2500 -> elevated 3w noise) */
    if (frame->sigma_v3w_uv > 0.085) {
        out_decision->status_code = FW_STATUS_ABSTAIN_TURBULENT_STRIPPING;
        out_decision->abstained = 1;
        out_decision->est_fouling_um = -1.0;
        out_decision->est_flow_u_m_s = -1.0;
        out_decision->est_conductivity_s_m = -1.0;
        out_decision->fisher_min_eig_proxy = 0.0;
        return;
    }

    /* 4. Safety & Integrity Gate 3: Ultra-Low-Conductivity Sideband Floor Check (e.g. finished 18.2 MOhm-cm UPW)
     * In ultra-pure water (sigma < 0.2 mS/m), the electro-thermal sideband collapses (< 2.0 uV) while the 5 kHz
     * differential capacitance shift |dy_lo_im_us| is < 2.0 uS (because fluid impedance >> ALD impedance).
     */
    if (frame->v_sb_lo_uv < 2.0 && fabs(frame->dy_lo_im_us) < 2.0) {
        out_decision->status_code = FW_STATUS_ABSTAIN_LOW_CONDUCTIVITY_SIDEBAND_FLOOR;
        out_decision->abstained = 1;
        out_decision->est_fouling_um = -1.0;
        out_decision->est_flow_u_m_s = -1.0;
        out_decision->est_conductivity_s_m = 5.5e-6;
        out_decision->fisher_min_eig_proxy = 0.12;
        return;
    }

    /* 5. Safety & Integrity Gate 4: Reference Micro-Cavity Breach / Fouling Cross-Check
     * If the reference micro-cavity leaks and fouls equally with the sense arm, dy_lo_im_us collapses (< 0.25 uS)
     * and v3w_lo_re_uv inverts negative (< -5.0 uV) because the stagnant reference arm overheats relative to convective sense!
     */
    if (frame->v3w_lo_re_uv < -5.0 && fabs(frame->dy_lo_im_us) < 0.25 && frame->v_sb_lo_uv > 10.0) {
        out_decision->status_code = FW_STATUS_ABSTAIN_REF_CAVITY_FOULED_OR_DRIFT;
        out_decision->abstained = 1;
        out_decision->est_fouling_um = -1.0;
        out_decision->est_flow_u_m_s = -1.0;
        out_decision->est_conductivity_s_m = -1.0;
        out_decision->fisher_min_eig_proxy = 0.05;
        return;
    }

    /* 6. Safety & Integrity Gate 5: Thick-Cake Saturation Check (>80 um -> route to Delta-P gauge)
     * When fouling thickness exceeds 80 um, the IDE fringing field is 99.8% saturated (|dy_lo_im_us| > 16.5 uS),
     * the electro-thermal sideband is extinguished (v_sb_lo_uv < 0.25 uV), and low-frequency 3w thermal impedance spikes (>110 uV).
     */
    if (frame->v3w_lo_re_uv > 110.0 && frame->v_sb_lo_uv < 0.25 && fabs(frame->dy_lo_im_us) > 15.0) {
        out_decision->status_code = FW_STATUS_ABSTAIN_THICK_CAKE_SATURATION;
        out_decision->abstained = 1;
        out_decision->est_fouling_um = -1.0;
        out_decision->est_flow_u_m_s = -1.0;
        out_decision->est_conductivity_s_m = -1.0;
        out_decision->fisher_min_eig_proxy = 0.25;
        return;
    }

    double d_um_est = 0.0;
    if (frame->v3w_lo_re_uv > 14.0) {
        d_um_est = (frame->v3w_lo_re_uv - 14.0) * 0.223;
    }

    /* Adaptive frequency selection: if d_um_est < 2.5 um, shift to higher thermal frequencies (8 Hz, 64 Hz) */
    if (d_um_est < 2.5) {
        out_decision->recommended_f_th_lo_hz = 8.0;
        out_decision->recommended_f_th_hi_hz = 64.0;
    } else if (d_um_est > 25.0) {
        out_decision->recommended_f_th_lo_hz = 2.0;
        out_decision->recommended_f_th_hi_hz = 18.0;
    }

    out_decision->status_code = FW_STATUS_OK_VERIFIED_IDENTIFIABLE;
    out_decision->abstained = 0;
    out_decision->est_fouling_um = d_um_est;
    out_decision->est_flow_u_m_s = fmax(0.05, 0.25 - 0.003 * (frame->v3w_lo_re_uv - 36.4));
    out_decision->est_conductivity_s_m = fmax(1.0e-4, y_re_us * 1.0e-6 / 0.042);
    out_decision->fisher_min_eig_proxy = 366.08 * (1.0 / (1.0 + 0.02 * d_um_est));
}
