/* SPDX-License-Identifier: MIT */
#include "lockin_core.h"
#include <math.h>
#include <stddef.h>
#include <string.h>

#define OTDB005_PI 3.14159265358979323846264338327950288

otdb005_acq_status_t otdb005_lockin_init(otdb005_lockin_state_t *s,
 float fs,float f_drive,uint32_t n) {
 if (!s) return OTDB005_ACQ_HOLD_INVALID_CONFIG;
 memset(s,0,sizeof(*s));
 if (!isfinite(fs)||!isfinite(f_drive)||fs<=0||f_drive<=0||
     fs<=6*f_drive||n<32||n>10000000U ||
     fabs((double)n*f_drive/fs-round((double)n*f_drive/fs))>1e-6) {
  s->status=OTDB005_ACQ_HOLD_INVALID_CONFIG;
  return s->status;
 }
 s->sample_hz=fs;s->drive_hz=f_drive;s->desired_samples=n;
 return OTDB005_ACQ_OK;
}

otdb005_acq_status_t otdb005_lockin_push(otdb005_lockin_state_t *s,
 uint32_t k,float diff,float ref,bool reference_observed) {
 if (!s) return OTDB005_ACQ_HOLD_INVALID_CONFIG;
 if (s->status!=OTDB005_ACQ_OK) return s->status;
 if (s->samples>=s->desired_samples||k!=s->samples) {
  s->status=OTDB005_ACQ_HOLD_INDEX;return s->status;
 }
 if(!reference_observed) {
  s->status=OTDB005_ACQ_HOLD_SAMPLE_MISSING;return s->status;
 }
 if(!isfinite(diff)||!isfinite(ref)) {
  s->status=OTDB005_ACQ_HOLD_NONFINITE;return s->status;
 }
 double phase=2.0*OTDB005_PI*3.0*(double)k*(double)s->drive_hz/(double)s->sample_hz;
 float sn=(float)sin(phase),cs=(float)cos(phase);
 s->sin3_sum[0]+=diff*sn;s->cos3_sum[0]+=diff*cs;
 s->sin3_sum[1]+=ref*sn;s->cos3_sum[1]+=ref*cs;
 s->samples++;
 return OTDB005_ACQ_OK;
}

static otdb005_phasor_t compute(const otdb005_lockin_state_t *s,unsigned ch) {
 float scale=1.4142135623730951f/(float)s->samples;
 otdb005_phasor_t p={s->sin3_sum[ch]*scale,s->cos3_sum[ch]*scale,0};
 p.magnitude_uv_rms=hypotf(p.inphase_uv_rms,p.quadrature_uv_rms);
 return p;
}

otdb005_lockin_window_t otdb005_lockin_finish(const otdb005_lockin_state_t *s) {
 otdb005_lockin_window_t out={0};out.disposition=OTDB005_ACQ_HOLD_INCOMPLETE;
 if (!s||s->status!=OTDB005_ACQ_OK||s->samples!=s->desired_samples||s->samples==0) {
  if(s && s->status!=OTDB005_ACQ_OK)out.disposition=s->status;
  return out;
 }
 out.differential=compute(s,0);out.independent_reference=compute(s,1);
 out.disposition=OTDB005_ACQ_OK;return out;
}
