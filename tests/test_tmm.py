"""
Tests for the TMM physics kernel (tmm.py).

All tests run without a GUI — pure physics validation.
Energy conservation and limiting-case checks.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from reflecto_sim.stack import resolve_stack, build_N_matrix
from reflecto_sim.tmm import (
    compute_spectrum,
    compute_na_spectrum,
    r_to_observables,
    t_to_observables,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute(stack, lam, lib, theta=0.0, pol="s"):
    """Resolve stack and run TMM. Returns (r, t, N0_arr, Ns_arr)."""
    layers, N0_arr, Ns_arr = resolve_stack(stack, lam, lib)
    if not layers:
        # Bare interface — analytic Fresnel at normal incidence
        r = (N0_arr - Ns_arr) / (N0_arr + Ns_arr)
        t = 2 * N0_arr / (N0_arr + Ns_arr)
        return r, t, N0_arr, Ns_arr
    N_mat, d_arr = build_N_matrix(layers)
    r, t = compute_spectrum(N_mat, d_arr, lam, N0_arr, Ns_arr,
                            theta_deg=theta, pol=pol)
    return r, t, N0_arr, Ns_arr


# ---------------------------------------------------------------------------
# Energy conservation: R + T ≈ 1 for lossless dielectrics
# ---------------------------------------------------------------------------

class TestEnergyConservation:
    def test_tio2_normal_s(self, lib, lam_vis, single_tio2_stack):
        r, t, N0, Ns = _compute(single_tio2_stack, lam_vis, lib, theta=0.0, pol="s")
        amp, R, phi = r_to_observables(r)
        amp_t, T, phi_t = t_to_observables(t, N0, Ns, 0.0, "s")
        np.testing.assert_allclose(R + T, 1.0, atol=1e-6,
                                   err_msg="R + T != 1 at normal incidence (TiO2/sio2)")

    def test_tio2_oblique_s(self, lib, lam_vis, single_tio2_stack):
        r, t, N0, Ns = _compute(single_tio2_stack, lam_vis, lib, theta=20.0, pol="s")
        _, R, _ = r_to_observables(r)
        _, T, _ = t_to_observables(t, N0, Ns, 20.0, "s")
        np.testing.assert_allclose(R + T, 1.0, atol=1e-6,
                                   err_msg="R + T != 1 at 20° incidence (s-pol)")

    def test_tio2_oblique_p(self, lib, lam_vis, single_tio2_stack):
        r, t, N0, Ns = _compute(single_tio2_stack, lam_vis, lib, theta=20.0, pol="p")
        _, R, _ = r_to_observables(r)
        _, T, _ = t_to_observables(t, N0, Ns, 20.0, "p")
        np.testing.assert_allclose(R + T, 1.0, atol=1e-6,
                                   err_msg="R + T != 1 at 20° incidence (p-pol)")

    def test_two_layer_conservation(self, lib, lam_vis, two_layer_stack):
        r, t, N0, Ns = _compute(two_layer_stack, lam_vis, lib, theta=0.0, pol="s")
        _, R, _ = r_to_observables(r)
        _, T, _ = t_to_observables(t, N0, Ns, 0.0, "s")
        np.testing.assert_allclose(R + T, 1.0, atol=1e-6)


# ---------------------------------------------------------------------------
# r_to_observables: |r|² == R
# ---------------------------------------------------------------------------

class TestObservables:
    def test_amp_squared_equals_R(self, lib, lam_vis, single_tio2_stack):
        r, t, N0, Ns = _compute(single_tio2_stack, lam_vis, lib)
        amp, R, phi = r_to_observables(r)
        np.testing.assert_allclose(amp ** 2, R, rtol=1e-10)

    def test_R_in_unit_interval(self, lib, lam_vis, single_tio2_stack):
        r, _, _, _ = _compute(single_tio2_stack, lam_vis, lib)
        _, R, _ = r_to_observables(r)
        assert np.all(R >= -1e-9), "R has negative values"
        assert np.all(R <= 1.0 + 1e-9), "R exceeds 1.0"

    def test_phase_range(self, lib, lam_vis, single_tio2_stack):
        r, _, _, _ = _compute(single_tio2_stack, lam_vis, lib)
        _, _, phi = r_to_observables(r)
        assert np.all(phi >= -math.pi - 1e-9)
        assert np.all(phi <= math.pi + 1e-9)

    def test_output_shapes(self, lib, lam_vis, single_tio2_stack):
        r, t, N0, Ns = _compute(single_tio2_stack, lam_vis, lib)
        amp, R, phi = r_to_observables(r)
        amp_t, T, phi_t = t_to_observables(t, N0, Ns, 0.0, "s")
        n = len(lam_vis)
        assert r.shape == (n,)
        assert R.shape == (n,)
        assert T.shape == (n,)


# ---------------------------------------------------------------------------
# Limiting cases
# ---------------------------------------------------------------------------

class TestLimitingCases:
    def test_bare_substrate_R(self, lib, lam_broad):
        """Stack with zero layers: R = Fresnel reflection at air/glass."""
        from reflecto_sim.stack import StackConfig
        stack = StackConfig(superstrate="air", substrate="glass", layers=[])
        r, t, N0, Ns = _compute(stack, lam_broad, lib, theta=0.0, pol="s")
        _, R, _ = r_to_observables(r)
        # At normal incidence, air→glass: R = ((n-1)/(n+1))^2 ≈ 0.040 for n=1.52
        n_glass = 1.52
        R_expected = ((n_glass - 1) / (n_glass + 1)) ** 2
        np.testing.assert_allclose(R, R_expected, atol=5e-3,
                                   err_msg="Bare glass R deviates from Fresnel formula")

    def test_zero_thickness_layer_is_transparent(self, lib, lam_vis):
        """A layer with d=0 nm must give the same result as no layer."""
        from reflecto_sim.stack import StackConfig, LayerSpec
        stack_bare = StackConfig(superstrate="air", substrate="sio2", layers=[])
        stack_zero = StackConfig(
            superstrate="air", substrate="sio2",
            layers=[LayerSpec(name="ghost", material="tio2", thickness_nm=0.0)],
        )
        r_bare, _, _, _ = _compute(stack_bare, lam_vis, lib)
        r_zero, _, _, _ = _compute(stack_zero, lam_vis, lib)
        np.testing.assert_allclose(
            np.abs(r_bare), np.abs(r_zero), atol=1e-9,
            err_msg="|r| differs between bare stack and zero-thickness layer",
        )

    def test_s_p_equal_at_normal_incidence(self, lib, lam_vis, single_tio2_stack):
        """At θ=0, s and p polarisations must give identical reflectance."""
        r_s, t_s, N0, Ns = _compute(single_tio2_stack, lam_vis, lib, theta=0.0, pol="s")
        r_p, t_p, _, _ = _compute(single_tio2_stack, lam_vis, lib, theta=0.0, pol="p")
        _, R_s, _ = r_to_observables(r_s)
        _, R_p, _ = r_to_observables(r_p)
        np.testing.assert_allclose(R_s, R_p, atol=1e-10,
                                   err_msg="s- and p-pol differ at normal incidence")


# ---------------------------------------------------------------------------
# NA integration
# ---------------------------------------------------------------------------

class TestNAIntegration:
    def test_na_zero_approaches_normal(self, lib, lam_vis, single_tio2_stack):
        """NA → 0 should approach the normal-incidence single-angle result."""
        r, _, N0, Ns = _compute(single_tio2_stack, lam_vis, lib, theta=0.0, pol="s")
        _, R_single, _ = r_to_observables(r)

        layers, N0_arr, Ns_arr = resolve_stack(single_tio2_stack, lam_vis, lib)
        N_mat, d_arr = build_N_matrix(layers)
        R_na, _ = compute_na_spectrum(N_mat, d_arr, lam_vis, N0_arr, Ns_arr,
                                      na=0.01, pol="s")
        np.testing.assert_allclose(R_na, R_single, atol=1e-3,
                                   err_msg="NA≈0 result deviates from single-angle R")

    def test_na_result_in_unit_interval(self, lib, lam_vis, single_tio2_stack):
        layers, N0_arr, Ns_arr = resolve_stack(single_tio2_stack, lam_vis, lib)
        N_mat, d_arr = build_N_matrix(layers)
        R_na, T_na = compute_na_spectrum(N_mat, d_arr, lam_vis, N0_arr, Ns_arr,
                                         na=0.4, pol="s")
        assert np.all(R_na >= -1e-9) and np.all(R_na <= 1.0 + 1e-9)
        assert np.all(T_na >= -1e-9) and np.all(T_na <= 1.0 + 1e-9)
