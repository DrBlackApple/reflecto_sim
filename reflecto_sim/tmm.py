"""Transfer Matrix Method (TMM) for multilayer optical stacks.

Core kernel is Numba-JIT compiled for near-C speed.
The outer interpolation loop remains in NumPy/SciPy.
"""

from __future__ import annotations

import math
import cmath

import numpy as np

try:
    import numba
    from numba import njit, complex128, float64, int8

    _NUMBA_AVAILABLE = True
except ImportError:
    _NUMBA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Numba JIT kernel — compiled once, cached to disk
# ---------------------------------------------------------------------------


def _make_kernel():
    """Return a JIT-compiled or pure-Python TMM kernel."""

    if _NUMBA_AVAILABLE:

        @njit(cache=True)
        def _kernel(N_layers, d_layers, lam_nm, theta_rad, N0, Ns, pol):
            """Compute complex reflection coefficient r for one wavelength.

            Parameters
            ----------
            N_layers : complex128[n_layers]   complex refractive indices
            d_layers : float64[n_layers]      layer thicknesses (nm)
            lam_nm   : float64                wavelength (nm)
            theta_rad: float64                angle of incidence in superstrate (rad)
            N0       : complex128             superstrate N
            Ns       : complex128             substrate N
            pol      : int8                   0 = s/TE, 1 = p/TM
            """
            TWO_PI = 6.283185307179586
            k0 = TWO_PI / lam_nm
            sin_t = cmath.sin(theta_rad)
            kz0 = cmath.sqrt(N0**2 - (N0 * sin_t) ** 2)
            kzs = cmath.sqrt(Ns**2 - (N0 * sin_t) ** 2)

            # Admittances for superstrate and substrate
            if pol == 0:  # s / TE
                eta0 = kz0
                etas = kzs
            else:  # p / TM
                eta0 = (N0**2) / kz0
                etas = (Ns**2) / kzs

            # Accumulate total transfer matrix (initialised to identity)
            M00 = 1.0 + 0j
            M01 = 0.0 + 0j
            M10 = 0.0 + 0j
            M11 = 1.0 + 0j

            for j in range(len(N_layers)):
                Nj = N_layers[j]
                dj = d_layers[j]

                kzj = k0 * cmath.sqrt(Nj**2 - (N0 * sin_t) ** 2)
                delta = kzj * dj

                if pol == 0:
                    eta_j = kzj / k0
                else:
                    eta_j = (Nj**2) * k0 / kzj

                c = cmath.cos(delta)
                s = cmath.sin(delta)

                # Layer transfer matrix L_j
                L00 = c
                L01 = -1j * s / eta_j
                L10 = -1j * eta_j * s
                L11 = c

                # M = M @ L_j  (inline 2x2 multiply)
                n00 = M00 * L00 + M01 * L10
                n01 = M00 * L01 + M01 * L11
                n10 = M10 * L00 + M11 * L10
                n11 = M10 * L01 + M11 * L11
                M00, M01, M10, M11 = n00, n01, n10, n11

            # reflection coefficient
            num = M00 * eta0 + M01 * eta0 * etas - M10 - M11 * etas
            den = M00 * eta0 + M01 * eta0 * etas + M10 + M11 * etas
            return num / den

        return _kernel

    else:
        # Pure-Python fallback (no Numba) — admittances match the JIT version
        def _kernel(N_layers, d_layers, lam_nm, theta_rad, N0, Ns, pol):
            TWO_PI = 2.0 * math.pi
            k0 = TWO_PI / lam_nm
            sin_t = cmath.sin(complex(theta_rad))
            # kz0/kzs are dimensionless (= N*cos θ); no k0 factor here
            kz0 = cmath.sqrt(N0**2 - (N0 * sin_t) ** 2)
            kzs = cmath.sqrt(Ns**2 - (N0 * sin_t) ** 2)

            if pol == 0:  # s / TE
                eta0, etas = kz0, kzs
            else:  # p / TM
                eta0 = (N0**2) / kz0
                etas = (Ns**2) / kzs

            M = np.eye(2, dtype=complex)
            for j in range(len(N_layers)):
                Nj = N_layers[j]
                dj = d_layers[j]
                kzj = k0 * cmath.sqrt(Nj**2 - (N0 * sin_t) ** 2)
                delta = kzj * dj
                # admittance for layer: divide by k0 to stay dimensionless
                if pol == 0:
                    eta_j = kzj / k0
                else:
                    eta_j = (Nj**2) * k0 / kzj
                c = cmath.cos(delta)
                s = cmath.sin(delta)
                L = np.array([[c, -1j * s / eta_j], [-1j * eta_j * s, c]])
                M = M @ L

            num = M[0, 0] * eta0 + M[0, 1] * eta0 * etas - M[1, 0] - M[1, 1] * etas
            den = M[0, 0] * eta0 + M[0, 1] * eta0 * etas + M[1, 0] + M[1, 1] * etas
            return num / den

        return _kernel


_tmm_kernel = _make_kernel()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_spectrum(
    N_mat: np.ndarray,  # shape (n_layers, n_lam), complex128
    d_arr: np.ndarray,  # shape (n_layers,), float64, nm
    lam_array: np.ndarray,  # shape (n_lam,), float64, nm
    N0_arr: np.ndarray,  # shape (n_lam,), complex128, superstrate
    Ns_arr: np.ndarray,  # shape (n_lam,), complex128, substrate
    theta_deg: float = 0.0,
    pol: str = "s",
) -> np.ndarray:
    """Compute complex reflection coefficient r across a wavelength array.

    Parameters
    ----------
    N_mat      : complex N matrix, shape (n_layers, n_lam)
    d_arr      : layer thicknesses in nm, shape (n_layers,)
    lam_array  : wavelengths in nm
    N0_arr     : superstrate N per wavelength
    Ns_arr     : substrate N per wavelength
    theta_deg  : angle of incidence in degrees (default 0)
    pol        : 's' (TE) or 'p' (TM)

    Returns
    -------
    r : complex128 array, shape (n_lam,)
    """
    theta_rad = math.radians(theta_deg)
    pol_int = np.int8(0) if pol.lower() == "s" else np.int8(1)

    n_lam = len(lam_array)
    r = np.empty(n_lam, dtype=np.complex128)

    for i in range(n_lam):
        r[i] = _tmm_kernel(
            N_mat[:, i],
            d_arr,
            lam_array[i],
            theta_rad,
            N0_arr[i],
            Ns_arr[i],
            pol_int,
        )
    return r


def r_to_observables(r: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decompose r into (|r|, R, phase_rad)."""
    amp = np.abs(r)
    R = amp**2
    phase = np.angle(r)
    return amp, R, phase


def compute_na_spectrum(
    N_mat: np.ndarray,
    d_arr: np.ndarray,
    lam_array: np.ndarray,
    N0_arr: np.ndarray,
    Ns_arr: np.ndarray,
    na: float,
    pol: str = "both",
    n_quad: int = 20,
) -> np.ndarray:
    """Compute NA-integrated effective reflectance R_eff(λ).

    Integrates R(θ,λ) over a cone of illumination angles [0, θ_max] where
    θ_max = arcsin(NA / n0), weighted by sin(θ)cos(θ) (intensity-correct).

    Parameters
    ----------
    na    : numerical aperture of the objective (NA = n0 * sin(θ_max))
    pol   : 's', 'p', or 'both' (unpolarized — average of s and p)
    n_quad: number of Gauss-Legendre quadrature points (default 20)

    Returns
    -------
    R_eff : real array, shape (n_lam,)
    """
    n0_ref = N0_arr[len(N0_arr) // 2].real
    sin_max = na / n0_ref
    if sin_max >= 1.0:
        raise ValueError(f"NA={na:.3f} exceeds superstrate n0={n0_ref:.3f}")
    theta_max = math.asin(sin_max)

    nodes, weights = np.polynomial.legendre.leggauss(n_quad)
    theta_pts = 0.5 * theta_max * (nodes + 1)   # map [-1,1] → [0, θ_max]
    w_scaled = weights * 0.5 * theta_max

    R_accum = np.zeros(len(lam_array))
    W_accum = 0.0

    for theta_i, w_i in zip(theta_pts, w_scaled):
        factor = math.sin(theta_i) * math.cos(theta_i) * w_i
        deg = math.degrees(theta_i)
        if pol.lower() in ("s", "p"):
            r = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, pol)
            R_i = np.abs(r) ** 2
        else:  # unpolarized
            rs = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, "s")
            rp = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, "p")
            R_i = 0.5 * (np.abs(rs) ** 2 + np.abs(rp) ** 2)
        R_accum += factor * R_i
        W_accum += factor

    return R_accum / W_accum


def warm_up_jit() -> None:
    """Trigger Numba JIT compilation with a trivial 1-layer stack."""
    if not _NUMBA_AVAILABLE:
        return
    N_mat = np.array([[1.5 + 0j]], dtype=np.complex128)
    d_arr = np.array([100.0], dtype=np.float64)
    lam = np.array([550.0])
    N0 = np.array([1.0 + 0j])
    Ns = np.array([1.52 + 0j])
    compute_spectrum(N_mat, d_arr, lam, N0, Ns, 0.0, "s")
