# reflecto_sim

A Transfer Matrix Method (TMM) optical reflectometry simulator for multilayer thin-film stacks. Computes complex reflectance spectra (amplitude, reflectance, phase) as a function of wavelength, angle of incidence, and polarization.

## Features

- **Rigorous TMM physics** — full 2×2 transfer matrix formulation for TE/TM polarizations and oblique incidence
- **Flexible material library** — tabulated n,k data (cubic-spline interpolated) and analytical models (Drude, Lorentz, Sellmeier, Cauchy, Graphene Kubo)
- **Effective medium mixing** — Bruggeman, Maxwell-Garnett, and linear mixing for composite layers
- **NA-integrated reflectance** — Gauss-Legendre weighted cone integration for finite numerical apertures
- **Numba JIT compilation** — near-C performance with transparent Python fallback
- **Interactive GUI** — dark-themed Tkinter application with live matplotlib plots (|r|, R, φ)
- **Parameter sweeps** — vary material composition or material identity across a layer
- **JSON stack persistence** — save and reload optical stack configurations

## Installation

```bash
pip install -r requirements.txt
```

Dependencies: `numpy`, `scipy`, `matplotlib`, `numba` (optional but recommended).

## Usage

### GUI

```bash
python main.py
```

The interface has three panels:

- **Left** — stack editor: add/remove/reorder layers, set material and thickness, configure mixing
- **Centre** — plots: amplitude |r|(λ), reflectance R(λ), phase φ(λ)
- **Right** — simulation controls: wavelength range, angle, polarization, NA mode, compute button

### Programmatic

```python
import numpy as np
from reflecto_sim.materials import MaterialLibrary
from reflecto_sim.stack import StackConfig, LayerSpec, resolve_stack, build_N_matrix
from reflecto_sim.tmm import compute_spectrum, r_to_observables

lib = MaterialLibrary()
lib.load_directory("materials/")

stack = StackConfig(
    superstrate="air",
    substrate="glass",
    layers=[
        LayerSpec(name="TiO2", material="tio2", thickness_nm=80),
        LayerSpec(name="Au",   material="gold_drude", thickness_nm=30),
    ]
)

lam = np.linspace(400, 800, 401)
resolved, N0_arr, Ns_arr = resolve_stack(stack, lam, lib)
N_mat, d_arr = build_N_matrix(resolved)

r = compute_spectrum(N_mat, d_arr, lam, N0_arr, Ns_arr, theta_deg=0, pol="s")
amp, R, phase = r_to_observables(r)
```

## Project Structure

```
reflecto_sim/
├── main.py                  # Entry point
├── requirements.txt
├── materials/               # Optical data (.txt tabulated, .json analytical)
└── reflecto_sim/
    ├── tmm.py               # TMM physics kernel (Numba JIT)
    ├── materials.py         # Material library and dispersion models
    ├── stack.py             # Stack/layer definitions and resolution
    ├── eff_medium.py        # Effective medium mixing models
    └── ui/
        ├── app.py           # Main application window
        ├── stack_editor.py  # Layer editor widget
        └── plot_panel.py    # Matplotlib plot panel
```

## How to Cite

If you use reflecto_sim in academic work, please cite it as:

> Herlent, J. (2026). *reflecto_sim: A Transfer Matrix Method optical reflectometry simulator* [Software]. Retrieved from https://github.com/DrBlackApple/reflecto_sim

Or in BibTeX:

```bibtex
@software{herlent2026reflectosim,
  author  = {Herlent, J.},
  title   = {reflecto\textunderscore sim: A Transfer Matrix Method optical reflectometry simulator},
  year    = {2026},
  url     = {https://github.com/DrBlackApple/reflecto_sim}
}
```

## License

See [LICENSE](LICENSE) for details.
