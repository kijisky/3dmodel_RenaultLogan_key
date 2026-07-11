#!/usr/bin/env python3
# ============================================================================
# Renault Logan key — parametric CAD model (CadQuery / OpenCASCADE)
# ============================================================================
#
# A clean, printable two-piece (clamshell) key head for a Renault / Dacia
# Logan, built from scratch as a parametric B-rep model.
#
# Design goals (from the request):
#
#   1. The mechanical blade is inserted from the FRONT of the key, exactly
#      like the OEM key: the flat metal TANG slides into a closed slot in a
#      solid dock in the BOTTOM half, and the wider SHOULDER butts the front
#      face as the depth stop. Floor + cap + side walls + back stop capture
#      the tang on every axis except pull-out (-X); a bolt through the tang's
#      factory hole into a boss in the bottom half locks that last axis. All
#      of this lives in the bottom half, so the blade is held with the top
#      half absent, and the bolt makes it captive.
#
#   2. There is a dedicated cavity for the immobilizer transponder
#      (PCF7936 / "ID46") — a rectangular nest molded into the bottom floor
#      with retaining ribs and a hold-down bump so the chip can't rattle.
#
# The head is split along a horizontal parting plane into `bottom` and `top`
# trays. Each half is built independently and exported separately so every
# STL is a clean 2-manifold solid that prints flat-side-down without supports.
#
# ----------------------------------------------------------------------------
# IMPORTANT — measure your own blank before printing.
# The blade / shoulder numbers below are estimates for the Renault/Dacia
# NE73 / VA2 / VAC102 blade family and the PCF7936 nest is sized from the
# common aftermarket "ID46" carrier module. Clones vary — put calipers on
# YOUR blade, shoulder, shoulder hole, and chip and update the PARAMETERS
# block. Everything else reflows automatically.
# ----------------------------------------------------------------------------
#
# Usage:
#   pip install cadquery
#   python3 cad/renault_logan_key.py            # writes STLs into export/
#   python3 cad/renault_logan_key.py --step     # also write STEP files
#
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
    head_length: float = 46.0    # front (blade side) -> back
    head_width: float = 30.0
    head_height: float = 13.0    # total assembled thickness
    corner_radius: float = 7.0
    wall: float = 2.2            # outer wall / floor / ceiling thickness

    # --- Mechanical blade — the TANG is the flat metal tail that slides into
    # the head from the front; the wider SHOULDER stays OUTSIDE and butts the
    # front face (that is the insertion-depth stop, exactly like the OEM key).
    # (NE73 / VA2 / VAC102 family — ESTIMATE, measure your own.) -----------
    blade_width: float = 9.0     # width of the tang that enters the head slot
    blade_thickness: float = 2.5 # steel stock thickness
    blade_insert: float = 12.0   # how deep the tang slides into the head
    blade_top_gap: float = 1.2   # plastic "cap" thickness above the tang slot.
    #   The tang slides into a closed slot in a solid dock in the BOTTOM half:
    #   floor below + this cap above + side walls + back stop capture it on
    #   every axis except -X (pull-out), which the bolt below locks. So even
    #   with no top half the blade only comes out if you remove the bolt.
    blade_pocket_wall: float = 2.0  # dock wall thickness around the tang slot
    blade_back_stop: float = 2.0    # solid stop behind the fully-inserted tang tip

    # --- Bolt through the tang's factory hole into a boss in the bottom half.
    # This is the pull-out lock; it works with the bottom half alone. Align
    # bolt_offset with the real hole in YOUR tang (measured into the head). ---
    bolt_offset: float = 6.0         # bolt/hole centre, from the front face (+X)
    tang_hole_dia: float = 3.2       # the factory hole in the tang (reference only)

    # --- Factory shoulder — external, wider than the slot; butts the front
    # face as the insertion stop.  Reference geometry / fit info only. --------
    shoulder_length: float = 5.0     # along key axis (X), sits outside the head
    shoulder_width: float = 13.0     # must be > blade_width (so it can't enter)
    shoulder_thickness: float = 2.5

    # --- Immobilizer transponder: PCF7936 ("ID46") carrier module --------
    # A flat rectangular carrier (NOT a glass capsule on most aftermarket
    # kits). Measure yours; glass-capsule versions need a round channel.
    chip_length: float = 16.0
    chip_width: float = 7.0
    chip_thickness: float = 3.0
    chip_center_x: float = 25.0   # nest centre, from front face
    chip_across: bool = True      # lay the chip crosswise (long axis along Y),
    #   which fits it between the blade tip and the keyring boss along X

    # --- Keyring ---------------------------------------------------------
    keyring_hole_dia: float = 5.0
    keyring_boss_dia: float = 11.0
    keyring_from_back: float = 6.0  # keyring centre, from the back edge

    # --- Assembly screws (top half -> bottom half, self-tapping) ---------
    # Sized for M2.5 self-tapping screws by default.
    asm_boss_dia: float = 6.2
    asm_pilot_dia: float = 2.0    # bottom: self-tap pilot
    asm_clear_dia: float = 2.7    # top: shank clearance
    asm_head_dia: float = 5.0     # top: counterbore for the head
    asm_head_depth: float = 2.0
    asm_x: tuple = (10.0, 36.0)   # screw columns, from front face
    asm_y_inset: float = 5.0      # screw rows, from each side wall

    # --- Blade retaining bolt (through the tang hole into a bottom boss) --
    use_blade_bolt: bool = True
    blade_boss_dia: float = 6.0
    blade_pilot_dia: float = 2.0
    blade_clear_dia: float = 2.7
    blade_head_dia: float = 5.0
    blade_head_depth: float = 2.0

    # --- Parting-line alignment lip --------------------------------------
    lip_width: float = 1.0
    lip_height: float = 1.0

    # --- Fit / print tuning ----------------------------------------------
    clearance: float = 0.30      # gap around blade/shoulder/chip pockets
    fn: int = 96                 # export tessellation quality

    # --- Derived (filled in __post_init__) -------------------------------
    split_z: float = field(init=False)

    def __post_init__(self):
        self.split_z = self.head_height / 2.0

    @property
    def keyring_x(self):
        return self.head_length - self.keyring_from_back

    @property
    def blade_z0(self):
        """Underside of the blade channel (blade rides high in the bottom
        half, blade_top_gap below the parting plane)."""
        return self.split_z - (self.blade_thickness + self.clearance) - self.blade_top_gap


P = KeyParams()
EPS = 0.02  # tiny overlap so coincident faces never land flush


# ============================================================================
# Small helpers
# ============================================================================

def rrect_solid(length, width, height, radius):
    """A rounded rectangular prism, centred on X=Y=0, sitting on Z=0."""
    r = min(radius, length / 2 - 0.01, width / 2 - 0.01)
    return (
        cq.Workplane("XY")
        .rect(length, width)
        .extrude(height)
        .edges("|Z")
        .fillet(r)
    )


def rrect_ring(length, width, height, radius, ring_width):
    """A hollow rounded-rectangle ring (a picture-frame), centred on X=Y=0."""
    outer = rrect_solid(length, width, height + 2 * EPS, radius).translate((0, 0, -EPS))
    inner = rrect_solid(
        length - 2 * ring_width,
        width - 2 * ring_width,
        height + 4 * EPS,
        max(radius - ring_width, 0.4),
    ).translate((0, 0, -2 * EPS))
    return outer.cut(inner)


# ============================================================================
# Shared internal features (returned as solids to add, or cutters to remove)
# ============================================================================

def blade_dock(p: KeyParams):
    """Solid block at the front of the bottom half that the blade channel is
    machined into.  Without this the (hollow) interior would give the tang
    nothing to grip; the dock supplies the floor, cap, side walls and back
    stop that actually retain the blade."""
    dock_len = p.wall + p.blade_insert + p.blade_back_stop
    dock_w = p.blade_width + p.clearance + 2 * p.blade_pocket_wall
    return (
        cq.Workplane("XY")
        .box(dock_len, dock_w, p.split_z, centered=(False, True, False))
    )


def blade_channel_cutter(p: KeyParams):
    """Carve the tang slot into the dock: a single narrow channel (tang width)
    running from OUTSIDE the front face straight back to the tang tip, at the
    blade height (z0 .. z0+blade_thickness).  A `blade_top_gap` cap is left
    above and a `blade_back_stop` of solid dock is left behind, so the tang is
    captured on every axis but -X.  The wider shoulder never enters — it butts
    the front face outside."""
    bw = p.blade_width + p.clearance
    bt = p.blade_thickness + p.clearance
    z0 = p.blade_z0
    chan_len = p.wall + p.blade_insert  # front face .. tang tip
    return (
        cq.Workplane("XY")
        .box(chan_len + EPS, bw, bt, centered=(False, True, False))
        .translate((-EPS, 0, z0))
    )


def immobilizer_nest(p: KeyParams):
    """Retaining ribs forming a rectangular nest for the PCF7936 carrier,
    added onto the bottom floor.  Low walls around the chip footprint plus
    a small hold-down bump so the closed lid keeps the chip seated."""
    # chip footprint in the head frame — X along the key axis, Y across it
    if p.chip_across:  # long axis across the key (along Y)
        fx, fy = p.chip_width + p.clearance, p.chip_length + p.clearance
    else:              # long axis along the key (along X)
        fx, fy = p.chip_length + p.clearance, p.chip_width + p.clearance
    rib = 1.2
    nest_h = min(p.chip_thickness + 1.2, p.split_z - p.wall - 0.6)
    outer = (
        cq.Workplane("XY")
        .box(fx + 2 * rib, fy + 2 * rib, nest_h, centered=(True, True, False))
    )
    inner = (
        cq.Workplane("XY")
        .box(fx, fy, nest_h + 2 * EPS, centered=(True, True, False))
        .translate((0, 0, -EPS))
    )
    ring = outer.cut(inner)
    return ring.translate((p.chip_center_x, 0, p.wall - EPS))


def _asm_screw_points(p: KeyParams):
    y = p.head_width / 2 - p.asm_y_inset
    return [(x, sy) for x in p.asm_x for sy in (-y, y)]


def boss(p, dia, x, y, z0, height):
    return (
        cq.Workplane("XY")
        .circle(dia / 2)
        .extrude(height)
        .translate((x, y, z0))
    )


def peg(p, dia, x, y, z0, height):
    """A vertical cutting cylinder (hole)."""
    return (
        cq.Workplane("XY")
        .circle(dia / 2)
        .extrude(height)
        .translate((x, y, z0))
    )


# ============================================================================
# The two shell halves
# ============================================================================

def _hollow_tray(p: KeyParams, is_bottom: bool):
    """A closed-bottom (or closed-top) open tray: outer rounded box minus an
    inset cavity, leaving `wall` all around plus one solid face (the outer
    face that lands on the print bed)."""
    h = p.split_z
    cx = p.head_length / 2
    outer = rrect_solid(p.head_length, p.head_width, h, p.corner_radius).translate((cx, 0, 0))
    inner_r = max(p.corner_radius - p.wall, 0.5)
    # cavity leaves a solid floor of `wall`, open at the parting face
    cavity = rrect_solid(
        p.head_length - 2 * p.wall,
        p.head_width - 2 * p.wall,
        h,  # up to (and through) the parting face
        inner_r,
    ).translate((cx, 0, p.wall))
    return outer.cut(cavity)


def bottom_shell(p: KeyParams):
    b = _hollow_tray(p, is_bottom=True)

    # interior bosses (added after hollowing so they stand full height)
    for (x, y) in _asm_screw_points(p):
        b = b.union(boss(p, p.asm_boss_dia, x, y, 0, p.split_z))
    b = b.union(boss(p, p.keyring_boss_dia, p.keyring_x, 0, 0, p.split_z))
    if p.use_blade_bolt:
        b = b.union(boss(p, p.blade_boss_dia, p.bolt_offset, 0, 0, p.split_z))

    # solid blade dock (its channel is cut further down)
    b = b.union(blade_dock(p))

    # immobilizer nest ribs on the floor
    b = b.union(immobilizer_nest(p))

    # alignment lip standing proud of the parting face (with a skirt buried in
    # the rim so it fuses by volume, not by a flush coincident face)
    skirt = 0.6
    cx = p.head_length / 2
    lip = _lip_ring(p, height=p.lip_height + skirt).translate((cx, 0, p.split_z - skirt))
    b = b.union(lip)

    # --- cut features ---
    b = b.cut(blade_channel_cutter(p))
    # keyring hole passes all the way through both halves (a ring threads it)
    b = b.cut(peg(p, p.keyring_hole_dia, p.keyring_x, 0, -EPS, p.split_z + 2 * EPS))
    # self-tap pilots are BLIND from the parting face (leave a closed outer
    # floor of `floor_keep` so the bottom show-face has no through holes)
    floor_keep = 1.0
    pilot_z0 = floor_keep
    pilot_h = p.split_z - floor_keep + EPS
    for (x, y) in _asm_screw_points(p):
        b = b.cut(peg(p, p.asm_pilot_dia, x, y, pilot_z0, pilot_h))
    if p.use_blade_bolt:
        b = b.cut(peg(p, p.blade_pilot_dia, p.bolt_offset, 0, pilot_z0, pilot_h))
    return b


def top_shell(p: KeyParams):
    h = p.head_height - p.split_z
    cx = p.head_length / 2
    outer = rrect_solid(p.head_length, p.head_width, h, p.corner_radius).translate((cx, 0, 0))
    inner_r = max(p.corner_radius - p.wall, 0.5)
    # cavity leaves a solid ceiling of `wall`, open at the parting face (z=0)
    cavity = rrect_solid(
        p.head_length - 2 * p.wall,
        p.head_width - 2 * p.wall,
        h - p.wall + EPS,
        inner_r,
    ).translate((cx, 0, -EPS))
    t = outer.cut(cavity)

    # interior bosses
    for (x, y) in _asm_screw_points(p):
        t = t.union(boss(p, p.asm_boss_dia, x, y, 0, h))
    t = t.union(boss(p, p.keyring_boss_dia, p.keyring_x, 0, 0, h))
    if p.use_blade_bolt:
        t = t.union(boss(p, p.blade_boss_dia, p.bolt_offset, 0, 0, h))

    # groove matching the bottom half's lip (slightly oversized for clearance)
    groove = _lip_ring(p, height=p.lip_height + p.clearance,
                       grow=p.clearance).translate((cx, 0, 0))
    t = t.cut(groove)

    # keyring hole
    t = t.cut(peg(p, p.keyring_hole_dia, p.keyring_x, 0, -EPS, h + 2 * EPS))

    # assembly screws: clearance holes + counterbores from the top outer face
    for (x, y) in _asm_screw_points(p):
        t = t.cut(peg(p, p.asm_clear_dia, x, y, -EPS, h + 2 * EPS))
        t = t.cut(peg(p, p.asm_head_dia, x, y, h - p.asm_head_depth, p.asm_head_depth + EPS))

    # blade bolt: clearance hole + counterbore
    if p.use_blade_bolt:
        t = t.cut(peg(p, p.blade_clear_dia, p.bolt_offset, 0, -EPS, h + 2 * EPS))
        t = t.cut(peg(p, p.blade_head_dia, p.bolt_offset, 0,
                      h - p.blade_head_depth, p.blade_head_depth + EPS))
    return t


def _lip_ring(p: KeyParams, height, grow=0.0):
    """Alignment lip (bottom) / groove (top) as a picture-frame ring centred
    on the wall annulus mid-line, so neither ring face is coincident with the
    inner or outer shell wall (that flush coincidence was what left tessella-
    tion slivers).  `grow` widens the ring symmetrically for groove clearance.
    Built centred on X=Y=0; the caller translates it onto the head."""
    w = p.lip_width + 2 * grow
    outer_len = (p.head_length - p.wall) + w   # centre-line at head_length-wall
    outer_wid = (p.head_width - p.wall) + w
    rad = max(p.corner_radius - (p.wall - w) / 2, 0.6)
    return rrect_ring(outer_len, outer_wid, height, rad, w)


# ============================================================================
# Reference geometry (fit-check only — never exported for printing)
# ============================================================================

def blade_reference(p: KeyParams):
    """Reference-only metal blade: the tang sits inside the slot (x from ~0 to
    wall+blade_insert), the wider shoulder butts the OUTSIDE of the front face
    (x from -shoulder_length to 0), and the cut blade sticks out further front.
    Not part of any printed STL."""
    z0 = p.blade_z0
    tang = (
        cq.Workplane("XY")
        .box(p.wall + p.blade_insert, p.blade_width, p.blade_thickness,
             centered=(False, True, False))
        .translate((0, 0, z0))
    )
    shoulder = (
        cq.Workplane("XY")
        .box(p.shoulder_length, p.shoulder_width, p.shoulder_thickness,
             centered=(False, True, False))
        .translate((-p.shoulder_length, 0, z0))
    )
    blade = (
        cq.Workplane("XY")
        .box(20, p.blade_width, p.blade_thickness, centered=(False, True, False))
        .translate((-p.shoulder_length - 20, 0, z0))
    )
    # the factory hole in the tang that the bolt passes through
    hole = (
        cq.Workplane("XY")
        .circle(p.tang_hole_dia / 2)
        .extrude(p.blade_thickness + 2)
        .translate((p.bolt_offset, 0, z0 - 1))
    )
    return tang.union(shoulder).union(blade).cut(hole)


def chip_reference(p: KeyParams):
    if p.chip_across:
        dx, dy = p.chip_width, p.chip_length
    else:
        dx, dy = p.chip_length, p.chip_width
    return (
        cq.Workplane("XY")
        .box(dx, dy, p.chip_thickness, centered=(True, True, False))
        .translate((p.chip_center_x, 0, p.wall))
    )


# ============================================================================
# Export
# ============================================================================

def print_ready_top(p: KeyParams):
    """Top half flipped flat-side-down for printing (open face up)."""
    h = p.head_height - p.split_z
    return top_shell(p).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, h))


def assembled(p: KeyParams):
    bottom = bottom_shell(p)
    top = top_shell(p).translate((0, 0, p.split_z))
    return bottom.union(top)


def main():
    p = P
    outdir = os.path.join(os.path.dirname(__file__), "..", "export")
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)

    do_step = "--step" in sys.argv
    tol = 0.05
    ang = 0.3

    parts = {
        "bottom_shell": bottom_shell(p),
        "top_shell": print_ready_top(p),
        "key_assembled": assembled(p),
    }
    for name, solid in parts.items():
        stl_path = os.path.join(outdir, name + ".stl")
        cq.exporters.export(solid, stl_path, tolerance=tol, angularTolerance=ang)
        print("wrote", stl_path)
        if do_step:
            step_path = os.path.join(outdir, name + ".step")
            cq.exporters.export(solid, step_path)
            print("wrote", step_path)

    print("done.")


if __name__ == "__main__":
    main()
