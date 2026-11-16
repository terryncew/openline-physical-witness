/* SPDX-License-Identifier: MIT
 * OTDB-APW research-only signal interlock. NOT a hardware safety certification.
 * Independent witness availability and real-world thresholds remain unverified.
 */
#ifndef OTDB005_REFERENCE_GUARD_H
#define OTDB005_REFERENCE_GUARD_H
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OTDB005_HOLD_UNCALIBRATED = 0,
    OTDB005_HOLD_MISSING_CHANNEL = 1,
    OTDB005_HOLD_STALE_MEASUREMENT = 2,
    OTDB005_HOLD_NONFINITE = 3,
    OTDB005_HOLD_REFERENCE_DRIFT = 4,
    OTDB005_HOLD_TEMPERATURE = 5,
    OTDB005_HOLD_OUT_OF_RANGE = 6,
    OTDB005_RESEARCH_ESTIMATE_ALLOWED = 7
} otdb005_gate_result_t;

typedef struct {
    float ref_3w_re_uv;
    float ref_3w_im_uv;
    float temperature_c;
    uint64_t monotonic_sample_ms;
    bool independent_reference_present;
    bool thermal_channel_calibrated;
} otdb005_reference_sample_t;

typedef struct {
    float baseline_3w_re_uv;
    float baseline_3w_im_uv;
    float baseline_temperature_c;
    float allowed_reference_vector_drift_uv;
    float temperature_change_limit_c;
    float max_abs_reference_uv;
    uint64_t max_sample_age_ms;
    bool calibrated;
} otdb005_gate_config_t;

otdb005_gate_result_t otdb005_guard_evaluate(
    const otdb005_gate_config_t *config,
    const otdb005_reference_sample_t *sample,
    uint64_t now_ms
);
const char *otdb005_gate_name(otdb005_gate_result_t code);
#endif
