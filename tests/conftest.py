"""
Shared pytest fixtures for reflecto_sim tests.

All fixtures here work without a GUI / display.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from reflecto_sim.materials import MaterialLibrary
from reflecto_sim.stack import LayerSpec, StackConfig


@pytest.fixture(scope="session")
def mat_dir() -> Path:
    """Return the path to the materials directory."""
    return Path(__file__).parent.parent / "materials"


@pytest.fixture(scope="session")
def lib(mat_dir: Path) -> MaterialLibrary:
    """MaterialLibrary loaded from the real materials/ directory."""
    library = MaterialLibrary()
    if mat_dir.exists():
        library.load_directory(mat_dir)
    return library


@pytest.fixture
def lam_vis() -> np.ndarray:
    """Visible wavelength array: 430–800 nm, 1 nm step."""
    return np.arange(430.0, 801.0, 1.0)


@pytest.fixture
def lam_broad() -> np.ndarray:
    """Broad wavelength array: 430–1500 nm, 2 nm step."""
    return np.arange(430.0, 1501.0, 2.0)


@pytest.fixture
def single_tio2_stack() -> StackConfig:
    """Air / TiO2 80 nm / SiO2 substrate."""
    return StackConfig(
        superstrate="air",
        substrate="sio2",
        layers=[LayerSpec(name="TiO2", material="tio2", thickness_nm=80.0)],
    )


@pytest.fixture
def two_layer_stack() -> StackConfig:
    """Air / TiO2 80 nm / SiO2 50 nm / glass substrate."""
    return StackConfig(
        superstrate="air",
        substrate="glass",
        layers=[
            LayerSpec(name="TiO2", material="tio2", thickness_nm=80.0),
            LayerSpec(name="SiO2", material="sio2", thickness_nm=50.0),
        ],
    )
