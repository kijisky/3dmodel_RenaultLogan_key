# Renault Logan key — parametric CAD model

A clean, printable **two-piece (clamshell) key head** for a Renault / Dacia
Logan, built **from scratch** as a parametric B-rep model in
[CadQuery](https://cadquery.readthedocs.io/) (OpenCASCADE kernel). Editing the
parameters at the top of the script reflows the whole part and re-exports
print-ready STLs.

| ![assembled](docs/renders/assembly_closed.png) | ![exploded](docs/renders/assembly_open.png) |
|---|---|
| ![fit check](docs/renders/fit_check.png) | ![bottom](docs/renders/bottom_shell.png) |

> The gray blade and dark chip in the *fit-check* view are **reference geometry
> only** — they are not part of any printed STL.

## What it does

1. **Blade inserts from the front, like the OEM key, and holds without the
   second half.** The flat metal **tang** slides into a closed slot in a solid
   *dock* in the **bottom** half; the wider **shoulder** butts the front face as
   the depth stop. Floor + a thin **cap** + side walls + a **back stop** capture
   the tang on every axis except pull-out; a **bolt** through the tang's factory
   hole into a boss in the bottom half locks that last axis. Because all of this
   lives in the bottom half, the blade is retained even with the top half
   removed — and the bolt makes it captive.

2. **Dedicated immobilizer cavity.** A rectangular **nest** (retaining ribs
   molded into the bottom floor) holds a **PCF7936 / "ID46"** transponder
   carrier. It sits crosswise between the blade tip and the keyring boss, and
   the closed lid keeps it from rattling.

3. Keyring boss + hole at the back, four corner assembly screws with printed
   bosses, and an alignment lip/groove around the parting line.

## Files

```
cad/renault_logan_key.py     the parametric model (edit this)
cad/render_previews.py       regenerates docs/renders/*.png from the STLs
export/bottom_shell.stl      print-ready, flat-side down          (+ .step)
export/top_shell.stl         print-ready, flat-side down          (+ .step)
export/key_assembled.stl     both halves fused (visual check)     (+ .step)
docs/renders/*.png           preview images
requirements.txt             cadquery + render deps
```

Both shell STLs are clean, watertight 2-manifold solids (verified: 0 boundary
edges, 0 non-manifold junctions) and print **flat-side down with no supports**.

## How the blade is held (cross-sections)

```
 side view (Y=0)                     top view (blade height)
 +--------- cap ----------+          front face
 |####  +- tang slot -+ ##|           |  +-- narrow tang slot --+  back
 |####  |   BLADE ----+--)|  shoulder -+<-|  (= tang width)      |# stop
 |#### bolt  +--------+ ##|  (outside) |  +----------------------+
 |####  # boss/thread # ##|           bolt hole (o)  through the tang
 +-- floor ---------------+
```

Front insertion: the tang slides in until the **shoulder hits the front
face**. The **bolt** drops through the tang's hole into the bottom boss and
locks it against pulling back out.

## Build / export

```bash
pip install -r requirements.txt

# export the three STLs into export/
python3 cad/renault_logan_key.py

# also write STEP files (for editing in other CAD)
python3 cad/renault_logan_key.py --step

# regenerate the preview PNGs
python3 cad/render_previews.py
```

## IMPORTANT — measure your own blank before printing

There is no verified physical Logan blank behind these numbers, so the
blade/shoulder dimensions are **estimates** for the Renault/Dacia
**NE73 / VA2 / VAC102** blade family and the PCF7936 nest is sized from the
common aftermarket "ID46" carrier. Clones vary. Put calipers on your actual
parts and update the `KeyParams` block at the top of
`cad/renault_logan_key.py`:

```python
blade_width, blade_thickness, blade_insert   # the tang that enters the head
shoulder_width, shoulder_length              # the external stop (width > blade_width)
bolt_offset                                  # must line up with the hole in YOUR tang
chip_length, chip_width, chip_thickness      # your PCF7936 carrier
clearance                                    # loosen/tighten every pocket at once
```

Everything else (shell envelope, walls, bosses, keyring, lip) derives from
these plus the head-envelope parameters, so a change reflows through the whole
model automatically.

## Printing notes

- Print both halves **flat-side down** as exported — each is a simple open
  tray, no supports.
- Hardware: 4 corner self-tapping screws + 1 blade bolt (defaults sized for
  **M2.5 self-tap**: ~2.0 mm pilot in the bottom, 2.7 mm clearance + counterbore
  in the top — change the `asm_*` / `blade_*` parameters for your screws).
- Fit-check the blade tang and the chip in the printed **bottom** half before
  closing the lid; adjust `clearance` if too tight or too loose, and confirm
  `bolt_offset` lines up with the hole in your tang.
