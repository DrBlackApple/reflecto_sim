"""Stack definition and builder for multilayer reflectometry simulations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import interp1d

if TYPE_CHECKING:
    from .materials import MaterialLibrary


@dataclass
class LayerSpec:
    """Specification for a single layer (before wavelength resolution)."""
    name: str
    material: str          # key in MaterialLibrary, or "mixed:..." for composite
    thickness_nm: float
    # For mixed layers only:
    mix_mat_b: str = ""
    mix_f: float = 0.5
    mix_model: str = "Bruggeman"
    # Sweep configuration (stored per-layer, persists in JSON):
    sweep_mode: str = ""           # "" | "material" | "mix"
    sweep_materials: list = field(default_factory=list)   # material sweep list
    sweep_mat_b: str = ""          # mix sweep: second material
    sweep_mix_model: str = "Bruggeman"
    sweep_n_pts: int = 11

    def is_mixed(self) -> bool:
        return bool(self.mix_mat_b)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "material": self.material,
            "thickness_nm": self.thickness_nm,
            "mix_mat_b": self.mix_mat_b,
            "mix_f": self.mix_f,
            "mix_model": self.mix_model,
            "sweep_mode": self.sweep_mode,
            "sweep_materials": list(self.sweep_materials),
            "sweep_mat_b": self.sweep_mat_b,
            "sweep_mix_model": self.sweep_mix_model,
            "sweep_n_pts": self.sweep_n_pts,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LayerSpec":
        return cls(
            name=d["name"],
            material=d["material"],
            thickness_nm=float(d["thickness_nm"]),
            mix_mat_b=d.get("mix_mat_b", ""),
            mix_f=float(d.get("mix_f", 0.5)),
            mix_model=d.get("mix_model", "Bruggeman"),
            sweep_mode=d.get("sweep_mode", ""),
            sweep_materials=list(d.get("sweep_materials", [])),
            sweep_mat_b=d.get("sweep_mat_b", ""),
            sweep_mix_model=d.get("sweep_mix_model", "Bruggeman"),
            sweep_n_pts=int(d.get("sweep_n_pts", 11)),
        )


@dataclass
class ResolvedLayer:
    """A layer with N(lambda) already interpolated."""
    name: str
    material_label: str
    thickness_nm: float
    N: np.ndarray   # complex128, shape (n_lam,)


@dataclass
class StackConfig:
    """Full stack configuration including superstrate, layers, substrate."""
    superstrate: str = "air"
    substrate: str = "glass"
    layers: list[LayerSpec] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "superstrate": self.superstrate,
            "substrate": self.substrate,
            "layers": [l.to_dict() for l in self.layers],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StackConfig":
        return cls(
            superstrate=d.get("superstrate", "air"),
            substrate=d.get("substrate", "glass"),
            layers=[LayerSpec.from_dict(l) for l in d.get("layers", [])],
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "StackConfig":
        return cls.from_dict(json.loads(Path(path).read_text()))


def resolve_stack(
    config: StackConfig,
    lam_array: np.ndarray,
    lib: "MaterialLibrary",
) -> tuple[list[ResolvedLayer], np.ndarray, np.ndarray]:
    """Resolve a StackConfig into ResolvedLayers and N arrays.

    Returns
    -------
    layers   : list of ResolvedLayer (N arrays populated)
    N0_arr   : superstrate N, shape (n_lam,)
    Ns_arr   : substrate  N, shape (n_lam,)
    """
    from .eff_medium import mix

    resolved: list[ResolvedLayer] = []
    for spec in config.layers:
        if spec.is_mixed():
            Na = lib.N(spec.material, lam_array)
            Nb = lib.N(spec.mix_mat_b, lam_array)
            N_arr = mix(Na, Nb, spec.mix_f, spec.mix_model)
            label = f"{spec.material}/{spec.mix_mat_b} f={spec.mix_f:.2f}"
        else:
            N_arr = lib.N(spec.material, lam_array)
            label = lib.label(spec.material)

        resolved.append(ResolvedLayer(
            name=spec.name,
            material_label=label,
            thickness_nm=spec.thickness_nm,
            N=N_arr,
        ))

    N0_arr = lib.N(config.superstrate, lam_array)
    Ns_arr = lib.N(config.substrate, lam_array)
    return resolved, N0_arr, Ns_arr


def build_N_matrix(layers: list[ResolvedLayer]) -> tuple[np.ndarray, np.ndarray]:
    """Stack layer N arrays into a matrix for the TMM kernel.

    Returns
    -------
    N_mat : shape (n_layers, n_lam), complex128
    d_arr : shape (n_layers,),       float64  (thicknesses in nm)
    """
    if not layers:
        raise ValueError("Stack is empty — add at least one layer.")
    N_mat = np.stack([l.N for l in layers], axis=0)
    d_arr = np.array([l.thickness_nm for l in layers], dtype=np.float64)
    return N_mat, d_arr
