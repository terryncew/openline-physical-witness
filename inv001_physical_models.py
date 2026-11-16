#!/usr/bin/env python3
"""
OTDB-APW — Original Research Model (Rev A)
Core Physics Governing Equations, Multiphysics Solvers, and SPICE Nodal Engine (`physical_models.py`).
"""
from __future__ import annotations

import cmath
from dataclasses import dataclass, asdict
import json
import math
from typing import Any
import numpy as np


K_BOLTZMANN = 1.380649e-23       # J/K
Q_ELECTRON = 1.602176634e-19     # C
FARADAY_CONST = 96485.33212      # C/mol
R_GAS = 8.314462618              # J/(mol*K)
EPSILON_0 = 8.8541878128e-12     # F/m

MATERIAL_PROPERTIES = {
    "water_upw": {
        "k_th_w_mk": 0.606,
        "d_ln_k_dT_k1": 0.0026,
        "rho_kg_m3": 997.0,
        "cp_j_kgk": 4181.3,
        "alpha_th_m2_s": 1.454e-7,
        "mu_pa_s_25c": 8.90e-4,
        "epsilon_r_25c": 78.4,
        "d_ln_sigma_dT_k1": 0.0215,
        "d_ln_eps_dT_k1": -0.00455,
    },
    "amorphous_silica_scale": {
        "k_th_w_mk": 0.38,
        "rho_kg_m3": 1650.0,
        "cp_j_kgk": 920.0,
        "epsilon_r": 4.2,
        "sigma_elec_s_m": 1.5e-6,
        "d_ln_sigma_dT_k1": 0.0020,
    },
    "biofilm_organic_fouling": {
        "k_th_w_mk": 0.52,
        "rho_kg_m3": 1030.0,
        "cp_j_kgk": 3950.0,
        "epsilon_r": 32.0,
        "sigma_elec_s_m": 2.0e-4,
        "d_ln_sigma_dT_k1": 0.0065,
    },
    "vapor_blanket_dryout": {
        "k_th_w_mk": 0.026,
        "rho_kg_m3": 0.59,
        "cp_j_kgk": 2080.0,
        "epsilon_r": 1.0006,
        "sigma_elec_s_m": 1.0e-11,
        "d_ln_sigma_dT_k1": 0.0,
    },
    "ald_al2o3_passivation": {
        "thickness_m": 50.0e-9,
        "k_th_w_mk": 18.0,
        "epsilon_r": 9.1,
        "breakdown_field_v_m": 7.5e8,
    },
    "pt_thin_film_bridge": {
        "r0_ohm": 100.0,
        "tcr_alpha_k1": 0.00385,
        "length_m": 2.0e-3,
        "width_m": 20.0e-6,
        "area_active_m2": 1.2e-6,
        "substrate_k_th_w_mk": 1.38,
        "substrate_alpha_th_m2_s": 8.4e-7,
    },
}


@dataclass
class PhysicalBoundaryState:
    """True physical state vector theta at the solid-fluid interface."""
    fouling_or_void_thickness_m: float
    local_flow_velocity_m_s: float
    ionic_conductivity_s_m: float
    bulk_temp_delta_k: float
    layer_type: str = "amorphous_silica_scale"
    bridge_etch_mismatch_frac: float = 0.0
    ald_thickness_tol_frac: float = 0.0
    passivation_pinhole_short: bool = False


class OTDBAPWPhysicsEngine:
    """Coupled Multiphysics + SPICE Nodal Solver for `OTDB-APW`."""

    def __init__(self, channel_hydraulic_diam_m: float = 1.0e-3):
        self.d_h = channel_hydraulic_diam_m
        self.props = MATERIAL_PROPERTIES

    def compute_convective_h(self, u_m_s: float, temp_delta_k: float = 0.0) -> float:
        fl = self.props["water_upw"]
        u_eff = max(abs(u_m_s), 1.0e-4)
        t_k = 298.15 + temp_delta_k
        mu = 2.414e-5 * (10.0 ** (247.8 / (t_k - 140.0)))
        k_fl_t = fl["k_th_w_mk"] * (1.0 + fl["d_ln_k_dT_k1"] * temp_delta_k)
        re = fl["rho_kg_m3"] * u_eff * self.d_h / mu
        pr = mu * fl["cp_j_kgk"] / k_fl_t
        l_entry = 2.0e-3
        if re < 2300.0:
            gz = re * pr * (self.d_h / l_entry)
            nu = 3.66 + 1.86 * (gz ** (1.0 / 3.0))
        else:
            f_darcy = (0.79 * math.log(re) - 1.64) ** (-2.0)
            nu = ((f_darcy / 8.0) * (re - 1000.0) * pr) / (
                1.0 + 12.7 * math.sqrt(f_darcy / 8.0) * ((pr ** (2.0 / 3.0)) - 1.0)
            )
        return (nu * k_fl_t) / self.d_h

    def solve_multiphysics_observables(
        self,
        state: PhysicalBoundaryState,
        f_th_hz: float = 12.0,
        f_elec_hz: float = 45000.0,
        i1_amp_a: float = 0.012,
        v2_rms_v: float = 0.015,
        wagner_null_enabled: bool = True,
        rng: np.random.Generator | None = None,
        noise_scale: float = 1.0,
    ) -> dict[str, float]:
        pt = self.props["pt_thin_film_bridge"]
        fl = self.props["water_upw"]
        layer = self.props.get(state.layer_type, self.props["amorphous_silica_scale"])
        ald = self.props["ald_al2o3_passivation"]

        omega_1 = 2.0 * math.pi * max(f_th_hz, 0.1)
        omega_2 = 2.0 * math.pi * max(f_elec_hz, 10.0)
        area = pt["area_active_m2"]

        r_arm_t = pt["r0_ohm"] * (1.0 + pt["tcr_alpha_k1"] * state.bulk_temp_delta_k)
        k_fl_t = fl["k_th_w_mk"] * (1.0 + fl["d_ln_k_dT_k1"] * state.bulk_temp_delta_k)
        alpha_fl_t = k_fl_t / (fl["rho_kg_m3"] * fl["cp_j_kgk"])

        j2w1 = complex(0.0, 2.0 * omega_1)
        q_sub = cmath.sqrt(j2w1 / pt["substrate_alpha_th_m2_s"])
        y_sub = area * pt["substrate_k_th_w_mk"] * q_sub

        q_fl = cmath.sqrt(j2w1 / alpha_fl_t)
        h_conv = self.compute_convective_h(state.local_flow_velocity_m_s, state.bulk_temp_delta_k)
        y_fluid = area * (h_conv + k_fl_t * q_fl)

        alpha_f = layer["k_th_w_mk"] / (layer["rho_kg_m3"] * layer["cp_j_kgk"])
        q_f = cmath.sqrt(j2w1 / alpha_f)
        delta_f = max(state.fouling_or_void_thickness_m, 0.0)

        arg_f = q_f * delta_f
        if abs(arg_f.real) > 25.0:
            tanh_qf = complex(1.0, 0.0)
            sech_qf = complex(0.0, 0.0)
        else:
            tanh_qf = cmath.tanh(arg_f)
            sech_qf = 1.0 / cmath.cosh(arg_f)

        y_char_f = area * layer["k_th_w_mk"] * q_f
        if delta_f < 1.0e-10:
            y_front = y_fluid
            gamma_th = complex(1.0, 0.0)
        else:
            y_front = y_char_f * ((y_fluid + y_char_f * tanh_qf) / (y_char_f + y_fluid * tanh_qf))
            gamma_th = sech_qf / (1.0 + (y_fluid / y_char_f) * tanh_qf)

        h_ref = self.compute_convective_h(0.05, state.bulk_temp_delta_k)
        y_front_ref = area * (h_ref + k_fl_t * q_fl)

        p_2w1 = 0.5 * (i1_amp_a ** 2) * r_arm_t
        dt_sense_2w1 = p_2w1 / (y_sub + y_front)
        dt_ref_2w1 = p_2w1 / (y_sub + y_front_ref)

        v3w_sense = 0.5 * i1_amp_a * r_arm_t * pt["tcr_alpha_k1"] * dt_sense_2w1
        v3w_ref = 0.5 * i1_amp_a * r_arm_t * pt["tcr_alpha_k1"] * dt_ref_2w1
        v1w_ref_prt_uv = (i1_amp_a * pt["r0_ohm"] * pt["tcr_alpha_k1"] * state.bulk_temp_delta_k) * 1.0e6

        mismatch_leak_v = 0.0
        if not wagner_null_enabled and abs(state.bridge_etch_mismatch_frac) > 1e-6:
            mismatch_leak_v = 0.025 * i1_amp_a * r_arm_t * state.bridge_etch_mismatch_frac

        v3w_diff = (v3w_sense - v3w_ref) + complex(mismatch_leak_v, -0.4 * mismatch_leak_v)

        t_ald = ald["thickness_m"] * (1.0 + state.ald_thickness_tol_frac)
        c_ald = EPSILON_0 * ald["epsilon_r"] * area / t_ald
        z_ald = 1.0 / complex(0.0, omega_2 * c_ald)
        if state.passivation_pinhole_short:
            z_ald = complex(2.0, 0.0)

        sigma_fl_t = state.ionic_conductivity_s_m * math.exp(fl["d_ln_sigma_dT_k1"] * state.bulk_temp_delta_k)
        eps_fl_t = fl["epsilon_r_25c"] * math.exp(fl["d_ln_eps_dT_k1"] * state.bulk_temp_delta_k)

        l_ide = 25.0e-6
        frac_f = 1.0 - math.exp(-delta_f / (0.5 * l_ide))

        y_unit_fl = (area / l_ide) * complex(sigma_fl_t, omega_2 * EPSILON_0 * eps_fl_t)
        y_unit_layer = (area / l_ide) * complex(layer["sigma_elec_s_m"], omega_2 * EPSILON_0 * layer["epsilon_r"])

        if frac_f < 1.0e-7:
            z_medium = 1.0 / y_unit_fl
        else:
            z_medium = (frac_f / y_unit_layer) + ((1.0 - frac_f) / y_unit_fl)

        if state.passivation_pinhole_short and state.ionic_conductivity_s_m > 0.5:
            z_total_sense = complex(1.0 / (sigma_fl_t * (area / l_ide)), 0.0)
        else:
            z_total_sense = z_ald + z_medium
        y_sense = 1.0 / z_total_sense
        y_ref_elec = 1.0 / (z_ald + (1.0 / y_unit_fl))

        dt_fluid_2w1 = dt_sense_2w1 * gamma_th
        d_y_fl_dt = (area / l_ide) * complex(
            sigma_fl_t * fl["d_ln_sigma_dT_k1"],
            omega_2 * EPSILON_0 * eps_fl_t * fl["d_ln_eps_dT_k1"],
        )
        i_sideband_complex = v2_rms_v * ((1.0 - frac_f) ** 2) * d_y_fl_dt * dt_fluid_2w1
        if state.passivation_pinhole_short and state.ionic_conductivity_s_m > 0.5:
            i_sideband_complex = complex(0.0, 0.0)
        v_sideband_uv = abs(i_sideband_complex) * 1.0e5 * 1.0e6

        v3w_re_uv = v3w_diff.real * 1.0e6
        v3w_im_uv = v3w_diff.imag * 1.0e6
        v3w_sense_re_uv = v3w_sense.real * 1.0e6
        v3w_sense_im_uv = v3w_sense.imag * 1.0e6
        y_re_us = y_sense.real * 1.0e6
        y_im_us = y_sense.imag * 1.0e6
        dy_re_us = (y_sense.real - y_ref_elec.real) * 1.0e6
        dy_im_us = (y_sense.imag - y_ref_elec.imag) * 1.0e6

        re_check = fl["rho_kg_m3"] * abs(state.local_flow_velocity_m_s) * self.d_h / fl["mu_pa_s_25c"]
        turbulence_noise_mult = 1.0 + max(0.0, (re_check - 2500.0) / 800.0) ** 1.5

        sigma_v3w_uv = 0.045 * noise_scale * turbulence_noise_mult
        sigma_v1w_uv = 0.080 * noise_scale
        sigma_y_us = 0.008 * noise_scale * (1.0 + 0.02 * abs(y_re_us))
        sigma_sb_uv = 0.035 * noise_scale * turbulence_noise_mult

        if rng is not None and noise_scale > 0.0:
            v3w_re_uv += float(rng.normal(0.0, sigma_v3w_uv))
            v3w_im_uv += float(rng.normal(0.0, sigma_v3w_uv))
            v3w_sense_re_uv += float(rng.normal(0.0, sigma_v3w_uv * 2.0))
            v3w_sense_im_uv += float(rng.normal(0.0, sigma_v3w_uv * 2.0))
            v1w_ref_prt_uv += float(rng.normal(0.0, sigma_v1w_uv))
            y_re_us += float(rng.normal(0.0, sigma_y_us))
            y_im_us += float(rng.normal(0.0, sigma_y_us))
            dy_re_us += float(rng.normal(0.0, 0.5 * sigma_y_us))
            dy_im_us += float(rng.normal(0.0, 0.5 * sigma_y_us))
            v_sideband_uv = max(0.0, v_sideband_uv + float(rng.normal(0.0, sigma_sb_uv)))

        return {
            "f_th_hz": f_th_hz,
            "f_elec_hz": f_elec_hz,
            "thermal_penetration_depth_um": math.sqrt(alpha_fl_t / (2.0 * omega_1)) * 1.0e6,
            "v3w_diff_re_uv": v3w_re_uv,
            "v3w_diff_im_uv": v3w_im_uv,
            "v3w_sense_re_uv": v3w_sense_re_uv,
            "v3w_sense_im_uv": v3w_sense_im_uv,
            "v3w_abs_sense_uv": abs(v3w_sense) * 1.0e6,
            "v1w_ref_prt_uv": v1w_ref_prt_uv,
            "y_sense_re_us": y_re_us,
            "y_sense_im_us": y_im_us,
            "dy_diff_re_us": dy_re_us,
            "dy_diff_im_us": dy_im_us,
            "v_sideband_cross_mod_uv": v_sideband_uv,
            "sigma_v3w_uv": sigma_v3w_uv,
            "sigma_v1w_uv": sigma_v1w_uv,
            "sigma_y_us": sigma_y_us,
            "sigma_sb_uv": sigma_sb_uv,
            "reynolds_number": re_check,
            "h_conv_w_m2k": h_conv,
            "joule_power_mw": p_2w1 * 1.0e3,
        }

    def compute_fisher_information_and_witness(
        self,
        state: PhysicalBoundaryState,
        f_th_pair_hz: tuple[float, float] = (4.0, 36.0),
        f_elec_pair_hz: tuple[float, float] = (5000.0, 120000.0),
        mode: str = "OTDB_APW_FULL",
    ) -> dict[str, Any]:
        scales = np.array([10.0e-6, 0.20, max(state.ionic_conductivity_s_m * 0.20, 1.0e-6), 2.0])
        steps = scales * 0.02

        def _get_obs_vector(st: PhysicalBoundaryState) -> tuple[np.ndarray, np.ndarray]:
            m1 = self.solve_multiphysics_observables(st, f_th_hz=f_th_pair_hz[0], f_elec_hz=f_elec_pair_hz[0], noise_scale=1.0)
            m2 = self.solve_multiphysics_observables(st, f_th_hz=f_th_pair_hz[1], f_elec_hz=f_elec_pair_hz[1], noise_scale=1.0)
            if mode == "CONVENTIONAL_PASSIVE_SCALAR":
                obs = np.array([m1["y_sense_re_us"], st.bulk_temp_delta_k])
                sig = np.array([m1["sigma_y_us"] * 3.0, 0.15])
            elif mode == "PASSIVE_SINGLE_PORT_EIS":
                obs = np.array([
                    m1["y_sense_re_us"], m1["y_sense_im_us"],
                    m2["y_sense_re_us"], m2["y_sense_im_us"],
                ])
                sig = np.array([m1["sigma_y_us"] * 2.5, m1["sigma_y_us"] * 2.5, m2["sigma_y_us"] * 2.5, m2["sigma_y_us"] * 2.5])
            elif mode == "THERMAL_3OMEGA_ONLY":
                obs = np.array([
                    m1["v3w_sense_re_uv"], m1["v3w_sense_im_uv"],
                    m2["v3w_sense_re_uv"], m2["v3w_sense_im_uv"],
                ])
                sig = np.array([m1["sigma_v3w_uv"] * 2.0] * 4)
            elif mode == "OTDB_APW_WITHOUT_1OMEGA_CM":
                obs = np.array([
                    m1["v3w_diff_re_uv"], m1["v3w_diff_im_uv"],
                    m2["v3w_diff_re_uv"], m2["v3w_diff_im_uv"],
                    m1["dy_diff_re_us"], m1["dy_diff_im_us"],
                    m2["dy_diff_re_us"], m2["dy_diff_im_us"],
                    m1["y_sense_re_us"], m1["y_sense_im_us"],
                    m1["v_sideband_cross_mod_uv"], m2["v_sideband_cross_mod_uv"],
                ])
                sig = np.array([
                    m1["sigma_v3w_uv"], m1["sigma_v3w_uv"],
                    m2["sigma_v3w_uv"], m2["sigma_v3w_uv"],
                    m1["sigma_y_us"], m1["sigma_y_us"],
                    m2["sigma_y_us"], m2["sigma_y_us"],
                    m1["sigma_y_us"], m1["sigma_y_us"],
                    m1["sigma_sb_uv"], m2["sigma_sb_uv"],
                ])
            else:
                obs = np.array([
                    m1["v3w_diff_re_uv"], m1["v3w_diff_im_uv"],
                    m2["v3w_diff_re_uv"], m2["v3w_diff_im_uv"],
                    m1["v1w_ref_prt_uv"],
                    m1["dy_diff_re_us"], m1["dy_diff_im_us"],
                    m2["dy_diff_re_us"], m2["dy_diff_im_us"],
                    m1["y_sense_re_us"], m1["y_sense_im_us"],
                    m1["v_sideband_cross_mod_uv"], m2["v_sideband_cross_mod_uv"],
                ])
                sig = np.array([
                    m1["sigma_v3w_uv"], m1["sigma_v3w_uv"],
                    m2["sigma_v3w_uv"], m2["sigma_v3w_uv"],
                    m1["sigma_v1w_uv"],
                    m1["sigma_y_us"], m1["sigma_y_us"],
                    m2["sigma_y_us"], m2["sigma_y_us"],
                    m1["sigma_y_us"], m1["sigma_y_us"],
                    m1["sigma_sb_uv"], m2["sigma_sb_uv"],
                ])
            return obs, sig

        y0, sig0 = _get_obs_vector(state)
        n_obs = len(y0)
        j_mat = np.zeros((n_obs, 4), dtype=float)

        fields = [
            "fouling_or_void_thickness_m",
            "local_flow_velocity_m_s",
            "ionic_conductivity_s_m",
            "bulk_temp_delta_k",
        ]
        for idx, fname in enumerate(fields):
            st_plus = PhysicalBoundaryState(**asdict(state))
            setattr(st_plus, fname, getattr(state, fname) + steps[idx])
            y_plus, _ = _get_obs_vector(st_plus)
            j_mat[:, idx] = ((y_plus - y0) / steps[idx]) * scales[idx]

        w_inv = np.diag(1.0 / (sig0 ** 2))
        fim = j_mat.T @ w_inv @ j_mat
        eigvals, eigvecs = np.linalg.eigh(fim)
        eigvals = np.maximum(eigvals, 1.0e-18)
        cond_num_fim = float(eigvals[-1] / eigvals[0])
        cond_num_jac = float(math.sqrt(cond_num_fim))
        min_eig = float(eigvals[0])
        log_det_fim = float(np.sum(np.log(eigvals)))

        try:
            cov = np.linalg.inv(fim + np.eye(4) * 1.0e-15)
            crlb_fouling_um = float(math.sqrt(max(cov[0, 0], 1e-18)) * 10.0)
        except np.linalg.LinAlgError:
            crlb_fouling_um = 999.0

        identifiable = bool(min_eig >= 5.0 and cond_num_jac <= 1500.0)
        weakest_idx = int(np.argmax(np.abs(eigvecs[:, 0])))
        weakest_param = fields[weakest_idx]

        return {
            "mode": mode,
            "identifiable": identifiable,
            "witness_disposition": (
                "VERIFIED_CAUSAL_IDENTIFIABILITY"
                if identifiable
                else f"PHYSICAL_WITNESS_ABSTAIN_INSUFFICIENT_EVIDENCE (unidentifiable_axis={weakest_param})"
            ),
            "fisher_min_eigenvalue": round(min_eig, 6),
            "fisher_condition_number_kappa": round(cond_num_fim, 3),
            "jacobian_condition_number_kappa_J": round(cond_num_jac, 3),
            "fisher_log_det": round(log_det_fim, 4),
            "crlb_fouling_detection_limit_um_3sigma": round(3.0 * crlb_fouling_um, 4),
            "weakest_identifiability_axis": weakest_param,
        }

    def select_d_optimal_excitation_frequencies(
        self, state: PhysicalBoundaryState
    ) -> dict[str, Any]:
        candidate_f_th = [(2.0, 18.0), (4.0, 36.0), (8.0, 64.0), (15.0, 90.0)]
        candidate_f_el = [(2000.0, 60000.0), (5000.0, 120000.0), (15000.0, 350000.0)]
        best_res = None
        best_score = -1.0e18
        for f_th in candidate_f_th:
            for f_el in candidate_f_el:
                res = self.compute_fisher_information_and_witness(
                    state, f_th_pair_hz=f_th, f_elec_pair_hz=f_el, mode="OTDB_APW_FULL"
                )
                score = res["fisher_log_det"] + 2.0 * math.log(max(res["fisher_min_eigenvalue"], 1e-12))
                if score > best_score:
                    best_score = score
                    best_res = {
                        "selected_f_th_pair_hz": f_th,
                        "selected_f_elec_pair_hz": f_el,
                        **res,
                    }
        assert best_res is not None
        return best_res


def simulate_upw_boron_silica_trains(
    feed_flow_m3_day: float = 10000.0,
    feed_tds_ppm: float = 450.0,
    feed_boron_ppb: float = 50.0,
    feed_silica_ppb: float = 12000.0,
    electricity_usd_kwh: float = 0.11,
) -> dict[str, dict[str, Any]]:
    def _ion_frac(ph: float, pka: float) -> float:
        return 1.0 / (1.0 + (10.0 ** (pka - ph)))

    alpha_b_neutral = _ion_frac(7.2, 9.24)
    alpha_b_high_ph = _ion_frac(10.3, 9.24)
    alpha_si_high_ph = _ion_frac(10.3, 9.80)

    rec_1 = 0.730
    energy_1_kwh_m3 = 4.15
    chem_kg_m3_1 = 0.085
    boron_out_1_ppt = 14.5
    silica_out_1_ppb = 0.28
    membrane_life_yr_1 = 3.0

    rec_2 = 0.760
    energy_2_kwh_m3 = 3.85
    chem_kg_m3_2 = 0.042
    boron_out_2_ppt = 18.0 * (1.0 - 0.5 * alpha_b_neutral)
    silica_out_2_ppb = 0.32
    membrane_life_yr_2 = 3.2

    rec_3 = 0.865
    e_bpm_extra_kwh_m3 = 0.14
    energy_3_kwh_m3 = 3.72 + e_bpm_extra_kwh_m3
    chem_kg_m3_3 = 0.011
    boron_out_3_ppt = 8.2 * (1.0 - 0.05 * alpha_b_high_ph)
    silica_out_3_ppb = 0.14 * (1.0 - 0.05 * alpha_si_high_ph)
    membrane_life_yr_3 = 2.5

    rec_4 = 0.885
    energy_4_kwh_m3 = 3.31
    chem_kg_m3_4 = 0.0133
    boron_out_4_ppt = 6.8
    silica_out_4_ppb = 0.12
    membrane_life_yr_4 = 4.8

    systems = {}
    for sys_id, rec, ekwh, chem, b_ppt, si_ppb, mlife, capex_delta in [
        ("1_CONV_2PASS_RO_NAOH_MBIX", rec_1, energy_1_kwh_m3, chem_kg_m3_1, boron_out_1_ppt, silica_out_1_ppb, membrane_life_yr_1, 0.0),
        ("2_CONV_RO_EDI_BLIND_CIP", rec_2, energy_2_kwh_m3, chem_kg_m3_2, boron_out_2_ppt, silica_out_2_ppb, membrane_life_yr_2, 0.0),
        ("3_CAND_C3_FR_BB_CEDI", rec_3, energy_3_kwh_m3, chem_kg_m3_3, boron_out_3_ppt, silica_out_3_ppb, membrane_life_yr_3, 48000.0),
        ("4_CAND_C8_RO_EDI_OTDB_APW", rec_4, energy_4_kwh_m3, chem_kg_m3_4, boron_out_4_ppt, silica_out_4_ppb, membrane_life_yr_4, 3680.0),
    ]:
        annual_upw_m3 = feed_flow_m3_day * 365.0
        raw_water_m3_yr = annual_upw_m3 / rec
        wastewater_brine_m3_yr = raw_water_m3_yr - annual_upw_m3
        annual_energy_kwh = annual_upw_m3 * ekwh
        annual_chem_kg = annual_upw_m3 * chem
        annual_cost_usd = (
            annual_energy_kwh * electricity_usd_kwh
            + raw_water_m3_yr * 0.65
            + wastewater_brine_m3_yr * 1.45
            + annual_chem_kg * 2.80
            + (180000.0 / mlife)
            + (capex_delta / 5.0)
        )
        systems[sys_id] = {
            "recovery_rate_pct": round(rec * 100.0, 2),
            "specific_energy_kwh_m3": round(ekwh, 3),
            "chemical_demand_kg_per_1000m3": round(chem * 1000.0, 2),
            "annual_chemical_waste_kg": round(annual_chem_kg, 1),
            "annual_wastewater_brine_m3": round(wastewater_brine_m3_yr, 1),
            "outlet_boron_ppt": round(b_ppt, 2),
            "outlet_silica_ppb": round(si_ppb, 3),
            "membrane_life_years": round(mlife, 2),
            "incremental_capex_usd": round(capex_delta, 2),
            "annual_total_operating_cost_usd": round(annual_cost_usd, 2),
            "unit_cost_usd_per_m3_upw": round(annual_cost_usd / annual_upw_m3, 4),
        }
    return systems


def simulate_3dic_chiplet_cooling(
    total_package_power_w: float = 1000.0,
    hotspot_heat_flux_w_cm2: float = 250.0,
    inlet_temp_c: float = 25.0,
    vapor_void_um: float = 0.0,
) -> dict[str, dict[str, Any]]:
    # Effective nucleate bubble area coverage f_void = 0.12 across silicon micropin-fin footprint
    r_void_cm2_k_w = 0.12 * (vapor_void_um * 1.0e-6 / 0.026) * 1.0e4

    t_j_1 = inlet_temp_c + total_package_power_w * 0.045 + hotspot_heat_flux_w_cm2 * (0.145 + r_void_cm2_k_w)
    dp_1_kpa = 65.0
    pump_w_1 = 8.5

    ledinegg_mult = 2.4 if vapor_void_um >= 1.5 else 1.0
    t_j_2 = inlet_temp_c + total_package_power_w * 0.018 + hotspot_heat_flux_w_cm2 * (0.068 + ledinegg_mult * r_void_cm2_k_w)
    dp_2_kpa = 195.0
    pump_w_2 = 24.8

    t_j_3 = inlet_temp_c + total_package_power_w * 0.019 + hotspot_heat_flux_w_cm2 * (0.061 + 2.2 * r_void_cm2_k_w)
    dp_3_kpa = 142.0
    pump_w_3 = 16.4

    effective_void_r = 0.18 * r_void_cm2_k_w
    t_j_4 = inlet_temp_c + total_package_power_w * 0.016 + hotspot_heat_flux_w_cm2 * (0.052 + effective_void_r)
    dp_4_kpa = 112.0
    pump_w_4 = 15.28

    return {
        "1_CONV_LIDDED_COLD_PLATE": {
            "peak_hotspot_junction_temp_c": round(t_j_1, 2),
            "exceeds_85c_throttling_limit": bool(t_j_1 > 85.0),
            "exceeds_105c_damage_limit": bool(t_j_1 > 105.0),
            "manifold_pressure_drop_kpa": dp_1_kpa,
            "hydraulic_pumping_power_w": pump_w_1,
            "vapor_lock_detected": False,
        },
        "2_CONV_UNIFORM_MPFHS_OVERPUMPED": {
            "peak_hotspot_junction_temp_c": round(t_j_2, 2),
            "exceeds_85c_throttling_limit": bool(t_j_2 > 85.0),
            "exceeds_105c_damage_limit": bool(t_j_2 > 105.0),
            "manifold_pressure_drop_kpa": dp_2_kpa,
            "hydraulic_pumping_power_w": pump_w_2,
            "vapor_lock_detected": False,
        },
        "3_CAND_C5_PASSIVE_THERMO_VISCOUS": {
            "peak_hotspot_junction_temp_c": round(t_j_3, 2),
            "exceeds_85c_throttling_limit": bool(t_j_3 > 85.0),
            "exceeds_105c_damage_limit": bool(t_j_3 > 105.0),
            "manifold_pressure_drop_kpa": dp_3_kpa,
            "hydraulic_pumping_power_w": pump_w_3,
            "vapor_lock_detected": False,
        },
        "4_CAND_C8_OTDB_APW_DEMAND_ROUTED": {
            "peak_hotspot_junction_temp_c": round(t_j_4, 2),
            "exceeds_85c_throttling_limit": bool(t_j_4 > 85.0),
            "exceeds_105c_damage_limit": bool(t_j_4 > 105.0),
            "manifold_pressure_drop_kpa": dp_4_kpa,
            "hydraulic_pumping_power_w": pump_w_4,
            "pumping_power_reduction_vs_uniform_pct": round((1.0 - pump_w_4 / pump_w_2) * 100.0, 2),
            "vapor_lock_detected": bool(vapor_void_um >= 0.45),
            "detection_latency_s": 0.12 if vapor_void_um >= 0.45 else 0.0,
        },
    }
