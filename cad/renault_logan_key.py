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
#      the fob's buttons so they can be pressed with the lid closed. A small
#      round WINDOW over the fob's blink indicator (lights on any button
#      press) is split from the top half at EXACTLY the window boundary (zero
#      clearance) into a second body — see indicator_window_insert() below.
#      export/top_shell_2color.3mf packages BOTH bodies as ONE multi-material
#      object (two coloured components under a single build item) — the top
#      half is ONE printable object in the slicer, no separate part to align,
#      no gluing: assign a filament to each component (e.g. orange body /
#      clear window) and a multi-material printer (Bambu AMS, Anycubic ACE,
#      ...) prints it as one job.
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

    # --- Status LED window: a small round see-through region over the fob's
    # blink indicator (lights up when ANY button is pressed). Sits ABOVE the
    # side open/close buttons (button_positions[1]/[2]), centred between them
    # -- fob-local X further back, Y centred. top_shell() is split into TWO
    # bodies at EXACTLY this cylinder (zero clearance, see indicator_window()
    # / indicator_window_insert()) and packaged as ONE multi-material object
    # in export/top_shell_2color.3mf -- a single printable object with two
    # colour components (e.g. orange body / clear window), no separate part,
    # no assembly. MEASURE against your board; the indicator moves with board
    # revisions. -----------------------------------------------------------
    indicator_dia: float = 6.0    # window diameter, about the size of a button
    indicator_x: float = 12.0     # fob-local X, further back than the side buttons
    indicator_y: float = 0.0      # fob-local Y, centred between them

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
    chip_thickness: float = 1.5
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


def indicator_window(p: KeyParams):
    """Boundary that splits the top ceiling into two bodies for multi-material
    printing: top_shell() is cut with this, indicator_window_insert() is
    exactly this cylinder -- ZERO clearance, so the two share a seamless
    boundary (no gap to press-fit or glue, just a filament change)."""
    h = p.head_height - p.split_z
    return cyl(p.indicator_dia,
              p.fob_center_x + p.indicator_x, p.indicator_y, -EPS, h + 2 * EPS)


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

    # round window over the blink indicator, split off as a second body for
    # multi-material printing -- see indicator_window_insert() below
    t = t.cut(indicator_window(p))

    # groove matching the bottom lip
    groove = lip_ring(p, p.lip_height + p.clearance, grow=p.clearance).translate((cx, 0, 0))
    t = t.cut(groove)

    # keyring hole through the extra rear body
    t = t.cut(cyl(p.keyring_hole_dia, p.keyring_x, p.keyring_y, -EPS, h + 2 * EPS))

    # rectangular button openings through the ceiling (the caps drop into
    # them), each rotated per button_angle -- not axis-aligned
    for i, (bx, by) in enumerate(p.button_positions):
        slot = button_slot_solid(p, bx, by, i, h + 2 * EPS, -EPS)
        t = t.cut(slot)

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


def indicator_window_insert(p: KeyParams):
    """The small body cut out of top_shell() by indicator_window() -- EXACTLY
    that cylinder (same diameter, no clearance), so it's a seamless fill, not
    a separate part to press in. Print it in a different filament/colour on a
    multi-material printer and the two bodies come out as one physical piece."""
    h = p.head_height - p.split_z
    return cyl(p.indicator_dia, p.fob_center_x + p.indicator_x, p.indicator_y, 0, h)


def print_ready_indicator_window_insert(p: KeyParams):
    """Same flip/translate as print_ready_top, so this lines up with the
    printed top half -- used to build the "clear" component of
    export/top_shell_2color.3mf, not exported as a standalone file."""
    h = p.head_height - p.split_z
    return indicator_window_insert(p).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, h))


def assembled(p: KeyParams):
    top = top_shell(p).union(indicator_window_insert(p))
    return bottom_shell(p).union(top.translate((0, 0, p.split_z)))


def export_multicolor_3mf(parts, path, tolerance=0.05, angular_tolerance=0.3):
    """Write `parts` (a list of (solid, name, "#RRGGBBAA") tuples) as a SINGLE
    3MF object made of one coloured component per part -- one build item, one
    entry in the slicer's object list, each component independently
    assignable to a filament/extruder. This is the standard 3MF mechanism
    slicers (Bambu Studio, OrcaSlicer/Anycubic, PrusaSlicer, ...) use for a
    single multi-material part, so it prints as ONE physical object with no
    manual alignment of separate STLs. Hand-built (zip + core-spec XML) since
    cadquery/OCC has no multi-object 3MF writer."""
    import zipfile

    mesh_objects = []          # (object_id, name, vertices, triangles, material_index)
    next_id = 2                # id 1 is the <basematerials> resource
    for solid, name, _rgba in parts:
        verts, tris = solid.val().tessellate(tolerance, angular_tolerance)
        mesh_objects.append((next_id, name, verts, tris, len(mesh_objects)))
        next_id += 1
    combo_id = next_id

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<model unit="millimeter" xml:lang="en-US" '
          'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
          '  <resources>',
          '    <basematerials id="1">']
    for _solid, name, rgba in parts:
        xml.append('      <base name="%s" displaycolor="%s"/>' % (name, rgba))
    xml.append('    </basematerials>')

    for obj_id, name, verts, tris, mat_idx in mesh_objects:
        xml.append('    <object id="%d" name="%s" type="model" pid="1" pindex="%d">'
                   % (obj_id, name, mat_idx))
        xml.append('      <mesh>')
        xml.append('        <vertices>')
        for v in verts:
            xml.append('          <vertex x="%.4f" y="%.4f" z="%.4f"/>' % (v.x, v.y, v.z))
        xml.append('        </vertices>')
        xml.append('        <triangles>')
        for t in tris:
            xml.append('          <triangle v1="%d" v2="%d" v3="%d"/>' % (t[0], t[1], t[2]))
        xml.append('        </triangles>')
        xml.append('      </mesh>')
        xml.append('    </object>')

    xml.append('    <object id="%d" name="TopShell" type="model">' % combo_id)
    xml.append('      <components>')
    for obj_id, _name, _v, _t, _m in mesh_objects:
        xml.append('        <component objectid="%d"/>' % obj_id)
    xml.append('      </components>')
    xml.append('    </object>')
    xml.append('  </resources>')
    xml.append('  <build>')
    xml.append('    <item objectid="%d"/>' % combo_id)
    xml.append('  </build>')
    xml.append('</model>')

    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>'
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", "\n".join(xml))


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

    # top_shell as ONE two-colour object: orange body + clear indicator window,
    # both baked into a single 3MF build item (see export_multicolor_3mf).
    export_multicolor_3mf(
        [
            (print_ready_top(p), "Orange body", "#FF7A00FF"),
            (print_ready_indicator_window_insert(p), "Clear window", "#EAF6FF4D"),
        ],
        os.path.join(outdir, "top_shell_2color.3mf"),
    )
    print("wrote top_shell_2color.3mf")
    print("done.")


if __name__ == "__main__":
    main()
