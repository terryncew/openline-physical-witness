/* SPDX-License-Identifier: MIT
 * Host-testable math for 2-channel coherent lock-in; no hardware driver or safety certification.
 */
#ifndef OTDB005_LOCKIN_CORE_H
#define OTDB005_LOCKIN_CORE_H
#include <stdint.h>
#include <stdbool.h>

typedef enum {OTDB005_ACQ_OK=0,OTDB005_ACQ_HOLD_INVALID_CONFIG,
   OTDB005_ACQ_HOLD_SAMPLE_MISSING,OTDB005_ACQ_HOLD_NONFINITE,
   OTDB005_ACQ_HOLD_INCOMPLETE,OTDB005_ACQ_HOLD_INDEX} otdb005_acq_status_t;

typedef struct {float sin3_sum[2],cos3_sum[2]; uint32_t samples; uint32_t desired_samples;
  float sample_hz,drive_hz; otdb005_acq_status_t status;} otdb005_lockin_state_t;

typedef struct {float inphase_uv_rms,quadrature_uv_rms,magnitude_uv_rms;} otdb005_phasor_t;

typedef struct {otdb005_phasor_t differential, independent_reference;
  otdb005_acq_status_t disposition;} otdb005_lockin_window_t;

otdb005_acq_status_t otdb005_lockin_init(otdb005_lockin_state_t *s,
 float sample_rate_hz,float drive_hz,uint32_t window_samples);
otdb005_acq_status_t otdb005_lockin_push(otdb005_lockin_state_t *s,
 uint32_t sample_index,float diff_uv,float reference_uv,bool reference_observed);
otdb005_lockin_window_t otdb005_lockin_finish(const otdb005_lockin_state_t *s);
#endif
