/* SPDX-License-Identifier: MIT
 * Research-only tri-arm reference-witness screening: not deployed firmware.
 * No hardware, calibration or field-detection performance has been validated.
 */
#ifndef OTDB_TRIARM_WITNESS_H
#define OTDB_TRIARM_WITNESS_H
#include <stdbool.h>
#include <stdint.h>

#define OTDB_TRIARM_FREQ_COUNT 2

typedef enum {
    OTDB006_HOLD_UNCALIBRATED = 0,
    OTDB006_HOLD_NO_INDEPENDENT_GUARD,
    OTDB006_HOLD_STALE_OR_REPLAYED,
    OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG,
    OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED,
    OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED,
    OTDB006_HOLD_MIXED_FOULING_UNRESOLVED,
    OTDB006_HOLD_MAINTENANCE_REQUIRED,
    OTDB006_OBSERVATION_CONSISTENT_ONLY
} otdb006_disposition_t;

typedef struct {
    /* These thresholds are illustrative, not sensor-specific validated values. */
    double baseline_ref_guard_re_uv[OTDB_TRIARM_FREQ_COUNT];
    double baseline_ref_guard_im_uv[OTDB_TRIARM_FREQ_COUNT];
    double thermal_drift_limit_uv[OTDB_TRIARM_FREQ_COUNT];
    double baseline_ref_guard_ide_us;
    double ide_drift_limit_us;
    double max_temperature_gap_c;
    double max_conductivity_gap_fraction;
    double max_flow_gap_fraction;
    double clean_turbidity_ntu;
    double max_turbidity_change_ntu;
    uint64_t max_sample_age_ms;
    uint64_t max_blank_age_ms;
    uint32_t calibration_epoch;
    bool clean_baseline_externally_confirmed;
} otdb006_limits_t;

typedef struct {
    uint32_t calibration_epoch;
    uint64_t sequence;
    uint64_t captured_at_ms;
    uint64_t independent_blank_at_ms;
    bool separate_raw_reference_and_guard_channels;
    bool guarded_coupon_inspected_clean;
    bool reference_measurement_present;
    bool protected_guard_measurement_present;
    bool ide_reference_guard_measurement_present;
    bool turbidity_measurement_present;
    double ref_guard_re_uv[OTDB_TRIARM_FREQ_COUNT];
    double ref_guard_im_uv[OTDB_TRIARM_FREQ_COUNT];
    double ref_guard_ide_us;
    double reference_temperature_c;
    double guard_temperature_c;
    double reference_conductivity_ms_cm;
    double guard_conductivity_ms_cm;
    double reference_flow_ml_min;
    double guard_flow_ml_min;
    double turbidity_ntu;
} otdb006_observation_t;

typedef struct {
    uint64_t last_sequence;
    bool observed_any;
    bool contamination_latched;
} otdb006_monitor_state_t;

otdb006_disposition_t otdb006_check(
    otdb006_monitor_state_t *state,
    const otdb006_limits_t *limits,
    const otdb006_observation_t *obs,
    uint64_t now_ms
);
const char *otdb006_disposition_name(otdb006_disposition_t disposition);
#endif
