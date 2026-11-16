/* SPDX-License-Identifier: MIT
 * No I/O, controls, measurements or calibration in this module.
 * All observations are supplied from outside; raw channel independence must
 * be established by independently tested hardware and firmware, not by this API.
 */
#include "triarm_witness.h"
#include <math.h>
#include <stddef.h>

static bool safe_positive(double x) {return isfinite(x) && x > 0.0;}
static double rel_gap(double a, double b) {
    return fabs(a-b) / fmax(fmax(fabs(a),fabs(b)),1e-12);
}
static bool valid_limits(const otdb006_limits_t *c) {
    if(!c || !c->clean_baseline_externally_confirmed || c->calibration_epoch==0 ||
       c->max_sample_age_ms==0 || c->max_blank_age_ms==0 ||
       !safe_positive(c->ide_drift_limit_us) ||
       !safe_positive(c->max_temperature_gap_c) ||
       !safe_positive(c->max_conductivity_gap_fraction) ||
       !safe_positive(c->max_flow_gap_fraction) ||
       !safe_positive(c->max_turbidity_change_ntu) ||
       !isfinite(c->clean_turbidity_ntu) || c->clean_turbidity_ntu<0.0 ||
       !isfinite(c->baseline_ref_guard_ide_us)) return false;
    for(unsigned i=0;i<OTDB_TRIARM_FREQ_COUNT;++i){
        if(!isfinite(c->baseline_ref_guard_re_uv[i]) ||
           !isfinite(c->baseline_ref_guard_im_uv[i]) ||
           !safe_positive(c->thermal_drift_limit_uv[i])) return false;
    }
    return true;
}

otdb006_disposition_t otdb006_check(otdb006_monitor_state_t *s,
    const otdb006_limits_t *c,const otdb006_observation_t *o,uint64_t now_ms) {
    if(!s || !c || !o || !c->clean_baseline_externally_confirmed ||
       c->calibration_epoch==0) return OTDB006_HOLD_UNCALIBRATED;
    if(s->contamination_latched) return OTDB006_HOLD_MAINTENANCE_REQUIRED;
    if(!valid_limits(c)) return OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG;
    if(o->calibration_epoch!=c->calibration_epoch || o->sequence==0 ||
       (s->observed_any && o->sequence<=s->last_sequence) ||
       o->captured_at_ms>now_ms ||
       now_ms-o->captured_at_ms>c->max_sample_age_ms ||
       o->independent_blank_at_ms>o->captured_at_ms ||
       o->captured_at_ms-o->independent_blank_at_ms>c->max_blank_age_ms)
        return OTDB006_HOLD_STALE_OR_REPLAYED;
    /* Record even failed observation sequence, preventing a failed packet from
       becoming an apparent fresh success on replay. Persistence is not implemented. */
    s->last_sequence=o->sequence;
    s->observed_any=true;
    if(!o->separate_raw_reference_and_guard_channels ||
       !o->guarded_coupon_inspected_clean ||
       !o->reference_measurement_present ||
       !o->protected_guard_measurement_present ||
       !o->ide_reference_guard_measurement_present ||
       !o->turbidity_measurement_present)
        return OTDB006_HOLD_NO_INDEPENDENT_GUARD;
    if(!isfinite(o->ref_guard_ide_us) ||
       !isfinite(o->reference_temperature_c) ||
       !isfinite(o->guard_temperature_c) ||
       !isfinite(o->reference_conductivity_ms_cm) ||
       !isfinite(o->guard_conductivity_ms_cm) ||
       !isfinite(o->reference_flow_ml_min) ||
       !isfinite(o->guard_flow_ml_min) ||
       !isfinite(o->turbidity_ntu) ||
       o->reference_conductivity_ms_cm<=0.0 || o->guard_conductivity_ms_cm<=0.0 ||
       o->reference_flow_ml_min<=0.0 || o->guard_flow_ml_min<=0.0 ||
       o->turbidity_ntu<0.0) return OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG;
    for(unsigned i=0;i<OTDB_TRIARM_FREQ_COUNT;++i) {
        if(!isfinite(o->ref_guard_re_uv[i]) || !isfinite(o->ref_guard_im_uv[i]))
            return OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG;
    }
    if(fabs(o->reference_temperature_c-o->guard_temperature_c)>
          c->max_temperature_gap_c ||
       rel_gap(o->reference_conductivity_ms_cm,o->guard_conductivity_ms_cm)>
          c->max_conductivity_gap_fraction ||
       rel_gap(o->reference_flow_ml_min,o->guard_flow_ml_min)>
          c->max_flow_gap_fraction)
        return OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED;
    /* Two complex thermal signatures plus an independent electrical witness.
       Detectability below the empirically derived measurement noise is unknown. */
    bool suspect=fabs(o->ref_guard_ide_us-c->baseline_ref_guard_ide_us)>
                      c->ide_drift_limit_us;
    for(unsigned i=0;i<OTDB_TRIARM_FREQ_COUNT;++i){
       double delta=hypot(o->ref_guard_re_uv[i]-c->baseline_ref_guard_re_uv[i],
                          o->ref_guard_im_uv[i]-c->baseline_ref_guard_im_uv[i]);
       if(delta>c->thermal_drift_limit_uv[i]) suspect=true;
    }
    if(suspect) {
        s->contamination_latched=true;
        return OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED;
    }
    /* Mixed suspended solids may make the mineral-only estimator unsuitable.
       No estimate is calculated or trusted by this gate. */
    if(fabs(o->turbidity_ntu-c->clean_turbidity_ntu)>
         c->max_turbidity_change_ntu)
        return OTDB006_HOLD_MIXED_FOULING_UNRESOLVED;
    return OTDB006_OBSERVATION_CONSISTENT_ONLY;
}

const char *otdb006_disposition_name(otdb006_disposition_t d){
    switch(d){
      case OTDB006_HOLD_UNCALIBRATED:return "HOLD_UNCALIBRATED";
      case OTDB006_HOLD_NO_INDEPENDENT_GUARD:return "HOLD_NO_INDEPENDENT_GUARD";
      case OTDB006_HOLD_STALE_OR_REPLAYED:return "HOLD_STALE_OR_REPLAYED";
      case OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG:return "HOLD_BAD_NUMERIC_OR_CONFIG";
      case OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED:return "HOLD_ENVIRONMENT_NOT_MATCHED";
      case OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED:return "HOLD_REFERENCE_FOULING_SUSPECTED";
      case OTDB006_HOLD_MIXED_FOULING_UNRESOLVED:return "HOLD_MIXED_FOULING_UNRESOLVED";
      case OTDB006_HOLD_MAINTENANCE_REQUIRED:return "HOLD_MAINTENANCE_REQUIRED";
      case OTDB006_OBSERVATION_CONSISTENT_ONLY:return "OBSERVATION_CONSISTENT_ONLY";
      default:return "HOLD_UNKNOWN";
    }
}
