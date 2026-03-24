"""Effective medium approximations for mixed-material layers.

All models accept complex N arrays for two materials and a volume fraction f
(fraction of material A), operating on permittivity eps = N^2.
Returns N_eff = sqrt(eps_eff), choosing the root with Im(N_eff) >= 0.
"""

from __future__ import annotations

import numpy as np


def _safe_sqrt(eps: np.ndarray) -> np.ndarray:
    """Complex square root with Im >= 0 convention."""
    N = np.sqrt(eps.astype(np.complex128))
    # Flip sign where imaginary part is negative
    N = np.where(N.imag < 0, -N, N)
    return N


def linear(N_a: np.ndarray, N_b: np.ndarray, f: float) -> np.ndarray:
    """Volume-weighted linear mixing of permittivities.

    eps_eff = f * eps_a + (1 - f) * eps_b
    """
    N_a = np.asarray(N_a, dtype=np.complex128)
    N_b = np.asarray(N_b, dtype=np.complex128)
    eps_a = N_a ** 2
    eps_b = N_b ** 2
    eps_eff = f * eps_a + (1.0 - f) * eps_b
    return _safe_sqrt(eps_eff)


def maxwell_garnett(N_a: np.ndarray, N_b: np.ndarray, f: float) -> np.ndarray:
    """Maxwell Garnett model: inclusions of A embedded in host B.

    eps_eff = eps_b * (eps_a + 2*eps_b + 2*f*(eps_a - eps_b))
                    / (eps_a + 2*eps_b -   f*(eps_a - eps_b))
    """
    N_a = np.asarray(N_a, dtype=np.complex128)
    N_b = np.asarray(N_b, dtype=np.complex128)
    eps_a = N_a ** 2
    eps_b = N_b ** 2
    delta = eps_a - eps_b
    num = eps_a + 2 * eps_b + 2 * f * delta
    den = eps_a + 2 * eps_b - f * delta
    eps_eff = eps_b * num / den
    return _safe_sqrt(eps_eff)


def bruggeman(N_a: np.ndarray, N_b: np.ndarray, f: float) -> np.ndarray:
    """Bruggeman symmetric effective medium (self-consistent).

    Analytical solution of the quadratic:
      f*(eps_a - eps_eff)/(eps_a + 2*eps_eff)
      + (1-f)*(eps_b - eps_eff)/(eps_b + 2*eps_eff) = 0

    => eps_eff = (b + sqrt(b^2 + 8*eps_a*eps_b)) / 4
       where b = (3f - 1)*eps_a + (2 - 3f)*eps_b
    """
    N_a = np.asarray(N_a, dtype=np.complex128)
    N_b = np.asarray(N_b, dtype=np.complex128)
    eps_a = N_a ** 2
    eps_b = N_b ** 2
    b = (3.0 * f - 1.0) * eps_a + (2.0 - 3.0 * f) * eps_b
    discriminant = b ** 2 + 8.0 * eps_a * eps_b
    eps_eff = (b + np.sqrt(discriminant.astype(np.complex128))) / 4.0
    result = _safe_sqrt(eps_eff)
    # Bruggeman can return two roots; pick the physical one (Im >= 0, Re > 0)
    alt = _safe_sqrt((b - np.sqrt(discriminant.astype(np.complex128))) / 4.0)
    use_alt = (result.real < 0) & (alt.real >= 0)
    result = np.where(use_alt, alt, result)
    return result


MODELS = {
    "Bruggeman": bruggeman,
    "Maxwell Garnett": maxwell_garnett,
    "Linear": linear,
}


def mix(N_a: np.ndarray, N_b: np.ndarray, f: float,
        model: str = "Bruggeman") -> np.ndarray:
    """Dispatch to a mixing model by name."""
    if model not in MODELS:
        raise ValueError(f"Unknown mixing model '{model}'. Choose from {list(MODELS)}")
    return MODELS[model](N_a, N_b, f)
