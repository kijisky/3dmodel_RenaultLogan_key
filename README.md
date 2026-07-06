# Renault Logan key — parametric shell (Phase 1)

Parametric OpenSCAD model for a custom, 3D-printable key head that:

- accepts the original mechanical **key blade** (with its factory shoulder),
  transplanted from the OEM head, inserted and **bolted through** exactly
  like an original VAC-style key, and
- accepts the **PCF7936 ("ID46") immobilizer transponder** chip in a
  dedicated floor nest.

Phase 2 (not implemented yet) will add an internal cavity sized for a
**Pharaon V16i** alarm remote ("teardrop" style fob) inside the same shell.

## Status: Phase 1 only

This phase delivers the blade + immobilizer shell. The general hollow
interior is intentionally generous so Phase 2 can add the alarm-remote
cavity later without reworking the outer shell.

## Files

```
cad/renault_logan_key.scad   parametric OpenSCAD source (this is the model)
export/top_shell.stl         phase-1 STL export, top half (print-ready orientation)
export/bottom_shell.stl      phase-1 STL export, bottom half (print-ready orientation)
docs/renders/*.png           preview renders (see below)
```

| ![assembly](docs/renders/assembly_closed.png) | ![exploded](docs/renders/assembly_open.png) |
|---|---|
| ![top shell](docs/renders/top_shell.png) | ![bottom shell](docs/renders/bottom_shell.png) |

The exploded view (top right) and the two shell close-ups show the
**rectangular chip nest** molded into the bottom half's floor — that's
where the PCF7936 goes.

## Design overview

- The head is split into a **top and bottom shell**, joined along a
  horizontal parting plane at mid-thickness with 4 self-tapping screws
  through printed bosses, plus an alignment lip around the rim.
- Building each half independently (rather than boolean-cutting a shared
  solid) keeps the STL geometry a clean 2-manifold — no repair needed.
- **Blade retention (VAC-style):** the blade inserts fully into a slot in
  the front face. The slot has two sections: a narrow channel sized to the
  blade, and — just behind it — a wider pocket sized to the factory
  **shoulder**, which is wider than the blade and forms a mechanical
  retention step (the blade can't be pulled back out once seated). The
  blade is then **bolted in place** through its factory shoulder hole with
  a screw that threads into a boss in the bottom half and is captured by a
  clearance hole + counterbore in the top half — the same construction as
  an original VAC-family key, not just a friction fit.
- **Immobilizer:** the PCF7936 chip is a flat rectangular "stick" module
  (NXP package SOT385-1, ~12 x 5 x 2mm — not a glass capsule), so it sits
  in a **low-walled rectangular nest molded into the bottom half's floor**.
  Drop the chip into the nest before closing the lid; the top half simply
  closes over it.
- A keyring hole (with a reinforced boss) sits near the back of the head.
- **Print orientation:** both halves are meant to be printed **flat-side
  down** (closed outer face on the bed, open/parting face up) — each half
  is then a simple open tray, no supports needed. `render_mode="top"`
  automatically reorients the top shell for this (its natural position in
  the assembly is flat-side *up*, since it's the lid).

## IMPORTANT — measure your own key before printing

The repo does not have a verified physical Logan blank to measure, so the
blade/shoulder dimensions in the "MEASURE YOUR OWN PART" section at the
top of `renault_logan_key.scad` are **estimates** for the Renault/Dacia
**NE73 / VA2 / VAC102** blade family, cross-referenced from locksmith blank
catalogs — not confirmed against a real Logan key. The PCF7936 nest is
sized from the NXP SOT385-1 datasheet outline, but clone/aftermarket chips
vary. Use calipers on your actual blade, shoulder, and chip, and update:

```openscad
blade_length, blade_width, blade_thickness
shoulder_length, shoulder_width, shoulder_thickness
blade_screw_offset                              // must line up with the real hole in your blade's shoulder
immobilizer_length, immobilizer_width, immobilizer_thickness
```

Everything else (shell envelope, wall thickness, screw bosses, keyring,
alignment lip) is derived from these and from the independent "Head shell
envelope" parameters further down, so changing the measurements above
reflows through the whole model automatically.

## Rendering / exporting

Requires [OpenSCAD](https://openscad.org/) (developed against 2021.01).

```bash
# open the interactive viewer (shows the closed assembly + reference blade/chip)
openscad cad/renault_logan_key.scad

# export STLs for printing (print-ready orientation, flat side down)
openscad -o export/top_shell.stl    -D 'render_mode="top"'    cad/renault_logan_key.scad
openscad -o export/bottom_shell.stl -D 'render_mode="bottom"' cad/renault_logan_key.scad
```

`render_mode` (top-of-file variable, overridable with `-D`) selects what
gets rendered:

- `"assembly"` — both shells assembled + reference blade/chip (visual check only)
- `"assembly_open"` — same, pulled apart along Z
- `"top"` — top shell, print-ready orientation (flat side down)
- `"bottom"` — bottom shell, print-ready orientation (flat side down)
- `"blade_reference"` — just the reference blade/shoulder solid

The silver/gray blade and dark chip shown in the assembly views are
**reference geometry only** (for checking fit) — they are not part of
either STL export.

## Printing notes

- Print both halves flat-side down as exported — each half is a simple
  open tray, no supports needed.
- Assembly hardware: 5x self-tapping screws total (4 corner + 1 through the
  blade shoulder) sized for a ~2.0mm pilot hole in the bottom half and a
  ~2.6mm clearance hole + counterbore in the top half (M2.5 self-tap
  assumed by default — adjust `screw_*` parameters for your hardware).
- Fit-check the blade and chip in the printed bottom half before
  screwing anything permanently; adjust `fit_clearance` if too tight or
  too loose. Make sure `blade_screw_offset` actually lines up with the
  hole in your blade before drilling in the screw.

## Next step (Phase 2)

Add a cavity sized for the Pharaon V16i alarm remote inside the existing
hollow interior, without changing the outer shell envelope.
