"""
ComputeWorker — QObject-based computation back-end.

Runs on a dedicated QThread.  Emits signals with results; never touches
widgets directly.  All physics code is imported from the non-UI modules.
"""

from __future__ import annotations

import copy
import math

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from ..materials import MaterialLibrary, MaterialRangeError
from ..stack import StackConfig, resolve_stack, build_N_matrix
from ..tmm import (
    compute_spectrum,
    compute_na_spectrum,
    r_to_observables,
    t_to_observables,
    warm_up_jit,
)


class ComputeWorker(QObject):
    """
    Worker that runs TMM computations on a background QThread.

    Signals
    -------
    result_ready(dict)
        Emitted when computation succeeds.  The dict has a ``mode`` key:
        ``"spectrum"`` | ``"na"`` | ``"sweep"`` | ``"mix_sweep"``.
    error_occurred(str)
        Emitted on handled errors (MaterialRangeError, ValueError…).
    progress_changed(str)
        Status text updates during sweep iterations or JIT warmup.
    """

    result_ready    = Signal(object)
    error_occurred  = Signal(str)
    progress_changed = Signal(str)

    def __init__(self, lib: MaterialLibrary, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._lib = lib

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------

    @Slot()
    def warmup(self) -> None:
        """Pre-compile Numba JIT kernels in background."""
        try:
            warm_up_jit()
            self.progress_changed.emit("Ready (JIT compiled)")
        except Exception as exc:
            self.progress_changed.emit(f"JIT warmup failed: {exc}")

    @Slot(object)
    def run(self, params: dict) -> None:
        """Dispatch to the appropriate computation based on params['mode']."""
        mode = params.get("mode", "spectrum")
        try:
            if mode == "spectrum":
                self._run_spectrum(params)
            elif mode == "na":
                self._run_na(params)
            elif mode == "sweep":
                self._run_sweep(params)
            elif mode == "mix_sweep":
                self._run_mix_sweep(params)
            else:
                self.error_occurred.emit(f"Unknown compute mode: {mode}")
        except MaterialRangeError as exc:
            self.error_occurred.emit(f"Range error: {exc}")
        except Exception as exc:
            self.error_occurred.emit(f"Error: {exc}")

    # ------------------------------------------------------------------
    # Internal computation helpers
    # ------------------------------------------------------------------

    def _run_spectrum(self, params: dict) -> None:
        lam_array: np.ndarray = params["lam_array"]
        config: StackConfig    = params["config"]
        theta: float           = params["theta"]
        pol: str               = params["pol"]

        layers, N0_arr, Ns_arr = resolve_stack(config, lam_array, self._lib)
        N_mat, d_arr = build_N_matrix(layers)
        r, t = compute_spectrum(
            N_mat, d_arr, lam_array, N0_arr, Ns_arr,
            theta_deg=theta, pol=pol,
        )
        amp, R, phi = r_to_observables(r)
        amp_t, T_t, phi_t = t_to_observables(t, N0_arr, Ns_arr, theta, pol)

        self.result_ready.emit({
            "mode":   "spectrum",
            "lam":    lam_array,
            "r":      r,
            "t":      t,
            "amp":    amp,
            "R":      R,
            "phi":    phi,
            "amp_t":  amp_t,
            "T_t":    T_t,
            "phi_t":  phi_t,
            "N0_arr": N0_arr,
            "Ns_arr": Ns_arr,
        })

    def _run_na(self, params: dict) -> None:
        lam_array: np.ndarray = params["lam_array"]
        config: StackConfig    = params["config"]
        na_val: float          = params["na_val"]
        pol: str               = params["pol"]

        layers, N0_arr, Ns_arr = resolve_stack(config, lam_array, self._lib)
        N_mat, d_arr = build_N_matrix(layers)
        R_eff, T_eff = compute_na_spectrum(
            N_mat, d_arr, lam_array, N0_arr, Ns_arr,
            na=na_val, pol=pol,
        )
        n0_ref = float(N0_arr[len(N0_arr) // 2].real)
        theta_max_deg = math.degrees(math.asin(min(na_val / n0_ref, 1.0)))

        self.result_ready.emit({
            "mode":          "na",
            "lam":           lam_array,
            "R_eff":         R_eff,
            "T_eff":         T_eff,
            "na_val":        na_val,
            "theta_max_deg": theta_max_deg,
        })

    def _run_sweep(self, params: dict) -> None:
        lam_array: np.ndarray = params["lam_array"]
        base_config: StackConfig = params["config"]
        layer_idx: int           = params["layer_index"]
        materials: list[str]     = params["materials"]
        theta: float             = params["theta"]
        pol: str                 = params["pol"]
        use_na: bool             = params.get("use_na", False)
        na_val: float            = params.get("na_val", 0.0)
        pol_single               = pol if pol != "both" else "s"

        results = []
        errors  = []
        total   = len(materials)

        for idx, mat in enumerate(materials):
            self.progress_changed.emit(f"Sweep: {idx}/{total}…")
            try:
                cfg = copy.deepcopy(base_config)
                cfg.layers[layer_idx].material = mat
                layers, N0_arr, Ns_arr = resolve_stack(cfg, lam_array, self._lib)
                N_mat, d_arr = build_N_matrix(layers)
                if use_na:
                    R_eff, T_eff = compute_na_spectrum(
                        N_mat, d_arr, lam_array, N0_arr, Ns_arr,
                        na=na_val, pol=pol,
                    )
                    results.append({
                        "label": mat, "lam": lam_array,
                        "amp": None, "R": R_eff, "phi": None,
                        "amp_t": None, "T_t": T_eff, "phi_t": None,
                        "is_na": True,
                    })
                else:
                    r, t = compute_spectrum(
                        N_mat, d_arr, lam_array, N0_arr, Ns_arr,
                        theta_deg=theta, pol=pol_single,
                    )
                    amp, R, phi = r_to_observables(r)
                    amp_t, T_t, phi_t = t_to_observables(
                        t, N0_arr, Ns_arr, theta, pol_single
                    )
                    results.append({
                        "label": mat, "lam": lam_array,
                        "amp": amp, "R": R, "phi": phi,
                        "amp_t": amp_t, "T_t": T_t, "phi_t": phi_t,
                        "is_na": False,
                    })
            except (MaterialRangeError, Exception):
                errors.append(mat)

        self.result_ready.emit({
            "mode":    "sweep",
            "results": results,
            "errors":  errors,
        })

    def _run_mix_sweep(self, params: dict) -> None:
        lam_array: np.ndarray    = params["lam_array"]
        base_config: StackConfig = params["config"]
        layer_idx: int           = params["layer_index"]
        mat_a: str               = params["mat_a"]
        mat_b: str               = params["mat_b"]
        model: str               = params["model"]
        f_values: list[float]    = params["f_values"]
        theta: float             = params["theta"]
        pol: str                 = params["pol"]
        use_na: bool             = params.get("use_na", False)
        na_val: float            = params.get("na_val", 0.0)
        pol_single               = pol if pol != "both" else "s"

        results = []
        errors  = []
        total   = len(f_values)

        for idx, f in enumerate(f_values):
            self.progress_changed.emit(f"Mix sweep: {idx}/{total}…")
            try:
                cfg = copy.deepcopy(base_config)
                layer = cfg.layers[layer_idx]
                layer.material  = mat_a
                layer.mix_mat_b = mat_b
                layer.mix_f     = float(f)
                layer.mix_model = model
                layers, N0_arr, Ns_arr = resolve_stack(cfg, lam_array, self._lib)
                N_mat, d_arr = build_N_matrix(layers)
                if use_na:
                    R_eff, T_eff = compute_na_spectrum(
                        N_mat, d_arr, lam_array, N0_arr, Ns_arr,
                        na=na_val, pol=pol,
                    )
                    results.append({
                        "f": float(f), "lam": lam_array,
                        "amp": None, "R": R_eff, "phi": None,
                        "amp_t": None, "T_t": T_eff, "phi_t": None,
                        "is_na": True,
                    })
                else:
                    r, t = compute_spectrum(
                        N_mat, d_arr, lam_array, N0_arr, Ns_arr,
                        theta_deg=theta, pol=pol_single,
                    )
                    amp, R, phi = r_to_observables(r)
                    amp_t, T_t, phi_t = t_to_observables(
                        t, N0_arr, Ns_arr, theta, pol_single
                    )
                    results.append({
                        "f": float(f), "lam": lam_array,
                        "amp": amp, "R": R, "phi": phi,
                        "amp_t": amp_t, "T_t": T_t, "phi_t": phi_t,
                        "is_na": False,
                    })
            except (MaterialRangeError, Exception):
                errors.append(float(f))

        self.result_ready.emit({
            "mode":    "mix_sweep",
            "mat_a":   mat_a,
            "mat_b":   mat_b,
            "results": results,
            "errors":  errors,
        })
