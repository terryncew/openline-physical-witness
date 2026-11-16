/* RESEARCH-ONLY MATH CORE: lacks hardware drivers, ADC configuration, DMA/PIO, calibration, power-up and build/flash project. Not deployable firmware. */
/*
 * OTDB-APW 005 — Seeed Studio XIAO RP2040 + HunStat2 (AD5941) Firmware
 * Phase-Locked 1w/3w Thermal-Wave Bridge & Dual-Channel Reference Integrity Acquisition
 * License: MIT
 */

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#define SAMPLE_RATE_HZ       512U
#define LUT_LEN_1HZ          512U
#define LUT_LEN_8HZ          64U
#define LOCKIN_WINDOW_SAMPLES 5120U  /* 10.0 s coherent integration window */

/* Hardware Pin Assignments on Seeed Studio XIAO RP2040 */
#define PIN_SPI_CS_AD5941    1U
#define PIN_SPI_CS_DAC1      2U
#define PIN_SPI_CS_DAC2      3U
#define PIN_GPIO0_SYNC_PIO   4U
#define PIN_TMUX1108_A0      5U
#define PIN_TMUX1108_A1      6U
#define PIN_TMUX1108_EN      7U
#define PIN_SPI_SCK          8U
#define PIN_SPI_MISO         9U
#define PIN_SPI_MOSI         10U

/* AD5941 AFE ADC Mux Channel Codes */
#define AD5941_MUX_AIN0_U2A_DIFF   0x01U  /* U2A: G=100 (BRIDGE_MID_SENSE - BRIDGE_MID_REF) */
#define AD5941_MUX_AIN1_VCM_REF    0x02U  /* U3B: VCM = 1.110 V Reference */
#define AD5941_MUX_AIN2_U2B_REF    0x03U  /* U2B: G=100 (BRIDGE_MID_REF - SUSUMU_DIV_MID) */
#define AD5941_MUX_AIN3_BRIDGE_EXC 0x04U  /* U3A/Q1: Bridge Top Excitation Monitor */

typedef struct {
    float i_1w_diff;
    float q_1w_diff;
    float i_3w_diff;
    float q_3w_diff;
    float i_3w_ref_u2b;
    float q_3w_ref_u2b;
    uint32_t sample_count;
} LockInAccumulators_t;

typedef struct {
    float v3w_diff_rti_uv;
    float v3w_ref_u2b_rti_uv;
    float eis_sense_mag_ohm[4];
    float eis_sense_phase_deg[4];
    float eis_ref_mag_ohm[4];
    bool  reference_contamination_alarm;
} Otdb005TelemetryFrame_t;

static uint16_t g_dac_sine_lut_1hz[LUT_LEN_1HZ];
static LockInAccumulators_t g_acc;

void otdb005_init_sine_lut(uint16_t dc_mid_code, uint16_t amp_code) {
    for (uint32_t k = 0; k < LUT_LEN_1HZ; ++k) {
        float theta = (2.0f * 3.14159265358979323846f * (float)k) / (float)LUT_LEN_1HZ;
        float val = (float)dc_mid_code + (float)amp_code * sinf(theta);
        if (val < 0.0f) val = 0.0f;
        if (val > 65535.0f) val = 65535.0f;
        g_dac_sine_lut_1hz[k] = (uint16_t)(val + 0.5f);
    }
}

void otdb005_process_sample_isr(uint32_t k_idx, int32_t adc_u2a_code, int32_t adc_u2b_code) {
    const float lsb_rti_uv = (1820000.0f / 65536.0f) / 100.0f; /* 1.82V FS, 16-bit, G=100 -> 0.2777 uV/LSB RTI */
    float v_diff_uv = (float)(adc_u2a_code - 32768) * lsb_rti_uv;
    float v_ref_uv  = (float)(adc_u2b_code - 32768) * lsb_rti_uv;

    float theta_1w = (2.0f * 3.14159265358979323846f * (float)(k_idx % LUT_LEN_1HZ)) / (float)LUT_LEN_1HZ;
    float theta_3w = 3.0f * theta_1w;

    g_acc.i_1w_diff    += v_diff_uv * sinf(theta_1w);
    g_acc.q_1w_diff    += v_diff_uv * cosf(theta_1w);
    g_acc.i_3w_diff    += v_diff_uv * sinf(theta_3w);
    g_acc.q_3w_diff    += v_diff_uv * cosf(theta_3w);
    g_acc.i_3w_ref_u2b += v_ref_uv  * sinf(theta_3w);
    g_acc.q_3w_ref_u2b += v_ref_uv  * cosf(theta_3w);
    g_acc.sample_count += 1U;
}

void otdb005_finalize_window(Otdb005TelemetryFrame_t *out) {
    float n = (float)(g_acc.sample_count > 0U ? g_acc.sample_count : 1U);
    float scale_rms = 1.41421356f / n;
    out->v3w_diff_rti_uv = scale_rms * sqrtf(
        g_acc.i_3w_diff * g_acc.i_3w_diff + g_acc.q_3w_diff * g_acc.q_3w_diff
    );
    out->v3w_ref_u2b_rti_uv = scale_rms * sqrtf(
        g_acc.i_3w_ref_u2b * g_acc.i_3w_ref_u2b + g_acc.q_3w_ref_u2b * g_acc.q_3w_ref_u2b
    );
    /* Trigger hardware reference-contamination alarm if U2B 3w shift > 1.19 uV RTI (3.5 sigma) */
    out->reference_contamination_alarm = (out->v3w_ref_u2b_rti_uv > 1.19f);
    g_acc = (LockInAccumulators_t){0};
}
