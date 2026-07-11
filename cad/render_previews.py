#!/usr/bin/env python3
"""Render matplotlib preview PNGs of the exported STLs into docs/renders/.
Not part of the model — just documentation images."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh

HERE = os.path.dirname(__file__)
EXPORT = os.path.abspath(os.path.join(HERE, "..", "export"))
RENDERS = os.path.abspath(os.path.join(HERE, "..", "docs", "renders"))
os.makedirs(RENDERS, exist_ok=True)


def add_mesh(ax, path, color, alpha=1.0, zshift=0.0, facecolor=None):
    m = mesh.Mesh.from_file(path)
    tris = m.vectors.copy()
    tris[:, :, 2] += zshift
    pc = Poly3DCollection(tris, alpha=alpha)
    pc.set_facecolor(facecolor or color)
    pc.set_edgecolor((0, 0, 0, 0.12))
    pc.set_linewidth(0.15)
    ax.add_collection3d(pc)
    return m


def frame(ax, meshes, elev=28, azim=-60):
    allv = np.vstack([m.vectors.reshape(-1, 3) for m in meshes])
    mn = allv.min(axis=0)
    mx = allv.max(axis=0)
    c = (mn + mx) / 2
    r = (mx - mn).max() / 2 * 1.05
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def one(path_color_list, out, elev=28, azim=-60, title=None):
    fig = plt.figure(figsize=(6, 4.2), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    ms = []
    for path, color, alpha, zsh in path_color_list:
        ms.append(add_mesh(ax, path, color, alpha, zsh))
    frame(ax, ms, elev, azim)
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(RENDERS, out), transparent=False)
    plt.close(fig)
    print("wrote", out)


RED = "#d42a2a"
GRY = "#b8bcc2"

one([(f"{EXPORT}/key_assembled.stl", RED, 1.0, 0.0)],
    "assembly_closed.png", title="Assembled key head")

one([(f"{EXPORT}/bottom_shell.stl", RED, 1.0, 0.0)],
    "bottom_shell.png", elev=42, azim=-72,
    title="Bottom half — blade channel, bolt boss, chip nest")

one([(f"{EXPORT}/top_shell.stl", GRY, 1.0, 0.0)],
    "top_shell.png", elev=42, azim=-72, title="Top half (lid)")

# exploded: bottom in place, top lifted — the top must be in ASSEMBLED
# orientation (not the mirrored print-ready one), so export a temp STL.
import sys
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402
import renault_logan_key as kly  # noqa: E402

tmp_top = os.path.join(EXPORT, "_tmp_top_assembled.stl")
top_asm = kly.top_shell(kly.P).translate((0, 0, kly.P.split_z))
cq.exporters.export(top_asm, tmp_top, tolerance=0.05, angularTolerance=0.3)

one([(f"{EXPORT}/bottom_shell.stl", RED, 1.0, 0.0),
     (tmp_top, GRY, 0.85, 16.0)],
    "assembly_open.png", elev=24, azim=-62, title="Exploded view")
os.remove(tmp_top)

# fit-check: bottom shell + reference blade + fob + chip in place
tmp_blade = os.path.join(EXPORT, "_tmp_blade.stl")
tmp_chip = os.path.join(EXPORT, "_tmp_chip.stl")
tmp_fob = os.path.join(EXPORT, "_tmp_fob.stl")
cq.exporters.export(kly.blade_reference(kly.P), tmp_blade, tolerance=0.05, angularTolerance=0.3)
cq.exporters.export(kly.chip_reference(kly.P), tmp_chip, tolerance=0.05, angularTolerance=0.3)
cq.exporters.export(kly.fob_reference(kly.P), tmp_fob, tolerance=0.05, angularTolerance=0.3)
one([(f"{EXPORT}/bottom_shell.stl", RED, 0.45, 0.0),
     (tmp_blade, "#8a8f98", 1.0, 0.0),
     (tmp_chip, "#2b2f36", 1.0, 0.0),
     (tmp_fob, "#1f6f3a", 0.9, 0.0)],
    "fit_check.png", elev=32, azim=-60,
    title="Fit check — blade + PCF7936 + alarm fob (green) with buttons")

# top-down: button holes over the fob buttons
one([(f"{EXPORT}/bottom_shell.stl", RED, 0.30, 0.0),
     (tmp_fob, "#1f6f3a", 1.0, 0.0)],
    "fob_buttons.png", elev=88, azim=-90,
    title="Fob seated — 3 buttons line up under the top-half holes")
for f in (tmp_blade, tmp_chip, tmp_fob):
    os.remove(f)

print("done.")
