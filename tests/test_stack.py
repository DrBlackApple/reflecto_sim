"""
Tests for stack.py — StackConfig, LayerSpec, resolve_stack, build_N_matrix.

No GUI required.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from reflecto_sim.stack import LayerSpec, StackConfig, resolve_stack, build_N_matrix


class TestLayerSpec:
    def test_defaults(self):
        spec = LayerSpec(name="test", material="tio2", thickness_nm=100.0)
        assert spec.mix_mat_b == ""
        assert spec.mix_f == 0.5
        assert spec.sweep_mode == ""
        assert spec.sweep_n_pts == 11

    def test_is_mixed_false_by_default(self):
        spec = LayerSpec(name="A", material="tio2", thickness_nm=50.0)
        assert not spec.is_mixed()

    def test_is_mixed_true_when_mix_mat_b_set(self):
        spec = LayerSpec(name="A", material="tio2", thickness_nm=50.0, mix_mat_b="sio2")
        assert spec.is_mixed()

    def test_roundtrip_serialization(self):
        spec = LayerSpec(
            name="test", material="tio2", thickness_nm=80.0,
            mix_mat_b="sio2", mix_f=0.3, mix_model="Maxwell Garnett",
            sweep_mode="mix", sweep_mat_b="mgo", sweep_n_pts=15,
        )
        d = spec.to_dict()
        spec2 = LayerSpec.from_dict(d)
        assert spec2.name == spec.name
        assert spec2.material == spec.material
        assert spec2.thickness_nm == spec.thickness_nm
        assert spec2.mix_mat_b == spec.mix_mat_b
        assert abs(spec2.mix_f - spec.mix_f) < 1e-12
        assert spec2.mix_model == spec.mix_model
        assert spec2.sweep_mode == spec.sweep_mode
        assert spec2.sweep_n_pts == spec.sweep_n_pts


class TestStackConfig:
    def test_default_config(self):
        cfg = StackConfig()
        assert cfg.superstrate == "air"
        assert cfg.substrate == "glass"
        assert cfg.layers == []

    def test_save_load_roundtrip(self, single_tio2_stack):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            single_tio2_stack.save(path)
            loaded = StackConfig.load(path)
            assert loaded.superstrate == single_tio2_stack.superstrate
            assert loaded.substrate == single_tio2_stack.substrate
            assert len(loaded.layers) == len(single_tio2_stack.layers)
            assert loaded.layers[0].material == single_tio2_stack.layers[0].material
            assert loaded.layers[0].thickness_nm == single_tio2_stack.layers[0].thickness_nm
        finally:
            Path(path).unlink(missing_ok=True)

    def test_json_structure(self, single_tio2_stack):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False,
                                          mode="w") as f:
            path = f.name
        try:
            single_tio2_stack.save(path)
            with open(path) as fp:
                data = json.load(fp)
            assert "superstrate" in data
            assert "substrate" in data
            assert "layers" in data
            assert isinstance(data["layers"], list)
        finally:
            Path(path).unlink(missing_ok=True)


class TestResolveStack:
    def test_resolve_returns_correct_count(self, lib, lam_vis, single_tio2_stack):
        layers, N0_arr, Ns_arr = resolve_stack(single_tio2_stack, lam_vis, lib)
        assert len(layers) == 1
        assert N0_arr.shape == lam_vis.shape
        assert Ns_arr.shape == lam_vis.shape

    def test_superstrate_air_index(self, lib, lam_vis, single_tio2_stack):
        _, N0_arr, _ = resolve_stack(single_tio2_stack, lam_vis, lib)
        np.testing.assert_allclose(N0_arr.real, 1.0, atol=1e-12)
        np.testing.assert_allclose(N0_arr.imag, 0.0, atol=1e-12)

    def test_N_matrix_shape(self, lib, lam_vis, single_tio2_stack):
        layers, N0_arr, Ns_arr = resolve_stack(single_tio2_stack, lam_vis, lib)
        N_mat, d_arr = build_N_matrix(layers)
        n_lam = len(lam_vis)
        n_layers = len(single_tio2_stack.layers)
        assert N_mat.shape == (n_layers, n_lam)
        assert d_arr.shape == (n_layers,)

    def test_two_layer_N_matrix(self, lib, lam_vis, two_layer_stack):
        layers, _, _ = resolve_stack(two_layer_stack, lam_vis, lib)
        N_mat, d_arr = build_N_matrix(layers)
        assert N_mat.shape[0] == 2
        assert d_arr.shape == (2,)
        np.testing.assert_allclose(d_arr[0], 80.0)
        np.testing.assert_allclose(d_arr[1], 50.0)

    def test_tio2_n_above_one(self, lib, lam_vis, single_tio2_stack):
        layers, _, _ = resolve_stack(single_tio2_stack, lam_vis, lib)
        N_mat, _ = build_N_matrix(layers)
        n_tio2 = N_mat[0].real
        assert np.all(n_tio2 > 1.0), "TiO2 n must be > 1"
        assert np.all(n_tio2 < 4.0), "TiO2 n suspiciously high (>4)"
