/* Host-only adversarial unit test. Synthetic phasors; no physical measurements. */
#include "../firmware/reference_guard.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void expect(otdb005_gate_result_t got, otdb005_gate_result_t want) {
    if (got != want) {
        fprintf(stderr, "expected %s, got %s\n", otdb005_gate_name(want), otdb005_gate_name(got));
        assert(got==want);
    }
}
int main(void) {
    const uint64_t now=10000;
    otdb005_gate_config_t cfg={.baseline_3w_re_uv=2.0f,
       .baseline_3w_im_uv=0.0f, .baseline_temperature_c=25.0f,
       .allowed_reference_vector_drift_uv=0.50f,
       .temperature_change_limit_c=2.0f,.max_abs_reference_uv=40.0f,
       .max_sample_age_ms=500,.calibrated=true};
    otdb005_reference_sample_t s={.ref_3w_re_uv=2.1f,.ref_3w_im_uv=0.05f,
       .temperature_c=25.1f,.monotonic_sample_ms=9900,
       .independent_reference_present=true,.thermal_channel_calibrated=true};
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_RESEARCH_ESTIMATE_ALLOWED);
    cfg.calibrated=false;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_UNCALIBRATED);
    cfg.calibrated=true; s.independent_reference_present=false;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_MISSING_CHANNEL);
    s.independent_reference_present=true; s.thermal_channel_calibrated=false;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_MISSING_CHANNEL);
    s.thermal_channel_calibrated=true; s.monotonic_sample_ms=9000;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_STALE_MEASUREMENT);
    s.monotonic_sample_ms=10100;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_STALE_MEASUREMENT);
    s.monotonic_sample_ms=9900; s.ref_3w_re_uv=NAN;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_NONFINITE);
    s.ref_3w_re_uv=2.1f; s.ref_3w_im_uv=0.8f;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_REFERENCE_DRIFT);
    s.ref_3w_im_uv=0.05f; s.ref_3w_re_uv=3.0f;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_REFERENCE_DRIFT);
    s.ref_3w_re_uv=2.1f; s.temperature_c=29.5f;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_TEMPERATURE);
    s.temperature_c=25.1f; cfg.max_abs_reference_uv=0.5f;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_OUT_OF_RANGE);
    cfg.max_abs_reference_uv=40.0f; cfg.allowed_reference_vector_drift_uv=0;
    expect(otdb005_guard_evaluate(&cfg,&s,now),OTDB005_HOLD_OUT_OF_RANGE);
    expect(otdb005_guard_evaluate(NULL,&s,now),OTDB005_HOLD_UNCALIBRATED);
    puts("PASS: 13 deterministic adversarial host guard cases (synthetic; no ADC hardware)");
    return 0;
}
