"""Material library: load dispersion data files and provide N(lambda) interpolators."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.interpolate import interp1d

# ---------------------------------------------------------------------------
# Analytical dispersion models
# ---------------------------------------------------------------------------

_HBAR_EV_S = 6.582119569e-16  # eV·s  (reduced Planck constant)
_C_NM_S = 2.99792458e17  # nm/s  (speed of light)
_HC_EV_NM = 2 * np.pi * _HBAR_EV_S * _C_NM_S  # ≈ 1239.84 eV·nm


def _eps_to_N(eps: np.ndarray) -> np.ndarray:
    """Convert dielectric function to complex refractive index with Im(N) >= 0."""
    N = np.sqrt(eps.astype(np.complex128))
    return np.where(N.imag < 0, -N, N)


def _analytical_drude(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Drude model: eps = eps_inf - omega_p^2 / (E^2 + i*gamma*E)"""
    E = _HC_EV_NM / lam_nm
    eps_inf = params["eps_inf"]
    wp = params["omega_p_eV"]
    g = params["gamma_eV"]
    eps = eps_inf - wp**2 / (E**2 + 1j * g * E)
    return _eps_to_N(eps)


def _analytical_lorentz(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Lorentz oscillator: eps = eps_inf + f*omega_0^2 / (omega_0^2 - E^2 - i*gamma*E)"""
    E = _HC_EV_NM / lam_nm
    eps_inf = params["eps_inf"]
    w0 = params["omega_0_eV"]
    f = params["f"]
    g = params["gamma_eV"]
    eps = eps_inf + f * w0**2 / (w0**2 - E**2 - 1j * g * E)
    return _eps_to_N(eps)


def _analytical_drude_lorentz(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Drude-Lorentz model: Drude free-electron term + sum of Lorentz oscillators."""
    E = _HC_EV_NM / lam_nm
    eps_inf = params["eps_inf"]
    wp = params["omega_p_eV"]
    gD = params["gamma_D_eV"]
    eps = eps_inf - wp**2 / (E**2 + 1j * gD * E)
    for osc in params.get("oscillators", []):
        wj = osc["omega_j_eV"]
        fj = osc["f_j"]
        gj = osc["gamma_j_eV"]
        eps = eps + fj * wj**2 / (wj**2 - E**2 - 1j * gj * E)
    return _eps_to_N(eps)


def _analytical_sellmeier(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Sellmeier: n^2 = 1 + sum_j B_j*lam^2 / (lam^2 - C_j)  (lam in um, C in um^2)"""
    lam_um = lam_nm / 1000.0
    n2 = np.ones(lam_nm.shape, dtype=np.float64)
    for pole in params["poles"]:
        B = pole["B"]
        C = pole["C_um2"]
        n2 = n2 + B * lam_um**2 / (lam_um**2 - C)
    # n2 may be slightly negative in absorption bands — clamp to 0
    n2 = np.maximum(n2, 0.0)
    return np.sqrt(n2).astype(np.complex128)


def _analytical_cauchy(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Cauchy: n = A + B/lam_um^2 + C/lam_um^4  (k=0)"""
    lam_um = lam_nm / 1000.0
    A = params["A"]
    B = params.get("B_um2", 0.0)
    C = params.get("C_um4", 0.0)
    n = A + B / lam_um**2 + C / lam_um**4
    return n.astype(np.complex128)


def _analytical_constant(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Constant refractive index: N = n + i*k"""
    n = params["n"]
    k = params.get("k", 0.0)
    return np.full(lam_nm.shape, complex(n, k), dtype=np.complex128)


def _analytical_graphene2d(lam_nm: np.ndarray, params: dict) -> np.ndarray:
    """Modèle 2D conducteur (graphène) via formule de Kubo — approche thin-slab.

    Paramètres JSON
    ---------------
    mu_c_eV : potentiel chimique (niveau de Fermi), eV  [défaut 0.0]
    tau_fs  : temps de diffusion, femtosecondes          [défaut 100.0]
    T_K     : température, Kelvin                        [défaut 300.0]
    d_nm    : épaisseur du slab équivalent, nm           [défaut 0.335]

    La couche doit être ajoutée avec une épaisseur égale à d_nm.

    Physique
    --------
    σ_s(ω) = σ_intra + σ_inter  (formule de Kubo)
    ε_eff  = 1 + i·σ_s / (ε₀·ω·d)
    N_eff  = √ε_eff
    """
    from scipy.constants import e, hbar, k as kB, epsilon_0, c, pi

    mu_c = params.get("mu_c_eV", 0.0) * e        # J
    tau  = params.get("tau_fs", 100.0) * 1e-15    # s
    T    = params.get("T_K", 300.0)               # K
    d    = params.get("d_nm", 0.335) * 1e-9       # m

    omega = 2.0 * pi * c / (lam_nm * 1e-9)       # rad/s
    kBT   = kB * T

    # Terme intraband (Kubo, forme fermée)
    intra_factor = (mu_c / kBT) + 2.0 * np.log(np.exp(-mu_c / kBT) + 1.0)
    sigma_intra = (1j * e**2 * kBT) / (pi * hbar**2 * (omega + 1j / tau)) * intra_factor

    # Terme interband (approximation analytique de Hanson/Falkovsky)
    hw = hbar * omega
    arg_re  = (hw - 2.0 * mu_c) / (2.0 * kBT)
    num_log = (hw + 2.0 * mu_c) ** 2 + (2.0 * kBT) ** 2
    den_log = (hw - 2.0 * mu_c) ** 2 + (2.0 * kBT) ** 2
    sigma_inter = (e**2 / (4.0 * hbar)) * (
        0.5
        + np.arctan(arg_re) / pi
        - 1j / (2.0 * pi) * np.log(num_log / den_log)
    )

    sigma_s  = sigma_intra + sigma_inter          # S (conductivité de surface)
    eps_eff  = 1.0 + 1j * sigma_s / (epsilon_0 * omega * d)
    return _eps_to_N(eps_eff)


_ANALYTICAL_MODELS: dict[str, Callable] = {
    "Drude": _analytical_drude,
    "Lorentz": _analytical_lorentz,
    "DrudeLorentz": _analytical_drude_lorentz,
    "Sellmeier": _analytical_sellmeier,
    "Cauchy": _analytical_cauchy,
    "Constant": _analytical_constant,
    "Graphene2D": _analytical_graphene2d,
}


def _load_analytical_json(
    path: Path,
) -> tuple[str, str, Callable, Callable, float, float]:
    """Parse a JSON material file and return (key, label, n_fn, k_fn, lam_min, lam_max).

    JSON format::

        {
          "name": "Gold_Drude",
          "model": "Drude",
          "params": { "eps_inf": 9.5, "omega_p_eV": 9.03, "gamma_eV": 0.071 },
          "wavelength_range_nm": [300, 2000]
        }

    Supported models: Drude, Lorentz, DrudeLorentz, Sellmeier, Cauchy, Constant.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("name", "model", "params", "wavelength_range_nm"):
        if key not in data:
            raise ValueError(f"Missing required field '{key}' in {path.name}")
    model_name = data["model"]
    if model_name not in _ANALYTICAL_MODELS:
        raise ValueError(
            f"Unknown model '{model_name}' in {path.name}. "
            f"Available: {list(_ANALYTICAL_MODELS)}"
        )
    params = data["params"]
    model_fn = _ANALYTICAL_MODELS[model_name]
    # Capture params by value to avoid late-binding issues
    n_fn: Callable = lambda lam, _p=params, _m=model_fn: _m(
        np.asarray(lam, dtype=np.float64), _p
    ).real
    k_fn: Callable = lambda lam, _p=params, _m=model_fn: _m(
        np.asarray(lam, dtype=np.float64), _p
    ).imag
    lam_range = data["wavelength_range_nm"]
    lam_min, lam_max = float(lam_range[0]), float(lam_range[1])
    label = data["name"]
    key = label.lower()
    return key, label, n_fn, k_fn, lam_min, lam_max


class MaterialRangeError(ValueError):
    """Raised when a requested wavelength is outside a material's data range."""


# Semi-infinite (non-dispersive) built-in media
_SEMI_INFINITE: dict[str, complex] = {
    "air": 1.0 + 0j,
    "vacuum": 1.0 + 0j,
    "glass": 1.52 + 0j,
    "sio2": 1.46 + 0j,
    "bk7": 1.52 + 0j,
}


class MaterialLibrary:
    """Loads and caches optical material data files.

    Each .txt file must have the header line ``lambda n k`` followed by
    space-separated numerical rows (wavelength in nm, real and imaginary
    parts of the refractive index).
    """

    def __init__(self) -> None:
        # name (lower) -> (n_interpolator, k_interpolator, lam_min, lam_max)
        self._cache: dict[str, tuple[Callable, Callable, float, float]] = {}
        # name -> display label (preserves original case)
        self._labels: dict[str, str] = {}
        # keys loaded from analytical JSON files
        self._analytical_keys: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, path: str | Path, name: str | None = None) -> str:
        """Load a single material file.  Returns the registered name (key)."""
        path = Path(path)
        label = name if name else path.stem
        key = label.lower()

        data = np.loadtxt(path, skiprows=1)
        lam = data[:, 0].astype(np.float64)
        n_vals = data[:, 1].astype(np.float64)
        k_vals = data[:, 2].astype(np.float64)

        # Sort by wavelength (some files may not be strictly sorted)
        order = np.argsort(lam)
        lam, n_vals, k_vals = lam[order], n_vals[order], k_vals[order]

        n_interp = interp1d(lam, n_vals, kind="cubic", bounds_error=True)
        k_interp = interp1d(lam, k_vals, kind="cubic", bounds_error=True)

        self._cache[key] = (n_interp, k_interp, float(lam[0]), float(lam[-1]))
        self._labels[key] = label
        return key

    def load_directory(self, directory: str | Path) -> list[str]:
        """Load all .txt and .json material files in a directory.

        .txt files are loaded as tabulated n,k data.
        .json files are loaded as analytically defined materials (Drude, Lorentz, etc.).
        Returns list of registered keys.
        """
        directory = Path(directory)
        keys = []
        for f in sorted(directory.glob("*.txt")):
            keys.append(self.load(f))
        for f in sorted(directory.glob("*.json")):
            try:
                key, label, n_fn, k_fn, lam_min, lam_max = _load_analytical_json(f)
                self.register(key, label, n_fn, k_fn, lam_min, lam_max)
                self._analytical_keys.add(key)
                keys.append(key)
            except Exception as e:
                print(f"Warning: could not load analytical material {f.name}: {e}")
        return keys

    def register(
        self,
        key: str,
        label: str,
        n_interp: Callable,
        k_interp: Callable,
        lam_min: float,
        lam_max: float,
    ) -> None:
        """Register a pre-built interpolator pair (used for mixed materials)."""
        k = key.lower()
        self._cache[k] = (n_interp, k_interp, lam_min, lam_max)
        self._labels[k] = label

    def N(self, name: str, lam_nm: np.ndarray) -> np.ndarray:
        """Return complex refractive index N = n + ik for *name* at wavelengths *lam_nm* (nm)."""
        lam_nm = np.asarray(lam_nm, dtype=np.float64)
        key = name.lower()

        # Semi-infinite / non-dispersive media
        if key in _SEMI_INFINITE:
            return np.full(lam_nm.shape, _SEMI_INFINITE[key], dtype=np.complex128)

        if key not in self._cache:
            raise KeyError(
                f"Material '{name}' not found in library. "
                f"Available: {self.available()}"
            )

        n_interp, k_interp, lam_min, lam_max = self._cache[key]

        out_of_range = np.where((lam_nm < lam_min) | (lam_nm > lam_max))[0]
        if len(out_of_range):
            bad = lam_nm[out_of_range]
            raise MaterialRangeError(
                f"Material '{name}' data covers {lam_min:.0f}–{lam_max:.0f} nm. "
                f"Requested wavelengths {bad[0]:.1f}…{bad[-1]:.1f} nm are out of range."
            )

        return n_interp(lam_nm) + 1j * k_interp(lam_nm)

    def wavelength_range(self, name: str) -> tuple[float, float]:
        """Return (lam_min, lam_max) in nm for a material."""
        key = name.lower()
        if key in _SEMI_INFINITE:
            return (0.0, np.inf)
        if key not in self._cache:
            raise KeyError(name)
        _, _, lam_min, lam_max = self._cache[key]
        return lam_min, lam_max

    def available(self) -> list[str]:
        """Return all registered material keys (lower-case) plus built-ins.

        Order: built-in constants → tabulated (.txt) → analytical JSON.
        """
        tabulated = [k for k in self._cache if k not in self._analytical_keys]
        analytical = [k for k in self._cache if k in self._analytical_keys]
        return list(_SEMI_INFINITE.keys()) + tabulated + analytical

    def labels(self) -> dict[str, str]:
        """Return mapping key -> display label."""
        combined = {k: k for k in _SEMI_INFINITE}
        combined.update(self._labels)
        return combined

    def label(self, key: str) -> str:
        key = key.lower()
        return self._labels.get(key, key)
