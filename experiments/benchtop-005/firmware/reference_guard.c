/* SPDX-License-Identifier: MIT
 * Fail-closed precondition check for an independently observed reference phasor.
 * No hardware I/O. No demonstrated physical fault-detection probability.
 */
#include "reference_guard.h"
#include <math.h>
#include <stddef.h>

static bool finite2(float x, float y) {return isfinite(x) && isfinite(y);}

otdb005_gate_result_t otdb005_guard_evaluate(
    const otdb005_gate_config_t *c,
    const otdb005_reference_sample_t *s,
    uint64_t now_ms
) {
    if (!c || !s || !c->calibrated) return OTDB005_HOLD_UNCALIBRATED;
    if (!s->independent_reference_present || !s->thermal_channel_calibrated)
        return OTDB005_HOLD_MISSING_CHANNEL;
    if (now_ms < s->monotonic_sample_ms ||
        now_ms - s->monotonic_sample_ms > c->max_sample_age_ms ||
        c->max_sample_age_ms == 0)
        return OTDB005_HOLD_STALE_MEASUREMENT;
    if (!finite2(c->baseline_3w_re_uv, c->baseline_3w_im_uv) ||
        !finite2(s->ref_3w_re_uv, s->ref_3w_im_uv) ||
        !finite2(s->temperature_c, c->baseline_temperature_c))
        return OTDB005_HOLD_NONFINITE;
    if (!isfinite(c->allowed_reference_vector_drift_uv) ||
        !isfinite(c->temperature_change_limit_c) ||
        !isfinite(c->max_abs_reference_uv) ||
        c->allowed_reference_vector_drift_uv <= 0 ||
        c->temperature_change_limit_c <= 0 ||
        c->max_abs_reference_uv <= 0)
        return OTDB005_HOLD_OUT_OF_RANGE;
    if (fabsf(s->temperature_c - c->baseline_temperature_c) >
        c->temperature_change_limit_c) return OTDB005_HOLD_TEMPERATURE;
    if (hypotf(s->ref_3w_re_uv, s->ref_3w_im_uv) > c->max_abs_reference_uv)
        return OTDB005_HOLD_OUT_OF_RANGE;
    /* Compare complex phasors, not just amplitudes: phase-only drift is a fault. */
    if (hypotf(s->ref_3w_re_uv - c->baseline_3w_re_uv,
               s->ref_3w_im_uv - c->baseline_3w_im_uv) >
        c->allowed_reference_vector_drift_uv)
        return OTDB005_HOLD_REFERENCE_DRIFT;
    return OTDB005_RESEARCH_ESTIMATE_ALLOWED;
}

const char *otdb005_gate_name(otdb005_gate_result_t code) {
    switch(code) {
    case OTDB005_HOLD_UNCALIBRATED: return "HOLD_UNCALIBRATED";
    case OTDB005_HOLD_MISSING_CHANNEL: return "HOLD_MISSING_CHANNEL";
    case OTDB005_HOLD_STALE_MEASUREMENT: return "HOLD_STALE_MEASUREMENT";
    case OTDB005_HOLD_NONFINITE: return "HOLD_NONFINITE";
    case OTDB005_HOLD_REFERENCE_DRIFT: return "HOLD_REFERENCE_DRIFT";
    case OTDB005_HOLD_TEMPERATURE: return "HOLD_TEMPERATURE";
    case OTDB005_HOLD_OUT_OF_RANGE: return "HOLD_OUT_OF_RANGE";
    case OTDB005_RESEARCH_ESTIMATE_ALLOWED: return "RESEARCH_ESTIMATE_ALLOWED";
    default: return "HOLD_UNKNOWN";
    }
}
