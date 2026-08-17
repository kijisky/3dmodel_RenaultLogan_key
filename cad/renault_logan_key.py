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
#      the fob's buttons so they can be pressed with the lid closed, each
#      ringed by a shallow FINGER DISH in the outer face so a fingertip
#      settles onto the button instead of poking a flat slot edge.
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
import math
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
    head_length: float = 58.0    # front (blade side) -> back. The rear part is
    #   extra solid body beyond the fob; the keyring hole goes through it.
    head_width: float = 34.0
    head_height: float = 12.0    # total assembled thickness
    split_ratio: float = 0.65    # fraction of head_height in the BOTTOM half.
    #   >0.5 makes the bottom (blade/chip/fob-tray) thicker and the top (lid)
    #   thinner — more of the fob body then sits in the sturdier bottom tray.
    corner_radius: float = 8.0
    wall: float = 2.2            # outer wall / floor / ceiling thickness

    # --- Mechanical blade — the TANG slides into the head; the wider SHOULDER
    # stays OUTSIDE and butts the front face (NE73/VA2/VAC102 — ESTIMATE) ----
    blade_width: float = 9.0     # width of the metal tang (reference)
    blade_slot_width: float = 10.0  # width of the CUT slot (a touch wider than
    #   the tang for an easy fit and easy support removal)
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
    fob_clearance: float = 0.4   # gap around the fob in its cavity
    fob_center_x: float = 31.5   # cavity centre from the front face
    # Retainer ribs: ONE small crush rib per long (Y) cavity wall, gripping the
    # fob edge so it can't rattle or spin. Positioned `fob_retainer_dx` from the
    # fob centre along X (+ = toward the back/fob hole, away from the blade);
    # `fob_retainer_thickness` is the rib's length along the wall; `grip` is
    # the interference past the fob edge.
    fob_retain: bool = True
    fob_retainer_thickness: float = 1.0
    fob_retainer_dx: float = 3.0
    fob_retainer_grip: float = 0.6

    # --- Fob buttons: 3 buttons on ONE face -> RECTANGULAR openings through the
    # TOP half that the button caps drop into. Positions are (x, y) in FOB-LOCAL
    # mm (x along fob_length toward the back, y across). MEASURE against your
    # board. The opening is generous so a small position error still clears. ---
    button_slot_l: float = 7.0   # opening size along its own long axis
    button_slot_w: float = 5.0   # opening size along its own short axis
    button_slot_r: float = 1.2   # corner radius of the opening
    button_positions: tuple = ((-6.0, 0.1), (6.0, 6.0), (6.0, -6.0))
    # Each opening is rotated so it isn't axis-aligned (matches the angled
    # button layout on the actual fob board, see photos). button_radial=True
    # auto-picks each angle as the radial direction from the fob centre through
    # that button (a common layout for round remotes); set False and use
    # button_angles to give explicit degrees per button instead.
    button_radial: bool = True
    button_angles: tuple = (0.0, 0.0, 0.0)   # used only if button_radial=False

    # Shallow finger dish cut into the OUTER face around each opening, so a
    # fingertip settles onto the button instead of poking a flat slot edge --
    # a plain hole through a hard shell is uncomfortable to press. Sphere-cap
    # cut, sized independently of the slot: button_dimple_dia is the dish's
    # rim diameter, button_dimple_depth how deep it is at the centre.
    button_dimple: bool = True
    button_dimple_dia: float = 10.0
    button_dimple_depth: float = 1.2

    # --- Immobilizer transponder PCF7936 ("ID46") carrier, by the blade.
    # Fully-walled nest beside the blade, molded ENTIRELY into the bottom half.
    # Near the top of the nest (just below the parting plane) the opening
    # NARROWS into an overhanging snap lip on the short (width) sides: you press
    # the chip down past the lip (the thin walls flex briefly), then it springs
    # back and the lip overhangs the chip from above — the chip is captive in
    # the BOTTOM HALF ALONE, with no top half needed. The top's hold-down pad
    # (below) adds a second, belt-and-suspenders layer once the lid is on. ----
    chip_length: float = 12.0
    chip_width: float = 6.0
    chip_thickness: float = 3.0
    chip_center_x: float = 9.5    # positioned to leave a real wall front & back
    chip_center_y: float = 9.5    # offset to the side of the blade slot
    chip_across: bool = False     # False -> long axis along X (along the key)
    chip_snap_lip_height: float = 1.0   # height of the overhanging retention lip
    chip_snap_overlap: float = 0.4      # lip overhang past the chip edge, per side
    chip_holddown: bool = True    # extra pad on the lid, presses the chip down
    chip_holddown_gap: float = 0.1

    # --- Keyring hole: a plain Z hole through the extra solid body behind the
    # fob (no protruding loop — the body is simply longer). -------------------
    keyring_hole_dia: float = 6.0
    keyring_x: float = 53.0          # from the front face (sits in the rear body)
    keyring_y: float = 8.0           # off-centre, toward one edge (was 0 = centred)

    # --- Assembly screws: 2 at the back corners; the blade bolt clamps the
    # front. Sized for M2.5 self-tapping screws. ----------------------------
    asm_pilot_dia: float = 2.0
    asm_clear_dia: float = 1.0
    asm_head_dia: float = 5.0
    asm_head_depth: float = 2.0
    asm_positions: tuple = ((51.0, 13.0), (51.0, -13.0))

    # --- Parting-line alignment lip --------------------------------------
    lip_width: float = 1.0
    lip_height: float = 1.0

    # --- Fit / print tuning ----------------------------------------------
    clearance: float = 0.30      # gap around blade / chip pockets
    fn: int = 96

    # --- Derived ---------------------------------------------------------
    split_z: float = field(init=False)

    def __post_init__(self):
        self.split_z = self.head_height * self.split_ratio

    @property
    def blade_z0(self):
        """Underside of the tang slot (tang rides high in the bottom half)."""
        return self.split_z - (self.blade_thickness + self.clearance) - self.blade_top_gap

    @property
    def chip_floor(self):
        """Floor of the chip nest. The nest is OPEN at the parting plane so the
        chip drops in from above while the shell is open, then the closed lid
        caps it — so the floor sits chip_thickness (+a little) below the split."""
        return max(self.split_z - self.chip_thickness - 0.6, self.wall + 0.3)

    @property
    def chip_snap_z(self):
        """Z where the nest narrows into the overhanging retention lip: full
        width below this, an overhang from here up to the parting plane."""
        z = self.split_z - self.chip_snap_lip_height
        chip_top = self.chip_floor + self.chip_thickness
        return max(z, chip_top + 0.15)


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


def ball(radius, x, y, z):
    """Sphere centred at (x, y, z) -- used to cut a shallow finger dish."""
    return cq.Workplane("XY").sphere(radius).translate((x, y, z))


def button_angle(p: "KeyParams", index, bx, by):
    """Rotation (degrees) for the button opening at FOB-LOCAL offset (bx, by).
    Radial mode points the opening's long axis away from the fob centre —
    matches the angled button layout typical of round remotes/seen in photos."""
    if p.button_radial:
        return math.degrees(math.atan2(by, bx))
    return p.button_angles[index]


def button_slot_solid(p: "KeyParams", bx, by, index, height, z0):
    """A rounded rectangular opening, rotated to button_angle, centred on the
    fob-local offset (bx, by) from the fob centre."""
    angle = button_angle(p, index, bx, by) + 90
    slot = rrect_solid(p.button_slot_l, p.button_slot_w, height, p.button_slot_r)
    slot = slot.rotate((0, 0, 0), (0, 0, 1), angle)
    return slot.translate((p.fob_center_x + bx, by, z0))


def button_dimple_cut(p: "KeyParams", bx, by):
    """Shallow spherical-cap dish in the top's OUTER face around a button
    opening. Sagitta geometry: a sphere of radius R positioned so its cap,
    sliced by the outer face (z=h), has the requested rim radius r and centre
    depth d -- R = (r^2 + d^2) / (2d), sphere centred d above that face minus
    its own radius (i.e. R - d above z=h)."""
    h = p.head_height - p.split_z
    r = p.button_dimple_dia / 2
    d = p.button_dimple_depth
    R = (r * r + d * d) / (2 * d)
    return ball(R, p.fob_center_x + bx, by, h + R - d)


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
    """Tang slot cut into the solid front at the blade height. It runs THROUGH
    from the front face into the fob cavity (so the tang slot is a passage, not
    a blind pocket — support material pushes straight out into the interior).
    The blade's own insertion depth is still set by the shoulder butting the
    front face, so no internal back stop is needed."""
    bw = p.blade_slot_width
    bt = p.blade_thickness + p.clearance
    fob_front = p.fob_center_x - p.fob_length / 2 - p.fob_clearance
    chan_len = fob_front + 2.5          # break through into the fob cavity
    return box_at(chan_len + EPS, bw, bt, -EPS, 0, p.blade_z0, cx=False)


def chip_pocket(p: KeyParams):
    """Nest for the PCF7936 carrier, cut into the solid front, molded ENTIRELY
    into the bottom half. Full width from the floor up to chip_snap_z; from
    there up to the parting plane the opening NARROWS (an overhanging snap
    lip on the short/width sides) — you press the chip down past the lip
    (the thin wall flexes briefly) and it is then captive with no top half
    needed at all."""
    if p.chip_across:
        full_l, full_w = p.chip_width + p.clearance, p.chip_length + p.clearance
    else:
        full_l, full_w = p.chip_length + p.clearance, p.chip_width + p.clearance

    z0 = p.chip_floor
    snap_z = p.chip_snap_z
    lower = box_at(full_l, full_w, snap_z - z0 + EPS, p.chip_center_x, p.chip_center_y, z0)

    if p.chip_across:
        narrow_l = max(full_l - 2 * p.chip_snap_overlap, 1.0)
        narrow_w = full_w
    else:
        narrow_l = full_l
        narrow_w = max(full_w - 2 * p.chip_snap_overlap, 1.0)
    upper = box_at(narrow_l, narrow_w, p.split_z - snap_z + EPS,
                   p.chip_center_x, p.chip_center_y, snap_z - EPS)

    return lower.union(upper)


def chip_holddown_pad(p: KeyParams):
    """A pad on the LID (top half) that reaches down through the nest's snap
    lip opening and presses the chip — a second retention layer once the lid
    is on, on top of the bottom half's own snap lip. Sized to the NARROW
    (post-lip) opening so it actually fits through. Returned in the top
    half's LOCAL frame (z=0 is the parting face), protruding below it."""
    chip_top = p.chip_floor + p.chip_thickness
    depth = p.split_z - chip_top - p.chip_holddown_gap
    if depth <= 0:
        return None
    if p.chip_across:
        pad_l = max(p.chip_width - 2 * p.chip_snap_overlap - 0.6, 1.0)
        pad_w = p.chip_length - 1.0
    else:
        pad_l = p.chip_length - 1.0
        pad_w = max(p.chip_width - 2 * p.chip_snap_overlap - 0.6, 1.0)
    return box_at(pad_l, pad_w, depth + EPS, p.chip_center_x, p.chip_center_y, -depth)


def fob_retainers(p: KeyParams):
    """One small crush rib per long (Y) cavity wall, gripping the fob edge so
    it can't rattle or spin. Added into the bottom half, floor to parting."""
    g = p.fob_retainer_grip
    rib_len = p.fob_retainer_thickness          # rib length along the wall (X)
    inner = p.fob_width / 2 - g                 # protrudes `grip` past the fob edge
    outer = p.fob_width / 2 + p.fob_clearance + 1.0   # buried in the wall
    cy_pos = (inner + outer) / 2
    dy = outer - inner
    rib_x = p.fob_center_x + p.fob_retainer_dx
    ribs = None
    for sy in (1, -1):
        r = box_at(rib_len, dy, p.split_z - p.wall + EPS, rib_x, sy * cy_pos, p.wall)
        ribs = r if ribs is None else ribs.union(r)
    return ribs


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

    # retainer ribs that grip the fob so it can't rattle or spin
    if p.fob_retain:
        b = b.union(fob_retainers(p))

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
    # keyring hole through the extra rear body
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

    # No cavity cut here: an early print with the fob pocket open on BOTH
    # halves let the fob rattle (too much total depth). Leaving the top solid
    # over the fob region relies on the bottom pocket alone to hold it snug.

    # groove matching the bottom lip
    groove = lip_ring(p, p.lip_height + p.clearance, grow=p.clearance).translate((cx, 0, 0))
    t = t.cut(groove)

    # keyring hole through the extra rear body
    t = t.cut(cyl(p.keyring_hole_dia, p.keyring_x, p.keyring_y, -EPS, h + 2 * EPS))

    # rectangular button openings through the ceiling (the caps drop into
    # them), each rotated per button_angle -- not axis-aligned. A shallow
    # finger dish around each opening makes it comfortable to press.
    for i, (bx, by) in enumerate(p.button_positions):
        slot = button_slot_solid(p, bx, by, i, h + 2 * EPS, -EPS)
        t = t.cut(slot)
        if p.button_dimple:
            t = t.cut(button_dimple_cut(p, bx, by))

    # hold-down pad that traps the chip against its nest when the lid closes
    if p.chip_holddown:
        pad = chip_holddown_pad(p)
        if pad is not None:
            t = t.union(pad)

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
    return box_at(dx, dy, p.chip_thickness, p.chip_center_x, p.chip_center_y, p.chip_floor)


def fob_reference(p: KeyParams):
    """Round fob body + 3 button bumps, resting on the cavity floor."""
    body = rrect_solid(p.fob_length, p.fob_width, p.fob_body_thickness, p.fob_corner_r)\
        .translate((p.fob_center_x, 0, p.wall))
    fob = body
    for i, (bx, by) in enumerate(p.button_positions):
        angle = button_angle(p, i, bx, by) + 90
        btn = (
            rrect_solid(p.button_slot_l - 1.5, p.button_slot_w - 1.5,
                       p.fob_button_height, max(p.button_slot_r - 0.3, 0.3))
            .rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((p.fob_center_x + bx, by, p.wall + p.fob_body_thickness))
        )
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
