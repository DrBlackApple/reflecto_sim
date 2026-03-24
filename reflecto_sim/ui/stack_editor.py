"""Layer stack editor widget — list of layers with controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from ..stack import LayerSpec, StackConfig
from .plot_panel import PALETTE, BG_DARK, AX_BG, LABEL_COL, SPINE_COL, TICK_COL

# Consistent widget colours
BTN_BG = "#1e1e3a"
BTN_FG = "#ccccee"
ENTRY_BG = "#1a1a2e"


def _swatch(idx: int) -> str:
    return PALETTE[idx % len(PALETTE)]


class LayerRow(tk.Frame):
    """A single row in the layer editor representing one LayerSpec."""

    def __init__(
        self,
        parent,
        spec: LayerSpec,
        index: int,
        materials: list[str],
        on_change: Callable,
        on_delete: Callable[[int], None],
        on_move: Callable[[int, int], None],
        **kw,
    ):
        super().__init__(parent, bg=AX_BG, pady=2, padx=4, **kw)
        self._spec = spec
        self._index = index
        self._on_change = on_change
        self._materials = materials

        col = _swatch(index)

        # Colour indicator
        tk.Frame(self, bg=col, width=6).pack(side=tk.LEFT, fill=tk.Y)

        # Layer name
        self._name_var = tk.StringVar(value=spec.name)
        name_entry = tk.Entry(
            self,
            textvariable=self._name_var,
            width=10,
            bg=ENTRY_BG,
            fg=LABEL_COL,
            insertbackground=LABEL_COL,
            relief=tk.FLAT,
            font=("Consolas", 9),
        )
        name_entry.pack(side=tk.LEFT, padx=(4, 2))
        self._name_var.trace_add("write", lambda *_: self._sync_name())

        # Material dropdown
        self._mat_var = tk.StringVar(value=spec.material)
        self._mat_cb = ttk.Combobox(
            self,
            textvariable=self._mat_var,
            values=materials,
            width=14,
            font=("Consolas", 9),
        )
        self._mat_cb.pack(side=tk.LEFT, padx=2)
        self._mat_var.trace_add("write", lambda *_: self._sync_material())

        # Thickness
        tk.Label(self, text="d:", bg=AX_BG, fg=TICK_COL, font=("Consolas", 9)).pack(
            side=tk.LEFT
        )
        self._thick_var = tk.StringVar(value=str(spec.thickness_nm))
        thick_entry = tk.Entry(
            self,
            textvariable=self._thick_var,
            width=7,
            bg=ENTRY_BG,
            fg=LABEL_COL,
            insertbackground=LABEL_COL,
            relief=tk.FLAT,
            font=("Consolas", 9),
        )
        thick_entry.pack(side=tk.LEFT, padx=2)
        self._thick_var.trace_add("write", lambda *_: self._sync_thickness())

        tk.Label(self, text="nm", bg=AX_BG, fg=TICK_COL, font=("Consolas", 8)).pack(
            side=tk.LEFT
        )

        # Sweep button
        self._sweep_btn = tk.Button(
            self,
            text=self._sweep_label(),
            width=3,
            command=self._open_sweep_config,
            relief=tk.FLAT,
            font=("Consolas", 8),
        )
        self._sweep_btn.pack(side=tk.LEFT, padx=(4, 1))
        self._refresh_sweep_btn()

        # Move buttons
        tk.Button(
            self,
            text="↑",
            width=2,
            command=lambda: on_move(index, -1),
            bg=BTN_BG,
            fg=BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
        ).pack(side=tk.RIGHT, padx=1)
        tk.Button(
            self,
            text="↓",
            width=2,
            command=lambda: on_move(index, +1),
            bg=BTN_BG,
            fg=BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
        ).pack(side=tk.RIGHT, padx=1)

        # Delete
        tk.Button(
            self,
            text="×",
            width=2,
            command=lambda: on_delete(index),
            bg="#3a0a0a",
            fg="#ff8888",
            relief=tk.FLAT,
            font=("Consolas", 9),
        ).pack(side=tk.RIGHT, padx=(1, 4))

    def _sync_name(self):
        self._spec.name = self._name_var.get()
        self._on_change()

    def _sync_material(self):
        self._spec.material = self._mat_var.get()
        self._on_change()

    def _sync_thickness(self):
        try:
            self._spec.thickness_nm = float(self._thick_var.get())
            self._on_change()
        except ValueError:
            pass

    def destroy(self):
        try:
            self._mat_cb.configure(textvariable="")
        except Exception:
            pass
        super().destroy()

    def update_materials(self, materials: list[str]) -> None:
        self._materials = materials
        self._mat_cb["values"] = materials

    def _sweep_label(self) -> str:
        mode = self._spec.sweep_mode
        if mode == "material":
            return "⊕M"
        if mode == "mix":
            return "⊕X"
        return "≈"

    def _refresh_sweep_btn(self) -> None:
        mode = self._spec.sweep_mode
        if mode:
            self._sweep_btn.config(
                text=self._sweep_label(), bg="#1a2a3a", fg="#00BFFF"
            )
        else:
            self._sweep_btn.config(text="≈", bg=BTN_BG, fg=TICK_COL)

    def _open_sweep_config(self) -> None:
        dlg = LayerSweepDialog(self, self._spec, self._materials)
        if dlg.applied:
            self._refresh_sweep_btn()
            self._on_change()


class MixedLayerDialog(tk.Toplevel):
    """Dialog to configure a mixed-material layer."""

    def __init__(self, parent, materials: list[str], existing: LayerSpec | None = None):
        super().__init__(parent)
        self.title("Mixed layer")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.result: LayerSpec | None = None

        pad = {"padx": 8, "pady": 4}

        def row(label, widget_factory, row_idx):
            tk.Label(
                self, text=label, bg=BG_DARK, fg=LABEL_COL, font=("Consolas", 9)
            ).grid(row=row_idx, column=0, sticky="e", **pad)
            w = widget_factory()
            w.grid(row=row_idx, column=1, sticky="ew", **pad)
            return w

        # Name
        self._name = tk.StringVar(value=existing.name if existing else "Mixed")
        row(
            "Name:",
            lambda: tk.Entry(
                self,
                textvariable=self._name,
                width=14,
                bg=ENTRY_BG,
                fg=LABEL_COL,
                insertbackground=LABEL_COL,
                relief=tk.FLAT,
                font=("Consolas", 9),
            ),
            0,
        )

        # Material A
        self._mat_a = tk.StringVar(
            value=existing.material if existing else (materials[0] if materials else "")
        )
        row(
            "Material A (f):",
            lambda: ttk.Combobox(
                self,
                textvariable=self._mat_a,
                values=materials,
                width=14,
                font=("Consolas", 9),
            ),
            1,
        )

        # Material B
        self._mat_b = tk.StringVar(
            value=(
                existing.mix_mat_b
                if existing
                else (materials[1] if len(materials) > 1 else "")
            )
        )
        row(
            "Material B (1-f):",
            lambda: ttk.Combobox(
                self,
                textvariable=self._mat_b,
                values=materials,
                width=14,
                font=("Consolas", 9),
            ),
            2,
        )

        # Volume fraction
        self._f = tk.DoubleVar(value=existing.mix_f if existing else 0.5)
        f_frame = tk.Frame(self, bg=BG_DARK)
        self._f_label = tk.Label(
            f_frame,
            text=f"{self._f.get():.2f}",
            bg=BG_DARK,
            fg=TICK_COL,
            font=("Consolas", 9),
            width=5,
        )
        self._f_label.pack(side=tk.RIGHT)
        scale = tk.Scale(
            f_frame,
            variable=self._f,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            length=140,
            bg=BG_DARK,
            fg=LABEL_COL,
            troughcolor=SPINE_COL,
            highlightthickness=0,
            showvalue=False,
            command=lambda v: self._f_label.config(text=f"{float(v):.2f}"),
        )
        scale.pack(side=tk.LEFT)
        tk.Label(
            self,
            text="Volume fraction f:",
            bg=BG_DARK,
            fg=LABEL_COL,
            font=("Consolas", 9),
        ).grid(row=3, column=0, sticky="e", **pad)
        f_frame.grid(row=3, column=1, sticky="ew", **pad)

        # Thickness
        self._thick = tk.StringVar(
            value=str(existing.thickness_nm) if existing else "100"
        )
        row(
            "Thickness (nm):",
            lambda: tk.Entry(
                self,
                textvariable=self._thick,
                width=10,
                bg=ENTRY_BG,
                fg=LABEL_COL,
                insertbackground=LABEL_COL,
                relief=tk.FLAT,
                font=("Consolas", 9),
            ),
            4,
        )

        # Model
        from ..eff_medium import MODELS

        self._model = tk.StringVar(
            value=existing.mix_model if existing else "Bruggeman"
        )
        row(
            "Model:",
            lambda: ttk.Combobox(
                self,
                textvariable=self._model,
                values=list(MODELS.keys()),
                width=14,
                font=("Consolas", 9),
            ),
            5,
        )

        # Buttons
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=8)
        tk.Button(
            btn_frame,
            text="Add",
            command=self._ok,
            bg="#1a3a1a",
            fg="#98FB98",
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=10,
        ).pack(side=tk.LEFT, padx=6)
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bg=BTN_BG,
            fg=BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=10,
        ).pack(side=tk.LEFT, padx=6)

        self.grab_set()
        self.wait_window()

    def _ok(self):
        try:
            thick = float(self._thick.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid thickness value.", parent=self)
            return
        self.result = LayerSpec(
            name=self._name.get(),
            material=self._mat_a.get(),
            thickness_nm=thick,
            mix_mat_b=self._mat_b.get(),
            mix_f=self._f.get(),
            mix_model=self._model.get(),
        )
        self.destroy()


class LayerSweepDialog(tk.Toplevel):
    """Configure sweep mode for a single layer (material list or mix fraction)."""

    def __init__(self, parent, spec: LayerSpec, all_materials: list[str]):
        super().__init__(parent)
        self.title("Sweep config")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.applied = False
        self._spec = spec
        self._all_materials = all_materials

        pad = {"padx": 8, "pady": 3}

        # ---- Mode selector ----
        mode_frame = tk.Frame(self, bg=BG_DARK)
        mode_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        tk.Label(mode_frame, text="Mode:", bg=BG_DARK, fg=LABEL_COL,
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self._mode_var = tk.StringVar(value=spec.sweep_mode if spec.sweep_mode else "none")
        for val, txt in (("none", "None"), ("material", "Material"), ("mix", "Mix fraction")):
            tk.Radiobutton(
                mode_frame, text=txt, variable=self._mode_var, value=val,
                bg=BG_DARK, fg=LABEL_COL, selectcolor=AX_BG,
                activebackground=BG_DARK, font=("Consolas", 9),
                command=self._on_mode_change,
            ).pack(side=tk.LEFT, padx=6)

        # ---- Content area (switched by mode) ----
        self._content = tk.Frame(self, bg=BG_DARK)
        self._content.pack(fill=tk.BOTH, expand=True, padx=8)

        self._frame_none = self._build_none_frame()
        self._frame_mat  = self._build_material_frame()
        self._frame_mix  = self._build_mix_frame()

        # ---- Buttons ----
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Apply", command=self._apply,
                  bg="#1a3a1a", fg="#98FB98", relief=tk.FLAT,
                  font=("Consolas", 9), padx=10).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT,
                  font=("Consolas", 9), padx=10).pack(side=tk.LEFT, padx=6)

        self._on_mode_change()
        self.grab_set()
        self.wait_window()

    # ---- Frame builders ----

    def _build_none_frame(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG_DARK)
        tk.Label(f, text="No sweep — single spectrum.", bg=BG_DARK, fg=TICK_COL,
                 font=("Consolas", 9), pady=12).pack()
        return f

    def _build_material_frame(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG_DARK)
        tk.Label(f, text="Materials to sweep:", bg=BG_DARK, fg=LABEL_COL,
                 font=("Consolas", 9)).pack(anchor="w", pady=(4, 2))
        lb_frame = tk.Frame(f, bg=BG_DARK)
        lb_frame.pack(fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        self._mat_lb = tk.Listbox(
            lb_frame, selectmode=tk.EXTENDED, height=8, width=22,
            bg=AX_BG, fg=LABEL_COL, selectbackground=SPINE_COL,
            selectforeground=LABEL_COL, font=("Consolas", 9),
            relief=tk.FLAT, yscrollcommand=sb.set,
        )
        sb.config(command=self._mat_lb.yview)
        self._mat_lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        for m in self._all_materials:
            self._mat_lb.insert(tk.END, m)
        # Pre-select previously chosen materials
        for i, m in enumerate(self._all_materials):
            if m in self._spec.sweep_materials:
                self._mat_lb.selection_set(i)
        sel_frame = tk.Frame(f, bg=BG_DARK)
        sel_frame.pack(anchor="w", pady=2)
        tk.Button(sel_frame, text="Select All",
                  command=lambda: self._mat_lb.select_set(0, tk.END),
                  bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT,
                  font=("Consolas", 8), padx=6).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(sel_frame, text="Clear",
                  command=lambda: self._mat_lb.selection_clear(0, tk.END),
                  bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT,
                  font=("Consolas", 8), padx=6).pack(side=tk.LEFT)
        return f

    def _build_mix_frame(self) -> tk.Frame:
        from ..eff_medium import MODELS
        f = tk.Frame(self._content, bg=BG_DARK)
        pad = {"padx": 4, "pady": 3}

        def row(label_text, widget, r):
            tk.Label(f, text=label_text, bg=BG_DARK, fg=LABEL_COL,
                     font=("Consolas", 9)).grid(row=r, column=0, sticky="e", **pad)
            widget.grid(row=r, column=1, sticky="ew", **pad)

        self._mix_mat_b = tk.StringVar(value=self._spec.sweep_mat_b or
                                        (self._all_materials[1] if len(self._all_materials) > 1 else ""))
        row("Material B (f=0):",
            ttk.Combobox(f, textvariable=self._mix_mat_b,
                         values=self._all_materials, width=16, font=("Consolas", 9)), 0)

        self._mix_model = tk.StringVar(value=self._spec.sweep_mix_model)
        row("Model:",
            ttk.Combobox(f, textvariable=self._mix_model,
                         values=list(MODELS.keys()), width=16, font=("Consolas", 9)), 1)

        self._mix_n_pts = tk.StringVar(value=str(self._spec.sweep_n_pts))
        n_entry = tk.Entry(f, textvariable=self._mix_n_pts, width=6,
                           bg=ENTRY_BG, fg=LABEL_COL, insertbackground=LABEL_COL,
                           relief=tk.FLAT, font=("Consolas", 9))
        row("N points:", n_entry, 2)

        tk.Label(f, text=f"  (Mat A = {self._spec.material}, f=1)",
                 bg=BG_DARK, fg=TICK_COL, font=("Consolas", 8)
                 ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))
        return f

    # ---- Mode switching ----

    def _on_mode_change(self) -> None:
        for fr in (self._frame_none, self._frame_mat, self._frame_mix):
            fr.pack_forget()
        mode = self._mode_var.get()
        {"none": self._frame_none, "material": self._frame_mat,
         "mix": self._frame_mix}[mode].pack(fill=tk.BOTH, expand=True)
        self.update_idletasks()

    # ---- Apply ----

    def _apply(self) -> None:
        mode = self._mode_var.get()
        if mode == "none":
            self._spec.sweep_mode = ""
            self._spec.sweep_materials = []
            self._spec.sweep_mat_b = ""
        elif mode == "material":
            selected = [self._mat_lb.get(i) for i in self._mat_lb.curselection()]
            if len(selected) < 2:
                messagebox.showwarning("Selection", "Select at least 2 materials.", parent=self)
                return
            self._spec.sweep_mode = "material"
            self._spec.sweep_materials = selected
        elif mode == "mix":
            try:
                n_pts = int(self._mix_n_pts.get())
                if n_pts < 2:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "N points must be an integer ≥ 2.", parent=self)
                return
            mat_b = self._mix_mat_b.get().strip()
            if not mat_b:
                messagebox.showerror("Error", "Select Material B.", parent=self)
                return
            self._spec.sweep_mode = "mix"
            self._spec.sweep_mat_b = mat_b
            self._spec.sweep_mix_model = self._mix_model.get()
            self._spec.sweep_n_pts = n_pts
        self.applied = True
        self.destroy()


class StackEditor(tk.Frame):
    """Full stack editor: superstrate, layer list, substrate."""

    def __init__(self, parent, materials: list[str], on_change: Callable, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._materials = materials
        self._on_change = on_change
        self._config = StackConfig()
        self._rows: list[LayerRow] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        def label(parent, text, **kw):
            return tk.Label(
                parent, text=text, bg=BG_DARK, fg=LABEL_COL, font=("Consolas", 9), **kw
            )

        def combo(parent, var, values, width=16):
            cb = ttk.Combobox(
                parent,
                textvariable=var,
                values=values,
                width=width,
                font=("Consolas", 9),
            )
            return cb

        SEMI = ["air", "vacuum", "glass", "sio2", "bk7"]

        # ---- Superstrate ----
        sup_frame = tk.Frame(self, bg=BG_DARK)
        sup_frame.pack(fill=tk.X, pady=(6, 2), padx=6)
        label(sup_frame, "Superstrate:").pack(side=tk.LEFT)
        self._sup_var = tk.StringVar(value=self._config.superstrate)
        self._sup_combo = combo(sup_frame, self._sup_var, SEMI, 10)
        self._sup_combo.pack(side=tk.LEFT, padx=4)
        self._sup_var.trace_add("write", lambda *_: self._sync_boundary())

        # ---- Layer list ----
        label(self, "Layers  (top → bottom):").pack(anchor="w", padx=6, pady=(6, 2))

        self._list_frame = tk.Frame(self, bg=BG_DARK)
        self._list_frame.pack(fill=tk.BOTH, expand=True, padx=6)

        # ---- Buttons ----
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, padx=6, pady=6)
        tk.Button(
            btn_frame,
            text="+ Layer",
            command=self._add_layer,
            bg="#1a2a3a",
            fg="#00BFFF",
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=8,
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            btn_frame,
            text="+ Mixed",
            command=self._add_mixed,
            bg="#1a1a3a",
            fg="#DA70D6",
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=8,
        ).pack(side=tk.LEFT)

        # ---- Substrate ----
        sub_frame = tk.Frame(self, bg=BG_DARK)
        sub_frame.pack(fill=tk.X, pady=(2, 6), padx=6)
        label(sub_frame, "Substrate:").pack(side=tk.LEFT)
        self._sub_var = tk.StringVar(value=self._config.substrate)
        self._sub_combo = combo(sub_frame, self._sub_var, SEMI, 10)
        self._sub_combo.pack(side=tk.LEFT, padx=4)
        self._sub_var.trace_add("write", lambda *_: self._sync_boundary())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync_boundary(self):
        self._config.superstrate = self._sup_var.get()
        self._config.substrate = self._sub_var.get()
        self._on_change()

    def destroy(self):
        for cb in (self._sup_combo, self._sub_combo):
            try:
                cb.configure(textvariable="")
            except Exception:
                pass
        super().destroy()

    def _rebuild_rows(self):
        for r in self._rows:
            r.destroy()
        self._rows = []
        for i, spec in enumerate(self._config.layers):
            row = LayerRow(
                self._list_frame,
                spec,
                i,
                self._materials,
                on_change=self._on_change,
                on_delete=self._delete_layer,
                on_move=self._move_layer,
            )
            row.pack(fill=tk.X, pady=2)
            self._rows.append(row)

    def _add_layer(self):
        n = len(self._config.layers) + 1
        mat = self._materials[0] if self._materials else "air"
        spec = LayerSpec(name=f"Layer {n}", material=mat, thickness_nm=100.0)
        self._config.layers.append(spec)
        self._rebuild_rows()
        self._on_change()

    def _add_mixed(self):
        dlg = MixedLayerDialog(self, self._materials)
        if dlg.result:
            self._config.layers.append(dlg.result)
            self._rebuild_rows()
            self._on_change()

    def _delete_layer(self, index: int):
        if 0 <= index < len(self._config.layers):
            del self._config.layers[index]
            self._rebuild_rows()
            self._on_change()

    def _move_layer(self, index: int, direction: int):
        layers = self._config.layers
        new_idx = index + direction
        if 0 <= new_idx < len(layers):
            layers[index], layers[new_idx] = layers[new_idx], layers[index]
            self._rebuild_rows()
            self._on_change()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_config(self) -> StackConfig:
        return self._config

    def set_config(self, config: StackConfig) -> None:
        self._config = config
        self._sup_var.set(config.superstrate)
        self._sub_var.set(config.substrate)
        self._rebuild_rows()

    def update_materials(self, materials: list[str]) -> None:
        self._materials = materials
        for row in self._rows:
            row.update_materials(materials)
