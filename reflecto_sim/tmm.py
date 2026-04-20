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
    from numba import njit, prange, complex128, float64, int8

    _NUMBA_AVAILABLE = True
except ImportError:
    _NUMBA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Numba JIT kernel — compiled once, cached to disk
# ---------------------------------------------------------------------------


def _make_kernels():
    """Return JIT-compiled or pure-Python TMM kernels (single + batch)."""

    if _NUMBA_AVAILABLE:

        @njit(cache=True)
        def _single(N_layers, d_layers, lam_nm, theta_rad, N0, Ns, pol):
            """Compute (r, t) for one wavelength.

            Parameters
            ----------
            N_layers : complex128[n_layers]   complex refractive indices
            d_layers : float64[n_layers]      layer thicknesses (nm)
            lam_nm   : float64                wavelength (nm)
            theta_rad: float64                angle of incidence in superstrate (rad)
            N0       : complex128             superstrate N
            Ns       : complex128             substrate N
            pol      : int8                   0 = s/TE, 1 = p/TM

            Returns
            -------
            (r, t) : complex reflection and transmission coefficients
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

            # Reflection and transmission coefficients
            den = M00 * eta0 + M01 * eta0 * etas + M10 + M11 * etas
            num_r = M00 * eta0 + M01 * eta0 * etas - M10 - M11 * etas
            r = num_r / den
            t = (2.0 * eta0) / den
            return r, t

        @njit(cache=True, parallel=True)
        def _batch(N_mat, d_arr, lam_array, theta_rad, N0_arr, Ns_arr, pol):
            """Compute (r, t) arrays for all wavelengths in parallel."""
            n = len(lam_array)
            r_out = np.empty(n, dtype=np.complex128)
            t_out = np.empty(n, dtype=np.complex128)
            for i in prange(n):
                r_out[i], t_out[i] = _single(
                    N_mat[:, i], d_arr, lam_array[i], theta_rad,
                    N0_arr[i], Ns_arr[i], pol
                )
            return r_out, t_out

        return _single, _batch

    else:
        # Pure-Python fallback (no Numba)
        def _single(N_layers, d_layers, lam_nm, theta_rad, N0, Ns, pol):
            TWO_PI = 2.0 * math.pi
            k0 = TWO_PI / lam_nm
            sin_t = cmath.sin(complex(theta_rad))
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
                if pol == 0:
                    eta_j = kzj / k0
                else:
                    eta_j = (Nj**2) * k0 / kzj
                c = cmath.cos(delta)
                s = cmath.sin(delta)
                L = np.array([[c, -1j * s / eta_j], [-1j * eta_j * s, c]])
                M = M @ L

            den = M[0, 0] * eta0 + M[0, 1] * eta0 * etas + M[1, 0] + M[1, 1] * etas
            num_r = M[0, 0] * eta0 + M[0, 1] * eta0 * etas - M[1, 0] - M[1, 1] * etas
            r = num_r / den
            t = (2.0 * eta0) / den
            return r, t

        def _batch(N_mat, d_arr, lam_array, theta_rad, N0_arr, Ns_arr, pol):
            n = len(lam_array)
            r_out = np.empty(n, dtype=np.complex128)
            t_out = np.empty(n, dtype=np.complex128)
            for i in range(n):
                r_out[i], t_out[i] = _single(
                    N_mat[:, i], d_arr, lam_array[i], theta_rad,
                    N0_arr[i], Ns_arr[i], pol
                )
            return r_out, t_out

        return _single, _batch


_tmm_single, _tmm_batch = _make_kernels()


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
) -> tuple[np.ndarray, np.ndarray]:
    """Compute complex reflection and transmission coefficients across wavelengths.

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
    (r, t) : complex128 arrays, shape (n_lam,)
    """
    theta_rad = math.radians(theta_deg)
    pol_int = np.int8(0) if pol.lower() == "s" else np.int8(1)
    return _tmm_batch(N_mat, d_arr, lam_array, theta_rad, N0_arr, Ns_arr, pol_int)


def r_to_observables(r: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decompose r into (|r|, R, phase_rad)."""
    amp = np.abs(r)
    R = amp**2
    phase = np.angle(r)
    return amp, R, phase


def t_to_observables(
    t: np.ndarray,
    N0_arr: np.ndarray,
    Ns_arr: np.ndarray,
    theta_deg: float,
    pol: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decompose t into (|t|, T, phase_rad).

    Transmittance T = |t|² × Re(η_s) / Re(η_0), using the admittance
    convention of the TMM kernel (handles both TE and TM correctly).

    Parameters
    ----------
    t        : complex transmission coefficient array, shape (n_lam,)
    N0_arr   : superstrate N per wavelength
    Ns_arr   : substrate N per wavelength
    theta_deg: angle of incidence in degrees
    pol      : 's' (TE) or 'p' (TM); 'both' treated as 's'
    """
    sin_t = math.sin(math.radians(theta_deg))
    # kz components (complex) — dimensionless (= N·cos θ in medium)
    kz0 = np.sqrt(N0_arr**2 - (N0_arr * sin_t) ** 2)
    kzs = np.sqrt(Ns_arr**2 - (N0_arr * sin_t) ** 2)

    pol_lower = pol.lower()
    if pol_lower in ("s", "both"):
        eta0 = kz0
        etas = kzs
    else:  # p / TM
        eta0 = N0_arr**2 / kz0
        etas = Ns_arr**2 / kzs

    T = np.abs(t) ** 2 * np.real(etas) / np.real(eta0)
    return np.abs(t), T, np.angle(t)


def compute_na_spectrum(
    N_mat: np.ndarray,
    d_arr: np.ndarray,
    lam_array: np.ndarray,
    N0_arr: np.ndarray,
    Ns_arr: np.ndarray,
    na: float,
    pol: str = "both",
    n_quad: int = 20,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute NA-integrated effective reflectance and transmittance.

    Integrates R(θ,λ) and T(θ,λ) over a cone of illumination angles
    [0, θ_max] where θ_max = arcsin(NA / n0), weighted by sin(θ)cos(θ).

    Parameters
    ----------
    na    : numerical aperture of the objective (NA = n0 * sin(θ_max))
    pol   : 's', 'p', or 'both' (unpolarized — average of s and p)
    n_quad: number of Gauss-Legendre quadrature points (default 20)

    Returns
    -------
    (R_eff, T_eff) : real arrays, shape (n_lam,)
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
    T_accum = np.zeros(len(lam_array))
    W_accum = 0.0

    for theta_i, w_i in zip(theta_pts, w_scaled):
        factor = math.sin(theta_i) * math.cos(theta_i) * w_i
        deg = math.degrees(theta_i)
        if pol.lower() in ("s", "p"):
            r_i, t_i = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, pol)
            R_i = np.abs(r_i) ** 2
            T_i = t_to_observables(t_i, N0_arr, Ns_arr, deg, pol)[1]
        else:  # unpolarized
            r_s, t_s = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, "s")
            r_p, t_p = compute_spectrum(N_mat, d_arr, lam_array, N0_arr, Ns_arr, deg, "p")
            R_i = 0.5 * (np.abs(r_s) ** 2 + np.abs(r_p) ** 2)
            T_i = 0.5 * (
                t_to_observables(t_s, N0_arr, Ns_arr, deg, "s")[1]
                + t_to_observables(t_p, N0_arr, Ns_arr, deg, "p")[1]
            )
        R_accum += factor * R_i
        T_accum += factor * T_i
        W_accum += factor

    return R_accum / W_accum, T_accum / W_accum


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
