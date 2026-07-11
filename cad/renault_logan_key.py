#!/usr/bin/env python3
# ============================================================================
# Renault Logan key — parametric CAD model (CadQuery / OpenCASCADE)
# ============================================================================
#
# A clean, printable two-piece (clamshell) key head for a Renault / Dacia
# Logan, built from scratch as a parametric B-rep model. It carries THREE
# payloads:
#
#   1. The mechanical blade, inserted from the FRONT like the OEM key: the flat
#      metal TANG slides into a closed slot in the solid front of the BOTTOM
#      half; the wider SHOULDER butts the front face as the depth stop. Floor +
#      cap + side walls + back stop capture the tang on every axis except
#      pull-out (-X); a BOLT through the tang's factory hole into the solid
#      front locks that. All of this lives in the bottom half, so the blade is
#      held with the top half absent — and the bolt makes it captive. (The same
#      bolt clamps the two halves together at the front.)
#
#   2. The alarm-remote fob (a round PCB ~31.5 x 28 mm, ~7 mm thick, with 3
#      buttons on one face) drops into a rounded CAVITY that fills the middle
#      and rear of the head. Three BUTTON HOLES through the TOP half sit over
#      the fob's buttons so they can be pressed with the lid closed.
#
#   3. The PCF7936 ("ID46") immobilizer transponder sits in a small nest in the
#      solid front, next to the blade.
#
# The head splits along a horizontal parting plane into `bottom` and `top`
# trays, each exported separately as a clean 2-manifold solid that prints
# flat-side-down without supports. The enlarged front of the head is solid, so
# the blade dock / chip nest / keyring / bolt are simply pockets cut into it —
# no separate bosses needed.
#
# ----------------------------------------------------------------------------
# IMPORTANT — measure your own parts before printing.
# Blade/shoulder numbers are estimates for the Renault/Dacia NE73 / VA2 /
# VAC102 family; the PCF7936 nest is sized from the common aftermarket "ID46"
# carrier; the fob cavity + button positions come from the supplied photos
# (31.5 x 28 mm, 3 buttons one side). BUTTON POSITIONS especially must be
# checked against your board. Update the PARAMETERS block; everything reflows.
# ----------------------------------------------------------------------------
#
# Usage:
#   pip install cadquery
#   python3 cad/renault_logan_key.py            # writes STLs into export/
#   python3 cad/renault_logan_key.py --step     # also write STEP files
#
# Coordinate frame: X = 0 at the front face, +X toward the back; Y = 0 on the
# centreline; Z = 0 at the bottom outer face, split_z at the parting plane.
# ============================================================================

from dataclasses import dataclass, field
import os
import sys

import cadquery as cq


# ============================================================================
# PARAMETERS  (edit these — the whole model is derived from them)
# ============================================================================

@dataclass
class KeyParams:
    # --- Head shell envelope (the printed plastic body) -------------------
    # Sized to hold the fob: width = fob_width + 2*fob_clearance + 2*wall;
    # length = solid front zone + fob + back wall; height = wall + fob_body +
    # gap + wall (the fob body is 7 mm; its 3 mm buttons poke out the top).
    head_length: float = 50.0    # front (blade side) -> back
    head_width: float = 34.0
    head_height: float = 12.0    # total assembled thickness
    corner_radius: float = 8.0
    wall: float = 2.2            # outer wall / floor / ceiling thickness

    # --- Mechanical blade — the TANG slides into the head; the wider SHOULDER
    # stays OUTSIDE and butts the front face (NE73/VA2/VAC102 — ESTIMATE) ----
    blade_width: float = 9.0     # width of the tang that enters the head slot
    blade_thickness: float = 2.5 # steel stock thickness
    blade_insert: float = 11.0   # how deep the tang slides into the head
    blade_top_gap: float = 1.2   # plastic cap thickness above the tang slot
    shoulder_length: float = 5.0     # external shoulder, along X (reference)
    shoulder_width: float = 13.0     # must be > blade_width (can't enter slot)
    shoulder_thickness: float = 2.5

    # --- Bolt through the tang's factory hole (pull-out lock + front clamp) --
    use_blade_bolt: bool = True
    bolt_offset: float = 6.0         # bolt/hole centre, from the front face (+X)
    tang_hole_dia: float = 3.2       # the factory hole in the tang (reference)
    blade_pilot_dia: float = 2.0     # bottom: self-tap pilot
    blade_clear_dia: float = 2.7     # top: shank clearance
    blade_head_dia: float = 5.0      # top: counterbore
    blade_head_depth: float = 2.0

    # --- Alarm-remote fob cavity (round PCB, from the photos) -------------
    fob_length: float = 31.5     # long axis (with the tabs) -> along X
    fob_width: float = 28.0      # -> along Y
    fob_body_thickness: float = 7.0   # PCB + battery holder, WITHOUT buttons
    fob_button_height: float = 3.0    # buttons stand this proud of the body
    fob_corner_r: float = 13.0   # the board is nearly round; big radius
    fob_clearance: float = 0.5   # gap around the fob in its cavity
    fob_center_x: float = 31.5   # cavity centre from the front face

    # --- Fob buttons: 3 buttons on ONE face -> holes through the TOP half.
    # Positions are (x, y) in FOB-LOCAL mm (x along fob_length toward the back,
    # y across). MEASURE THESE against your board and adjust. -----------------
    button_hole_dia: float = 5.0
    button_positions: tuple = ((-6.0, 0.0), (7.0, 7.0), (7.0, -7.0))

    # --- Immobilizer transponder PCF7936 ("ID46") carrier, by the blade ----
    chip_length: float = 16.0
    chip_width: float = 7.0
    chip_thickness: float = 3.0
    chip_center_x: float = 10.0
    chip_center_y: float = 9.0   # offset to the side of the blade dock
    chip_across: bool = False    # False -> long axis along X (along the key)

    # --- Keyring (front corner, by the blade — no room behind the fob) -----
    keyring_hole_dia: float = 5.0
    keyring_x: float = 7.0
    keyring_y: float = -11.0

    # --- Assembly screws: 2 at the back corners; the blade bolt clamps the
    # front. Sized for M2.5 self-tapping screws. ----------------------------
    asm_pilot_dia: float = 2.0
    asm_clear_dia: float = 2.7
    asm_head_dia: float = 5.0
    asm_head_depth: float = 2.0
    asm_positions: tuple = ((44.0, 13.0), (44.0, -13.0))

    # --- Parting-line alignment lip --------------------------------------
    lip_width: float = 1.0
    lip_height: float = 1.0

    # --- Fit / print tuning ----------------------------------------------
    clearance: float = 0.30      # gap around blade / chip pockets
    fn: int = 96

    # --- Derived ---------------------------------------------------------
    split_z: float = field(init=False)

    def __post_init__(self):
        self.split_z = self.head_height / 2.0

    @property
    def blade_z0(self):
        """Underside of the tang slot (tang rides high in the bottom half)."""
        return self.split_z - (self.blade_thickness + self.clearance) - self.blade_top_gap


P = KeyParams()
EPS = 0.02


# ============================================================================
# Helpers
# ============================================================================

def rrect_solid(length, width, height, radius):
    """Rounded rectangular prism, centred on X=Y=0, sitting on Z=0."""
    r = min(radius, length / 2 - 0.01, width / 2 - 0.01)
    return (
        cq.Workplane("XY").rect(length, width).extrude(height)
        .edges("|Z").fillet(r)
    )


def rrect_ring(length, width, height, radius, ring_width):
    """Hollow rounded-rectangle ring (picture-frame), centred on X=Y=0."""
    outer = rrect_solid(length, width, height + 2 * EPS, radius).translate((0, 0, -EPS))
    inner = rrect_solid(
        length - 2 * ring_width, width - 2 * ring_width, height + 4 * EPS,
        max(radius - ring_width, 0.4),
    ).translate((0, 0, -2 * EPS))
    return outer.cut(inner)


def cyl(dia, x, y, z0, height):
    """Vertical cylinder (a boss or a cutting peg)."""
    return cq.Workplane("XY").circle(dia / 2).extrude(height).translate((x, y, z0))


def box_at(dx, dy, dz, x, y, z0, cx=True, cy=True):
    return (
        cq.Workplane("XY")
        .box(dx, dy, dz, centered=(cx, cy, False))
        .translate((x, y, z0))
    )


# ============================================================================
# Feature cutters (global coordinates)
# ============================================================================

def fob_cavity(p: KeyParams, z0, height):
    """Rounded pocket that locates the fob, from z0 up by `height`."""
    return rrect_solid(
        p.fob_length + 2 * p.fob_clearance,
        p.fob_width + 2 * p.fob_clearance,
        height, p.fob_corner_r + p.fob_clearance,
    ).translate((p.fob_center_x, 0, z0))


def blade_channel(p: KeyParams):
    """Narrow tang slot cut into the solid front, at the blade height."""
    bw = p.blade_width + p.clearance
    bt = p.blade_thickness + p.clearance
    return box_at(p.wall + p.blade_insert + EPS, bw, bt, -EPS, 0, p.blade_z0, cx=False)


def chip_pocket(p: KeyParams):
    """Rectangular pocket for the PCF7936 carrier, cut into the solid front."""
    if p.chip_across:
        dx, dy = p.chip_width + p.clearance, p.chip_length + p.clearance
    else:
        dx, dy = p.chip_length + p.clearance, p.chip_width + p.clearance
    depth = p.chip_thickness + 0.6
    return box_at(dx, dy, depth + EPS, p.chip_center_x, p.chip_center_y, p.wall)


# ============================================================================
# Alignment lip / groove
# ============================================================================

def lip_ring(p: KeyParams, height, grow=0.0):
    w = p.lip_width + 2 * grow
    outer_len = (p.head_length - p.wall) + w
    outer_wid = (p.head_width - p.wall) + w
    rad = max(p.corner_radius - (p.wall - w) / 2, 0.6)
    return rrect_ring(outer_len, outer_wid, height, rad, w)


# ============================================================================
# Shell halves
# ============================================================================

def bottom_shell(p: KeyParams):
    cx = p.head_length / 2
    b = rrect_solid(p.head_length, p.head_width, p.split_z, p.corner_radius).translate((cx, 0, 0))

    # hollow the fob region only (front stays solid for blade/chip/keyring/bolt)
    b = b.cut(fob_cavity(p, p.wall, p.split_z))          # open at the parting face

    # alignment lip on the parting rim
    skirt = 0.6
    b = b.union(lip_ring(p, p.lip_height + skirt).translate((cx, 0, p.split_z - skirt)))
    # trim any lip that oversteps the fob opening or the outer edge
    b = b.intersect(
        rrect_solid(p.head_length, p.head_width, p.split_z + p.lip_height + 1, p.corner_radius)
        .translate((cx, 0, 0))
    )

    # --- pockets / holes in the solid front ---
    b = b.cut(blade_channel(p))
    b = b.cut(chip_pocket(p))
    b = b.cut(cyl(p.keyring_hole_dia, p.keyring_x, p.keyring_y, -EPS, p.split_z + 2 * EPS))

    # self-tap pilots, blind from the parting face (closed outer floor)
    floor_keep = 1.0
    for (x, y) in p.asm_positions:
        b = b.cut(cyl(p.asm_pilot_dia, x, y, floor_keep, p.split_z - floor_keep + EPS))
    if p.use_blade_bolt:
        b = b.cut(cyl(p.blade_pilot_dia, p.bolt_offset, 0, floor_keep, p.split_z - floor_keep + EPS))
    return b


def top_shell(p: KeyParams):
    cx = p.head_length / 2
    h = p.head_height - p.split_z
    t = rrect_solid(p.head_length, p.head_width, h, p.corner_radius).translate((cx, 0, 0))

    # fob region hollow, leaving a `wall` ceiling (open at the parting face z=0)
    t = t.cut(fob_cavity(p, -EPS, h - p.wall + EPS))

    # groove matching the bottom lip
    groove = lip_ring(p, p.lip_height + p.clearance, grow=p.clearance).translate((cx, 0, 0))
    t = t.cut(groove)

    # keyring hole
    t = t.cut(cyl(p.keyring_hole_dia, p.keyring_x, p.keyring_y, -EPS, h + 2 * EPS))

    # button holes through the ceiling, over each fob button
    for (bx, by) in p.button_positions:
        t = t.cut(cyl(p.button_hole_dia, p.fob_center_x + bx, by, -EPS, h + 2 * EPS))

    # assembly screws: clearance + counterbore from the top outer face
    for (x, y) in p.asm_positions:
        t = t.cut(cyl(p.asm_clear_dia, x, y, -EPS, h + 2 * EPS))
        t = t.cut(cyl(p.asm_head_dia, x, y, h - p.asm_head_depth, p.asm_head_depth + EPS))

    # blade bolt: clearance + counterbore (also clamps the front)
    if p.use_blade_bolt:
        t = t.cut(cyl(p.blade_clear_dia, p.bolt_offset, 0, -EPS, h + 2 * EPS))
        t = t.cut(cyl(p.blade_head_dia, p.bolt_offset, 0, h - p.blade_head_depth, p.blade_head_depth + EPS))
    return t


# ============================================================================
# Reference geometry (fit-check only — never exported for printing)
# ============================================================================

def blade_reference(p: KeyParams):
    z0 = p.blade_z0
    tang = box_at(p.wall + p.blade_insert, p.blade_width, p.blade_thickness, 0, 0, z0, cx=False)
    shoulder = box_at(p.shoulder_length, p.shoulder_width, p.shoulder_thickness,
                      -p.shoulder_length, 0, z0, cx=False)
    blade = box_at(20, p.blade_width, p.blade_thickness, -p.shoulder_length - 20, 0, z0, cx=False)
    hole = cyl(p.tang_hole_dia, p.bolt_offset, 0, z0 - 1, p.blade_thickness + 2)
    return tang.union(shoulder).union(blade).cut(hole)


def chip_reference(p: KeyParams):
    if p.chip_across:
        dx, dy = p.chip_width, p.chip_length
    else:
        dx, dy = p.chip_length, p.chip_width
    return box_at(dx, dy, p.chip_thickness, p.chip_center_x, p.chip_center_y, p.wall)


def fob_reference(p: KeyParams):
    """Round fob body + 3 button bumps, resting on the cavity floor."""
    body = rrect_solid(p.fob_length, p.fob_width, p.fob_body_thickness, p.fob_corner_r)\
        .translate((p.fob_center_x, 0, p.wall))
    fob = body
    for (bx, by) in p.button_positions:
        btn = cyl(p.button_hole_dia - 1.2, p.fob_center_x + bx, by,
                  p.wall + p.fob_body_thickness, p.fob_button_height)
        fob = fob.union(btn)
    return fob


# ============================================================================
# Export
# ============================================================================

def print_ready_top(p: KeyParams):
    """Top half flipped flat-side-down for printing (open face up)."""
    h = p.head_height - p.split_z
    return top_shell(p).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, h))


def assembled(p: KeyParams):
    return bottom_shell(p).union(top_shell(p).translate((0, 0, p.split_z)))


def main():
    p = P
    outdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "export"))
    os.makedirs(outdir, exist_ok=True)
    do_step = "--step" in sys.argv
    parts = {
        "bottom_shell": bottom_shell(p),
        "top_shell": print_ready_top(p),
        "key_assembled": assembled(p),
    }
    for name, solid in parts.items():
        cq.exporters.export(solid, os.path.join(outdir, name + ".stl"),
                            tolerance=0.05, angularTolerance=0.3)
        print("wrote", name + ".stl")
        if do_step:
            cq.exporters.export(solid, os.path.join(outdir, name + ".step"))
            print("wrote", name + ".step")
    print("done.")


if __name__ == "__main__":
    main()
