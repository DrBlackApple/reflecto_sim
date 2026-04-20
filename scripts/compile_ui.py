"""
Compile all .ui files in reflecto_sim/ui/ui/ → reflecto_sim/ui/ui_compiled/ui_*.py

Usage
-----
    python scripts/compile_ui.py

Run this every time you edit a .ui file in Qt Designer.
The generated files are committed to the repo so the app runs without
any build step for normal users.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "reflecto_sim" / "ui" / "ui"
OUT_DIR = ROOT / "reflecto_sim" / "ui" / "ui_compiled"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    init = OUT_DIR / "__init__.py"
    if not init.exists():
        init.write_text("# generated — do not edit\n")

    ui_files = sorted(UI_DIR.glob("*.ui"))
    if not ui_files:
        print(f"No .ui files found in {UI_DIR}")
        sys.exit(1)

    def _find_uic() -> list[str]:
        candidates = [
            Path(sys.executable).parent / "Scripts" / "pyside6-uic.exe",
            Path(sys.executable).parent / "pyside6-uic.exe",
            Path(sys.executable).parent.parent / "Scripts" / "pyside6-uic.exe",
        ]
        import site
        user_site = site.getusersitepackages()
        if isinstance(user_site, str):
            user_site = [user_site]
        for sp in user_site:
            candidates.append(Path(sp).parent.parent / "Scripts" / "pyside6-uic.exe")
        for c in candidates:
            if c.exists():
                return [str(c)]
        return ["pyside6-uic"]  # rely on PATH

    uic_cmd = _find_uic()

    errors = 0
    for ui_path in ui_files:
        out_path = OUT_DIR / f"ui_{ui_path.stem}.py"
        result = subprocess.run(
            uic_cmd + [str(ui_path), "-o", str(out_path)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  OK  {ui_path.name} -> {out_path.name}")
        else:
            print(f"  FAIL {ui_path.name}: {result.stderr.strip()}")
            errors += 1

    if errors:
        print(f"\n{errors} file(s) failed to compile.")
        sys.exit(1)
    else:
        print(f"\nCompiled {len(ui_files)} file(s) successfully.")


if __name__ == "__main__":
    main()
