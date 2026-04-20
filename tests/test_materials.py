"""
Tests for the material library (materials.py).

Validates loading, dispersion model evaluation, and interpolation.
No GUI required.
"""

from __future__ import annotations

import numpy as np
import pytest

from reflecto_sim.materials import MaterialLibrary, MaterialRangeError


class TestMaterialLibrary:
    def test_loads_materials(self, lib: MaterialLibrary):
        """Library must contain at least one material after load_directory."""
        assert len(list(lib.available())) > 0

    def test_builtin_semi_infinite(self):
        """Built-in semi-infinite media (air, glass, …) must be available."""
        lib = MaterialLibrary()  # no load_directory — built-ins only
        lam = np.array([500.0, 600.0, 700.0])
        for name in ("air", "vacuum", "glass", "sio2", "bk7", "al2o3"):
            N = lib.N(name, lam)
            assert N.shape == (3,), f"{name}: wrong shape"
            # All built-ins are real (non-absorbing)
            assert np.allclose(N.imag, 0.0), f"{name}: unexpected imaginary part"

    def test_air_index_is_one(self):
        lib = MaterialLibrary()
        lam = np.linspace(400, 800, 100)
        N = lib.N("air", lam)
        np.testing.assert_allclose(N.real, 1.0, atol=1e-12)
        np.testing.assert_allclose(N.imag, 0.0, atol=1e-12)

    def test_glass_index_positive(self):
        lib = MaterialLibrary()
        lam = np.linspace(400, 800, 50)
        N = lib.N("glass", lam)
        assert np.all(N.real > 1.0), "glass n must be > 1"

    def test_tabulated_material_shape(self, lib: MaterialLibrary):
        """Tabulated materials return correct shape."""
        avail = list(lib.available())
        if not avail:
            pytest.skip("No tabulated materials loaded")
        mat = avail[0]
        lam = np.arange(500.0, 701.0, 5.0)
        N = lib.N(mat, lam)
        assert N.shape == lam.shape, f"{mat}: shape mismatch"
        assert N.dtype == complex

    def test_range_error_raised(self, lib: MaterialLibrary):
        """Requesting wavelengths outside material range raises MaterialRangeError."""
        # Use a tabulated material — built-ins (air, glass, …) have no range check
        tabulated = [m for m in lib.available()
                     if m not in ("air", "vacuum", "glass", "sio2", "bk7", "al2o3")]
        if not tabulated:
            pytest.skip("No tabulated materials loaded")
        mat = tabulated[0]
        lam_bad = np.array([1.0, 2.0])  # 1–2 nm: certainly out of range
        with pytest.raises(MaterialRangeError):
            lib.N(mat, lam_bad)

    def test_refractive_index_positive_real(self, lib: MaterialLibrary):
        """Real part of N must be positive for all loaded materials."""
        lam = np.arange(500.0, 701.0, 5.0)
        errors = []
        for mat in lib.available():
            try:
                N = lib.N(mat, lam)
                if not np.all(N.real > 0):
                    errors.append(mat)
            except MaterialRangeError:
                pass  # OK — wavelength out of range for this material
        assert not errors, f"Non-positive n.real for: {errors}"

    def test_extinction_coefficient_non_negative(self, lib: MaterialLibrary):
        """k (imaginary part of N) must be ≥ 0 (passive material)."""
        lam = np.arange(500.0, 701.0, 5.0)
        errors = []
        for mat in lib.available():
            try:
                N = lib.N(mat, lam)
                if not np.all(N.imag >= -1e-6):
                    errors.append(mat)
            except MaterialRangeError:
                pass
        assert not errors, f"Negative k (absorbing sign error) for: {errors}"


class TestAnalyticalModels:
    """Quick smoke-tests for JSON-defined analytical dispersion models."""

    def test_gold_drude_loaded(self, lib: MaterialLibrary):
        """gold_drude model must produce complex N with Re(N) > 0."""
        if "gold_drude" not in lib.available():
            pytest.skip("gold_drude not in material library")
        lam = np.arange(600.0, 1001.0, 10.0)
        N = lib.N("gold_drude", lam)
        assert np.all(N.real > 0), "gold_drude: n should be > 0 in IR"
        assert np.all(N.imag >= 0), "gold_drude: k should be ≥ 0"
