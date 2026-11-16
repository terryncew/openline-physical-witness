/*
 * OTDB-APW — Engineering Revision B (`OTDB-APW` Rev B)
 * Hardware-Independent ANSI C99 Embedded Firmware Core Header (`otdb_apw_firmware_core.h`)
 * Target MCU: STMicroelectronics STM32G474RET6 (170 MHz Cortex-M4F) + AD5941 AFE + AD5683R DAC.
 * NOTE: Compiled and verified on host x86_64 via GCC (`libotdb_firmware.so`);
 * hardware-independent C99 core with zero OS/malloc dependencies.
 */
#ifndef OTDB_APW_FIRMWARE_CORE_H
#define OTDB_APW_FIRMWARE_CORE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    FW_STATUS_OK_VERIFIED_IDENTIFIABLE = 0,
    FW_STATUS_ABSTAIN_PINHOLE_SHORT_HOLD = 1,
    FW_STATUS_ABSTAIN_TURBULENT_STRIPPING = 2,
    FW_STATUS_ABSTAIN_THICK_CAKE_SATURATION = 3,
    FW_STATUS_ABSTAIN_REF_CAVITY_FOULED_OR_DRIFT = 4,
    FW_STATUS_ABSTAIN_LOW_CONDUCTIVITY_SIDEBAND_FLOOR = 5
} otdb_fw_status_t;

typedef struct {
    double v3w_lo_re_uv;
    double v3w_lo_im_uv;
    double v3w_hi_re_uv;
    double v3w_hi_im_uv;
    double v1w_prt_tap_uv;
    double y_lo_re_us;
    double y_lo_im_us;
    double y_hi_re_us;
    double y_hi_im_us;
    double dy_lo_re_us;
    double dy_lo_im_us;
    double dy_hi_re_us;
    double dy_hi_im_us;
    double v_sb_lo_uv;
    double v_sb_hi_uv;
    double sigma_v3w_uv;
} otdb_demod_frame_t;

typedef struct {
    int32_t status_code;
    int32_t abstained;
    uint16_t wagner_dac_i_code;
    uint16_t wagner_dac_q_code;
    double est_fouling_um;
    double est_flow_u_m_s;
    double est_conductivity_s_m;
    double est_temp_delta_k;
    double fisher_min_eig_proxy;
    double recommended_f_th_lo_hz;
    double recommended_f_th_hi_hz;
} otdb_fw_decision_t;

/* 1. Digital Quadrature Lock-In Demodulator on raw 16-bit signed ADC samples */
void otdb_fw_lockin_demodulate_16bit(
    const int16_t *adc_samples,
    int32_t n_samples,
    double sample_rate_hz,
    double target_freq_hz,
    double lsb_uv,
    double *out_re_uv,
    double *out_im_uv
);

/* 2. Wagner Active Ground 16-Bit DAC Nulling Step */
void otdb_fw_wagner_null_step(
    double v1w_bridge_residual_re_uv,
    double v1w_bridge_residual_im_uv,
    uint16_t *io_dac_i_code,
    uint16_t *io_dac_q_code
);

/* 3. Complete Embedded State Estimation, Integrity Checks & Safe Abstention Gate */
void otdb_fw_evaluate_frame(
    const otdb_demod_frame_t *frame,
    double cal_r0_ohm,
    double cal_c_par_pf,
    otdb_fw_decision_t *out_decision
);

#ifdef __cplusplus
}
#endif

#endif /* OTDB_APW_FIRMWARE_CORE_H */
