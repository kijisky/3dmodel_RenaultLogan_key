# Renault Logan key — parametric CAD model

A clean, printable **two-piece (clamshell) key head** for a Renault / Dacia
Logan, built **from scratch** as a parametric B-rep model in
[CadQuery](https://cadquery.readthedocs.io/) (OpenCASCADE kernel). Editing the
parameters at the top of the script reflows the whole part and re-exports
print-ready STLs.

| ![assembled](docs/renders/assembly_closed.png) | ![exploded](docs/renders/assembly_open.png) |
|---|---|
| ![fit check](docs/renders/fit_check.png) | ![fob + buttons](docs/renders/fob_buttons.png) |

> The gray blade, dark chip and green fob in the *fit-check* views are
> **reference geometry only** — they are not part of any printed STL.

Head envelope ≈ **58 × 34 × 12 mm** (auto-sized around the fob, with extra rear
body for the keyring hole). The parting plane is NOT at the mid-height: the
**bottom is thicker, the top (lid) thinner** (`split_ratio`, default 65/35), so
most of the fob and all of the blade/chip retention features sit in the
sturdier half.

## What it holds

1. **Alarm-remote fob** — a round PCB **31.5 × 28 mm, ~7 mm thick, 3 buttons on
   one face** — drops into a rounded **cavity** that fills the middle and rear
   of the head. **Retainer ribs** on the cavity walls grip its edge so it can't
   rattle or spin. Three **rectangular button openings** through the **top** half
   sit over the buttons — each opening is **rotated** (radial from the fob
   centre by default, matching the angled button layout seen on the board) so
   the caps drop in squarely; they're pressed with the lid closed. Insert the
   fob with the shell open, then close the lid.

2. **Blade inserts from the front, like the OEM key, and holds without the
   second half.** The flat metal **tang** slides into a slot in the solid front
   of the **bottom** half; the wider **shoulder** butts the front face as the
   depth stop. Floor + a thin **cap** + side walls capture the tang, and a
   **bolt** through the tang's factory hole locks pull-out (and clamps the two
   halves at the front). The slot runs **through into the fob cavity** (10 mm
   wide), so it is a passage — print supports push straight out into the
   interior instead of being trapped in a blind pocket.

3. **Immobilizer** — the **PCF7936 / "ID46"** transponder sits in a small nest
   in the solid front, right next to the blade, molded **entirely into the
   bottom half**. The nest is full width down low, then **narrows into an
   overhanging snap lip** just below the parting plane: press the chip down
   past the lip (the thin wall flexes briefly) and it springs back over the
   chip — so the chip is **captive in the bottom half alone**, even with the
   top half off. A hold-down pad on the lid adds a second retention layer once
   the key is closed.

4. **Keyring hole** — a plain hole through the extra solid body behind the fob
   (the body is simply longer; no protruding loop). Two back-corner assembly
   screws and an alignment lip/groove close the clamshell.

Because the enlarged front of the head is solid, the blade dock / chip nest /
keyring / bolt are just pockets cut into it — no separate printed bosses.

## Files

```
cad/renault_logan_key.py             the parametric model (edit this — CadQuery)
cad/renault_logan_key_freecad.FCMacro same model, ported to FreeCAD's own Part API
cad/render_previews.py               regenerates docs/renders/*.png from the STLs
export/bottom_shell.stl              print-ready, flat-side down          (+ .step)
export/top_shell.stl                 print-ready, flat-side down          (+ .step)
export/key_assembled.stl             both halves fused (visual check)     (+ .step)
docs/renders/*.png                   preview images
requirements.txt                     cadquery + render deps
```

Both shell STLs are clean, watertight 2-manifold solids (verified: 0 boundary
edges, 0 non-manifold junctions) and print **flat-side down with no supports**.

## How the blade is held (cross-sections)

```
 side view (Y=0)                       top view (blade height)
 +--------- cap -----------+           front face
 |####  +- tang slot ------|--> into    |  +- 10 mm slot ---------|--> fob
 |####  |   BLADE ---->    | fob cavity  |  |  (through)          | cavity
 |#### bolt  +------------ |             |  +--------------------- |
 |####  # solid / thread # |  shoulder --+<-- butts the front face (depth stop)
 +-- floor ----------------+           bolt hole (o)  through the tang
```

Front insertion: the tang slides in until the **shoulder hits the front
face**. The **bolt** drops through the tang's hole into the solid front and
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

## Opening in FreeCAD

Two options:

- **Just want the geometry in FreeCAD?** Import `export/*.step` (File → Import)
  — exact geometry, one click, but as a static shape (no parametric tree).
- **Want a native, editable `.FCStd`?** Run the macro:
  ```bash
  freecadcmd cad/renault_logan_key_freecad.FCMacro      # headless, no GUI needed
  # or: FreeCAD -> Macro -> Macros... -> Execute -> browse to the file
  ```
  It rebuilds the exact same model using FreeCAD's own `Part` scripting API
  (same `KeyParams`, same steps) and saves `export/renault_logan_key.FCStd`
  with `bottom_shell`, `top_shell`, `key_assembled` plus the reference
  blade/chip/fob objects.

  This port could not be run inside a real FreeCAD install in the environment
  that wrote it (none available there). It **was** cross-checked by executing
  the identical Part-API call sequence directly against the OpenCASCADE
  kernel (the same one FreeCAD's `Part` module wraps) and comparing the
  result to the verified CadQuery model: bounding boxes and **exact BREP
  volumes matched to 0.1 mm³**, and the resulting meshes were watertight
  (0 boundary edges, 0 non-manifold junctions). The one thing that couldn't be
  checked from outside FreeCAD is the exact `Part`/`FreeCAD` module call
  surface itself (`Part.makeBox`, `doc.addObject`, `doc.saveAs`, etc.) — these
  use long-stable, well-documented FreeCAD APIs, but if you hit an error on a
  specific line when you first run it, that's the one class of issue to
  expect; the geometry/parameters behind it are already proven correct.

## IMPORTANT — measure your own blank before printing

There is no verified physical Logan blank behind these numbers, so the
blade/shoulder dimensions are **estimates** for the Renault/Dacia
**NE73 / VA2 / VAC102** blade family and the PCF7936 nest is sized from the
common aftermarket "ID46" carrier. Clones vary. Put calipers on your actual
parts and update the `KeyParams` block at the top of
`cad/renault_logan_key.py`:

```python
fob_length, fob_width, fob_body_thickness    # your alarm fob PCB (31.5 x 28 x 7)
fob_button_height                            # how far the buttons stand proud
button_positions                             # (x, y) of each button in FOB-LOCAL mm
button_slot_l, button_slot_w                 # rectangular opening size  << CHECK THESE
button_radial, button_angles                 # opening rotation — see below
blade_width, blade_thickness, blade_insert   # the tang that enters the head
shoulder_width, shoulder_length              # the external stop (width > blade_width)
bolt_offset                                  # must line up with the hole in YOUR tang
chip_length, chip_width, chip_thickness      # your PCF7936 carrier
chip_snap_lip_height, chip_snap_overlap      # how strong the chip's snap retention is
split_ratio                                  # bottom/top thickness split (0.5 = even)
clearance                                    # loosen/tighten every pocket at once
```

`button_positions` came from the supplied photos and **must be verified** against
your board — they set where the top-half holes land. Each opening is rotated by
`button_radial` (default: auto — points radially away from the fob centre,
matching the angled layout in the photos); set `button_radial = False` and fill
in `button_angles` (degrees per button) if you need exact angles instead. The
head envelope (`head_length/width/height`) is chosen to wrap the fob; if you
change the fob size, bump these to keep ~2 mm of wall around it.

**Chip snap-fit tuning:** `chip_snap_overlap` (default 0.4 mm per side) is the
interference the chip must be pressed past — increase it for a firmer retention
if the chip falls out too easily, decrease it (or shrink `chip_snap_lip_height`)
if it's too hard to press in or the thin lip wall cracks when printed in your
material.

## Printing notes

- Print both halves **flat-side down** as exported — each is a simple open
  tray, no supports.
- Hardware: 2 back-corner self-tapping screws + 1 blade bolt at the front
  (which also clamps the halves). Defaults sized for **M2.5 self-tap**:
  ~2.0 mm pilot in the bottom, 2.7 mm clearance + counterbore in the top —
  change the `asm_*` / `blade_*` parameters for your screws.
- Drop the **fob** into its cavity and **press the chip down past its snap lip**
  into its nest in the printed **bottom** half (it should click in and stay put
  even before the lid goes on), check the blade tang slides in and the buttons
  line up under the top-half holes, then close the lid. Adjust `clearance` /
  `fob_clearance` if anything is too tight or too loose, `chip_snap_overlap` if
  the chip is too hard/easy to seat, and confirm `bolt_offset` lines up with the
  hole in your tang.
