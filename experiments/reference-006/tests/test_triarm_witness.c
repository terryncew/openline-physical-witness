/* SPDX-License-Identifier: MIT. Host-only constructed cases; not measured faults. */
#include "../firmware/triarm_witness.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static void check(otdb006_disposition_t got,otdb006_disposition_t want){
    if(got!=want){fprintf(stderr,"expected %s; got %s\n",otdb006_disposition_name(want),otdb006_disposition_name(got));assert(got==want);}
}
static otdb006_limits_t config(void){return (otdb006_limits_t){
 .baseline_ref_guard_re_uv={0.0,0.0},.baseline_ref_guard_im_uv={0.0,0.0},
 .thermal_drift_limit_uv={0.5,0.5},.baseline_ref_guard_ide_us=0.0,
 .ide_drift_limit_us=0.5,.max_temperature_gap_c=0.5,
 .max_conductivity_gap_fraction=0.05,.max_flow_gap_fraction=0.05,
 .clean_turbidity_ntu=0.5,.max_turbidity_change_ntu=1.0,
 .max_sample_age_ms=500,.max_blank_age_ms=2000,
 .calibration_epoch=7,.clean_baseline_externally_confirmed=true};}
static otdb006_observation_t reading(void){return (otdb006_observation_t){
 .calibration_epoch=7,.sequence=1,.captured_at_ms=9900,
 .independent_blank_at_ms=9000,.separate_raw_reference_and_guard_channels=true,
 .guarded_coupon_inspected_clean=true,.reference_measurement_present=true,
 .protected_guard_measurement_present=true,.ide_reference_guard_measurement_present=true,
 .turbidity_measurement_present=true,.ref_guard_re_uv={0.02,0.03},
 .ref_guard_im_uv={0.01,0.02},.ref_guard_ide_us=0.03,
 .reference_temperature_c=25,.guard_temperature_c=25.1,
 .reference_conductivity_ms_cm=10,.guard_conductivity_ms_cm=10.1,
 .reference_flow_ml_min=30,.guard_flow_ml_min=30.5,.turbidity_ntu=0.55};}
int main(void){
 const uint64_t now=10000;
 otdb006_limits_t c=config();otdb006_observation_t o=reading();
 otdb006_monitor_state_t st={0};
 check(otdb006_check(&st,&c,&o,now),OTDB006_OBSERVATION_CONSISTENT_ONLY);
 check(otdb006_check(&st,&c,&o,now),OTDB006_HOLD_STALE_OR_REPLAYED);
 o.sequence=2; o.ref_guard_re_uv[0]=0.7;
 check(otdb006_check(&st,&c,&o,now),OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED);
 o.sequence=3;o.ref_guard_re_uv[0]=0.02;
 check(otdb006_check(&st,&c,&o,now),OTDB006_HOLD_MAINTENANCE_REQUIRED);
 #define CASE(mut,expected) do{otdb006_monitor_state_t state={0};c=config();o=reading();mut;check(otdb006_check(&state,&c,&o,now),expected);}while(0)
 CASE(c.clean_baseline_externally_confirmed=false,OTDB006_HOLD_UNCALIBRATED);
 CASE(o.separate_raw_reference_and_guard_channels=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.guarded_coupon_inspected_clean=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.reference_measurement_present=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.protected_guard_measurement_present=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.ide_reference_guard_measurement_present=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.turbidity_measurement_present=false,OTDB006_HOLD_NO_INDEPENDENT_GUARD);
 CASE(o.calibration_epoch=6,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.sequence=0,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.captured_at_ms=12000,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.captured_at_ms=9000,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.independent_blank_at_ms=11000,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.independent_blank_at_ms=100,OTDB006_HOLD_STALE_OR_REPLAYED);
 CASE(o.reference_temperature_c=NAN,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(o.ref_guard_im_uv[1]=INFINITY,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(c.thermal_drift_limit_uv[1]=0.0,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(o.reference_conductivity_ms_cm=0,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(o.guard_temperature_c=27.0,OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED);
 CASE(o.guard_conductivity_ms_cm=8.0,OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED);
 CASE(o.guard_flow_ml_min=36.0,OTDB006_HOLD_ENVIRONMENT_NOT_MATCHED);
 CASE(o.ref_guard_im_uv[1]=0.75,OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED);
 CASE(o.ref_guard_re_uv[1]=0.7,OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED);
 CASE(o.ref_guard_ide_us=0.6,OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED);
 CASE(o.turbidity_ntu=3.5,OTDB006_HOLD_MIXED_FOULING_UNRESOLVED);
 CASE(c.max_temperature_gap_c=NAN,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(o.reference_flow_ml_min=-1.0,OTDB006_HOLD_BAD_NUMERIC_OR_CONFIG);
 CASE(o.ref_guard_re_uv[0]=0.5001; o.ref_guard_im_uv[0]=0.0,OTDB006_HOLD_REFERENCE_FOULING_SUSPECTED);
 CASE(o.ref_guard_re_uv[0]=0.50; o.ref_guard_im_uv[0]=0.0,OTDB006_OBSERVATION_CONSISTENT_ONLY);
 #undef CASE
 puts("PASS: reference screening; replay; two-frequency phase; IDE; environment; mixed-water; fault latch (constructed inputs)");
 return 0;
}
