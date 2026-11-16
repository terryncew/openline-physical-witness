/* SPDX-License-Identifier: MIT. Synthetic amplitudes only. */
#include "../firmware/lockin_core.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#define PI 3.14159265358979323846

static void check_frequency(float fd) {
 otdb005_lockin_state_t s;
 assert(otdb005_lockin_init(&s,512.f,fd,5120)==OTDB005_ACQ_OK);
 for(unsigned k=0;k<5120;k++) {
  float a=(float)(2.0*sin(2*PI*3*fd*k/512.0));
  float b=(float)(3.0*cos(2*PI*3*fd*k/512.0));
  assert(otdb005_lockin_push(&s,k,a,b,true)==OTDB005_ACQ_OK);
 }
 otdb005_lockin_window_t v=otdb005_lockin_finish(&s);
 assert(v.disposition==OTDB005_ACQ_OK);
 assert(fabs(v.differential.magnitude_uv_rms-2.0/sqrt(2))<0.002);
 assert(fabs(v.independent_reference.magnitude_uv_rms-3.0/sqrt(2))<0.002);
 assert(fabs(v.differential.quadrature_uv_rms)<0.002);
 assert(fabs(v.independent_reference.inphase_uv_rms)<0.002);
}
int main(void) {
 check_frequency(1.f);check_frequency(8.f);
 otdb005_lockin_state_t s;
 assert(otdb005_lockin_init(&s,512.f,100.f,5120)==OTDB005_ACQ_HOLD_INVALID_CONFIG);
 assert(otdb005_lockin_init(&s,512.f,1.f,100)==OTDB005_ACQ_HOLD_INVALID_CONFIG);
 assert(otdb005_lockin_init(&s,512.f,1.f,5120)==OTDB005_ACQ_OK);
 assert(otdb005_lockin_finish(&s).disposition==OTDB005_ACQ_HOLD_INCOMPLETE);
 assert(otdb005_lockin_push(&s,0,1,1,false)==OTDB005_ACQ_HOLD_SAMPLE_MISSING);
 assert(otdb005_lockin_finish(&s).disposition==OTDB005_ACQ_HOLD_SAMPLE_MISSING);
 assert(otdb005_lockin_init(&s,512.f,1.f,5120)==OTDB005_ACQ_OK);
 assert(otdb005_lockin_push(&s,1,1,1,true)==OTDB005_ACQ_HOLD_INDEX);
 assert(otdb005_lockin_init(&s,512.f,1.f,5120)==OTDB005_ACQ_OK);
 assert(otdb005_lockin_push(&s,0,NAN,1,true)==OTDB005_ACQ_HOLD_NONFINITE);
 puts("PASS: two coherent frequencies, two channels, and invalid/missing/out-of-order cases");
}
