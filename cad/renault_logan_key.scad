// ============================================================================
// Renault Logan key shell — parametric model
// Phase 1: shell that accepts the mechanical key blade (with its factory
//          shoulder) and a PCF7936 immobilizer transponder chip.
// Phase 2 (not yet implemented): cavity for a Pharaon V16i alarm remote
//          ("teardrop" style fob) inside the same shell.
//
// Renders two halves ("top_shell" / "bottom_shell") that are joined with
// small self-tapping screws through printed bosses. The shells are split
// along a horizontal parting plane at mid-thickness so that all internal
// cavities (blade channel, chip nest, keyring hole) can be printed without
// supports — each half is just a shallow open tray built independently
// (not boolean-cut from a shared solid), which keeps the CGAL geometry
// manifold. Both halves print flat-side down (render_mode="top" reorients
// the top shell for printing; its assembled orientation is used only
// inside assembly()/assembly_open()).
//
// Blade retention (like OEM VAC-style keys): the blade is inserted fully
// into the shell -- its factory shoulder (wider than the blade) drops into
// a captured pocket so it can't be pulled back out -- and then bolted
// through the shoulder's factory hole with a screw threading into a boss
// in the bottom half, exactly like the factory-original key.
//
// The PCF7936 chip sits in a low-walled nest molded into the bottom half's
// floor (see immobilizer_nest()) -- drop the chip in before closing the lid.
//
// IMPORTANT — measure your own blank before printing:
// The blade/shoulder dimensions below are estimates for the Renault/Dacia
// NE73 / VA2 / VAC102 blade family. The PCF7936 nest dimensions are based
// on the NXP SOT385-1 package datasheet outline (~12 x 5 x 2mm) but clone
// chips vary -- measure yours. None of this is confirmed against a
// physical Logan key. Update the "MEASURE YOUR OWN PART" section with
// calipers before printing a final version; the rest of the model follows
// automatically.
//
// Usage:
//   openscad -o top.stl    -D 'render_mode="top"'    renault_logan_key.scad
//   openscad -o bottom.stl -D 'render_mode="bottom"' renault_logan_key.scad
//   openscad renault_logan_key.scad   (opens GUI, shows full assembly + refs)
// ============================================================================

/* [Render mode] */
// "assembly"        - both shells + reference blade/transponder, for viewing
// "assembly_open"   - same, but pulled apart along Z for inspection
// "top"             - top shell only (for STL export)
// "bottom"          - bottom shell only (for STL export)
// "blade_reference" - just the reference blade/shoulder solid
render_mode = "assembly"; // ["assembly","assembly_open","top","bottom","blade_reference"]

show_blade_reference        = true;
show_immobilizer_reference  = true;

$fn = 64;

// ============================================================================
// MEASURE YOUR OWN PART — replace with calipers on the actual Logan blank
// ============================================================================

// --- Mechanical key blade (NE73 / VA2 / VAC102 family — estimate) ---
blade_length     = 35;    // shoulder to tip
blade_width      = 10.5;  // widest part of the cut blade
blade_thickness  = 2.4;   // steel stock thickness

// --- Factory shoulder (the wider flat section between blade and old head) ---
shoulder_length    = 5;     // along key axis
shoulder_width     = 15;    // wider than the blade -> forms a retention step
shoulder_thickness = 2.4;   // usually same stock as the blade

// --- Immobilizer transponder: PCF7936 ("ID46"), a flat "stick" module,
// NXP package SOT385-1, ~12 x 5 x 2mm (per NXP datasheet). Not a glass
// capsule -- measure your actual chip if it's a different clone/package.
immobilizer_length    = 13;   // chip length + clearance
immobilizer_width     = 5.6;  // chip width + clearance
immobilizer_thickness = 2.4;  // chip thickness + clearance
immobilizer_offset    = 20;   // distance of nest center from front face (X)

// --- Assembly fit clearance applied to blade/shoulder pocket ---
fit_clearance = 0.3;

// ============================================================================
// Head shell envelope (adjust freely — this is the printed part)
// ============================================================================

head_length    = 46;   // front (blade side) to back
head_width     = 30;
head_height    = 13;   // total assembled thickness
wall_thickness = 2.2;
corner_radius  = 7;

split_z = head_height / 2;  // parting plane

// --- Keyring ---
keyring_hole_dia = 5;
keyring_boss_dia = 11;
keyring_offset   = 40; // from front face; leaves 6mm to the back edge

// --- Screw bosses (assembly screws through top shell into bottom shell) ---
// Sized for M2.5 self-tapping screws — adjust to whatever hardware you have.
screw_boss_dia   = 6.4;
screw_pilot_dia  = 2.0;  // bottom half: self-tap pilot hole
screw_clear_dia  = 2.6;  // top half: clearance hole for the screw shank
screw_head_dia   = 5.2;  // top half: counterbore for the screw head
screw_head_depth = 2.0;
screw_x_positions = [11, 29]; // offsets from front face
screw_y_offset     = head_width/2 - 5;

// --- Blade retaining screw (like OEM VAC-style keys: the blade is inserted
// fully into the shell and bolted through its factory shoulder hole so it
// can't be pulled back out). Uses the same hardware as the assembly screws
// above; only the boss diameter is separate since it has to fit inside the
// shoulder pocket. Align blade_screw_offset with the actual hole in your
// blade's shoulder (the hole itself is in the metal blade -- nothing to cut
// there, this only sizes/positions the plastic pilot and clearance holes).
use_blade_screw     = true;
blade_screw_boss_dia = 7.0;
blade_screw_offset   = wall_thickness + shoulder_length/2; // from front face

// --- Alignment lip around the parting line ---
lip_thickness = 1.0;
lip_depth     = 1.0;

// Small overlap added to every internal boolean cut so that cut faces never
// land exactly flush on another face (avoids CGAL coincident-plane / non-
// manifold artifacts). Purely numerical, has no visible effect on the part.
eps = 0.05;

// ============================================================================
// Helpers
// ============================================================================

module rounded_rect(l, w, r) {
    rr = min(r, l/2 - 0.01, w/2 - 0.01);
    hull() {
        for (x = [-1, 1], y = [-1, 1])
            translate([x*(l/2 - rr), y*(w/2 - rr)]) circle(r = rr);
    }
}

module rounded_box(l, w, h, r) {
    linear_extrude(height = h) rounded_rect(l, w, r);
}

// ============================================================================
// Reference geometry (NOT for printing — for fit-checking only)
// ============================================================================

// Blade + shoulder envelope, positioned so the shoulder is fully inserted
// into the shell's shoulder pocket (X in [wall_thickness, wall_thickness +
// shoulder_length], i.e. just inside the front face) and the blade continues
// further in -X, sticking out through the front face at X=0. Vertically
// centered on the parting plane (Z = split_z), matching the cavities below.
module blade_reference() {
    color("silver") {
        translate([wall_thickness - blade_length, -blade_width/2, split_z - blade_thickness/2])
            cube([blade_length, blade_width, blade_thickness]);
        translate([wall_thickness, -shoulder_width/2, split_z - shoulder_thickness/2])
            cube([shoulder_length, shoulder_width, shoulder_thickness]);
        if (use_blade_screw)
            translate([blade_screw_offset, 0, split_z - shoulder_thickness/2 - 1])
                cylinder(d = screw_clear_dia, h = shoulder_thickness + 2);
    }
}

// PCF7936 ("ID46") transponder — the real chip ships as a flat rectangular
// "stick" module (NXP package SOT385-1, ~12 x 5 x 2mm), not a glass capsule.
// Shown resting in its floor nest (see immobilizer_nest() below).
module immobilizer_reference() {
    color("darkslategray")
        translate([immobilizer_offset - immobilizer_length/2, -immobilizer_width/2, wall_thickness])
            cube([immobilizer_length, immobilizer_width, immobilizer_thickness]);
}

// ============================================================================
// Cavities, expressed in GLOBAL coordinates (X: 0 at front face, positive
// into the head; Z: 0 at the bottom outer face, split_z at the parting
// plane). Each half module below translates these into its own local frame.
// ============================================================================

module blade_slot_cavity_global() {
    bw = blade_width + fit_clearance;
    bt = blade_thickness + fit_clearance;
    sw = shoulder_width + fit_clearance;
    st = shoulder_thickness + fit_clearance;

    // narrow channel through the front wall (blade passes through here)
    translate([-1, -bw/2, split_z - bt/2])
        cube([wall_thickness + 1 + eps, bw, bt]);

    // wider pocket just inside the wall that captures the shoulder step
    translate([-eps, -sw/2, split_z - st/2])
        cube([wall_thickness + shoulder_length + fit_clearance + eps, sw, st]);
}

module keyring_hole_global() {
    translate([keyring_offset, 0, -1])
        cylinder(d = keyring_hole_dia, h = head_height + 2);
}

// Low retaining wall standing on the bottom floor, forming a snug pocket
// for the flat PCF7936 module. Added (not subtracted) directly in
// bottom_shell() — this is the "where do I insert the chip" feature.
module immobilizer_nest() {
    nest_wall   = 1.2;
    nest_height = min(immobilizer_thickness + 1.5, split_z - wall_thickness - 0.5);
    translate([immobilizer_offset, 0, wall_thickness])
        linear_extrude(height = nest_height)
            difference() {
                square([immobilizer_length + 2*nest_wall, immobilizer_width + 2*nest_wall], center = true);
                square([immobilizer_length, immobilizer_width], center = true);
            }
}

// ============================================================================
// Independent tray halves.
// bottom = true  -> spans global Z [0, split_z], open at the top (parting) face
// bottom = false -> spans global Z [split_z, head_height], open at the bottom face
// ============================================================================

module tray_box(bottom) {
    h = bottom ? split_z : head_height - split_z;
    translate([head_length/2, 0, 0]) rounded_box(head_length, head_width, h, corner_radius);
}

// Boss pillars are unioned in AFTER the interior is hollowed out (see
// bottom_shell()/top_shell()) so they stand full-height inside the empty
// interior instead of being chopped down to the floor/ceiling thickness by
// the hollow subtraction.
module tray_bosses(bottom) {
    h = bottom ? split_z : head_height - split_z;
    translate([keyring_offset, 0, 0]) cylinder(d = keyring_boss_dia, h = h);
    for (x = screw_x_positions, y = [-screw_y_offset, screw_y_offset])
        translate([x, y, 0]) cylinder(d = screw_boss_dia, h = h);
    if (use_blade_screw)
        translate([blade_screw_offset, 0, 0]) cylinder(d = blade_screw_boss_dia, h = h);
}

module tray_hollow(bottom) {
    h = bottom ? split_z : head_height - split_z;
    ir = max(corner_radius - wall_thickness, 0.5);
    if (bottom)
        translate([head_length/2, 0, wall_thickness])
            rounded_box(head_length - 2*wall_thickness, head_width - 2*wall_thickness,
                        h - wall_thickness + eps, ir);
    else
        translate([head_length/2, 0, -eps])
            rounded_box(head_length - 2*wall_thickness, head_width - 2*wall_thickness,
                        h - wall_thickness + eps, ir);
}

// Protruding alignment lip (added on the bottom half's open face) /
// matching groove (removed from the top half's open face).
module lip_profile() {
    ir = max(corner_radius - wall_thickness, 0.5);
    difference() {
        rounded_rect(head_length - 2*wall_thickness, head_width - 2*wall_thickness, ir);
        rounded_rect(head_length - 2*(wall_thickness + lip_thickness),
                     head_width  - 2*(wall_thickness + lip_thickness),
                     max(ir - lip_thickness, 0.3));
    }
}

module bottom_shell() {
    difference() {
        union() {
            difference() {
                tray_box(true);
                tray_hollow(true);
            }
            tray_bosses(true);
            immobilizer_nest();
            // protruding lip at the open (top) face
            translate([head_length/2, 0, split_z - eps])
                linear_extrude(height = lip_depth) lip_profile();
        }
        blade_slot_cavity_global();
        keyring_hole_global();
        // self-tap pilot holes for the assembly screws
        for (x = screw_x_positions, y = [-screw_y_offset, screw_y_offset])
            translate([x, y, -1]) cylinder(d = screw_pilot_dia, h = split_z + 2);
        // self-tap pilot hole for the blade retaining screw
        if (use_blade_screw)
            translate([blade_screw_offset, 0, -1]) cylinder(d = screw_pilot_dia, h = split_z + 2);
    }
}

module top_shell() {
    zshift = split_z;
    translate([0, 0, zshift])
    difference() {
        union() {
            difference() {
                tray_box(false);
                tray_hollow(false);
            }
            tray_bosses(false);
        }
        translate([0, 0, -zshift]) blade_slot_cavity_global();
        translate([0, 0, -zshift]) keyring_hole_global();
        // groove matching the bottom half's alignment lip (slightly larger
        // for clearance on both the inner and outer edge of the lip)
        translate([head_length/2, 0, -eps])
            linear_extrude(height = lip_depth + eps)
                offset(delta = fit_clearance) lip_profile();
        // clearance holes + counterbores for the assembly screws
        for (x = screw_x_positions, y = [-screw_y_offset, screw_y_offset]) {
            translate([x, y, -1])
                cylinder(d = screw_clear_dia, h = head_height - split_z + 2);
            translate([x, y, head_height - split_z - screw_head_depth])
                cylinder(d = screw_head_dia, h = screw_head_depth + 1);
        }
        // clearance hole + counterbore for the blade retaining screw
        if (use_blade_screw) {
            translate([blade_screw_offset, 0, -1])
                cylinder(d = screw_clear_dia, h = head_height - split_z + 2);
            translate([blade_screw_offset, 0, head_height - split_z - screw_head_depth])
                cylinder(d = screw_head_dia, h = screw_head_depth + 1);
        }
    }
}

// ============================================================================
// Assembly / output
// ============================================================================

module assembly(explode = 0) {
    bottom_shell();
    translate([0, 0, explode]) top_shell();
    if (show_blade_reference)
        translate([0, 0, explode]) blade_reference();
    // the chip nest lives entirely in the bottom half's floor, so the
    // reference chip stays put (doesn't travel with the top half) when exploded
    if (show_immobilizer_reference)
        immobilizer_reference();
}

// Top shell, reoriented flat-side down (as printed), instead of its
// assembled position (flat-side up). Use this for STL export / standalone
// viewing; assembly()/assembly_open() use top_shell() directly so the two
// halves stay correctly aligned relative to each other.
module top_shell_print() {
    translate([0, 0, head_height]) mirror([0, 0, 1]) top_shell();
}

if (render_mode == "assembly") {
    assembly(0);
} else if (render_mode == "assembly_open") {
    assembly(25);
} else if (render_mode == "top") {
    top_shell_print();
} else if (render_mode == "bottom") {
    bottom_shell();
} else if (render_mode == "blade_reference") {
    blade_reference();
}
