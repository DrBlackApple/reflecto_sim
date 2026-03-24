"""Entry point for reflecto_sim — Reflectometry Simulator."""

from pathlib import Path

from reflecto_sim.materials import MaterialLibrary
from reflecto_sim.ui.app import ReflectoApp


def main():
    lib = MaterialLibrary()
    mat_dir = Path(__file__).parent / "materials"
    if mat_dir.exists():
        loaded = lib.load_directory(mat_dir)
        print(f"Loaded materials: {loaded}")
    else:
        print(f"Warning: materials directory not found at {mat_dir}")

    app = ReflectoApp(lib)
    app.mainloop()


if __name__ == "__main__":
    main()
