#!/usr/bin/env python3
"""Replace U3 DIP-64 module with PGA-68 in 68000sbc.kicad_pcb (KiCad 5 format).

- Pad numbers in MC68HC000_PGA68.kicad_mod == DIP-64 pin numbers, so nets map 1:1.
- PGA center (63.5, 45.72): one grid right of the old DIP anchor, clearing the
  top-left mounting hole.
- X1/X2 oscillator (stacked alt footprints) move to (72.39, 76.2), next to the
  PGA CLK pad (E1 = pad 15 at abs (74.93, 46.99)).
- Removes old traces: all copper in PGA zone and old-oscillator zone; U3-net
  copper in the old DIP region.
- Extends the top board edge up by 6.445 mm so the PGA fits.

Run from the 68k-nano directory. Makes no backup itself -- back up first!
"""
import math
import re
import sys

PCB = "68000sbc.kicad_pcb"
MOD = "PadRows.pretty/MC68HC000_PGA68.kicad_mod"

CENTER = (63.5, 45.72)
OSC_OLD_AT = "    (at 55.88 63.5 90)"
OSC_NEW_AT = "    (at 72.39 76.2 90)"
PGA_ZONE = (50.0, 31.5, 77.0, 59.0)    # clear ALL copper (pads + clearance)
OSC_ZONE = (47.3, 47.3, 56.9, 64.5)    # old oscillator spot: clear ALL copper
DIP_ZONE = (58.9, 43.6, 85.9, 126.6)   # old DIP area: clear U3-net copper
OLD_TOP_Y, NEW_TOP_Y = 38.735, 32.29   # board top edge move
OLD_ARC_Y, NEW_ARC_Y = 41.275, 34.83   # top corner arc centers


def block_end(s, i):
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError("unbalanced")


def inside(x, y, zone):
    x0, y0, x1, y1 = zone
    return x0 <= x <= x1 and y0 <= y <= y1


def rot(x, y, deg):
    """KiCad: +deg = CCW, board y axis points down."""
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t),
            -x * math.sin(t) + y * math.cos(t))


src = open(PCB).read()

# ---- 1. extract DIP module & its pad->net map -------------------------------
start = src.index("  (module Package_DIP:DIP-64_W22.86mm_Socket")
end = block_end(src, src.index("(", start))
dip = src[start:end]

pad_net = {}   # pad number -> raw "(net N NAME)" clause
for m in re.finditer(
    r'\(pad (\d+) thru_hole \w+ \(at [^)]*\) \(size [^)]*\) \(drill [^)]*\)'
    r' \(layers [^)]*\)\s*\n\s*(\(net \d+ .+?\))\)', dip):
    pad_net[m.group(1)] = m.group(2)
print(f"DIP pads with nets: {len(pad_net)}")
if len(pad_net) != 64:
    sys.exit("expected 64 DIP pads")
u3_nets = {int(re.match(r'\(net (\d+)', c).group(1)) for c in pad_net.values()}

# ---- 2. parse PGA footprint pads -------------------------------------------
mod = open(MOD).read()
pga_pads = re.findall(
    r'\(pad "([^"]+)" thru_hole (rect|circle) \(at ([-\d.]+) ([-\d.]+)\)', mod)
assert len(pga_pads) == 68, len(pga_pads)

# ---- 3. build the new module (KiCad 5 dialect) ------------------------------
L = []
L.append('  (module PadRows:MC68HC000_PGA68 (layer F.Cu) (tedit 5A02E8C5) (tstamp 5EDC3963)')
L.append(f'    (at {CENTER[0]} {CENTER[1]})')
L.append('    (descr "MC68HC000/MC68000/MC68010 PGA-68 (RC suffix), 2.54mm grid; pad numbers match DIP-64 pinout")')
L.append('    (tags "PGA68 68000 CPU")')
L.append('    (path /5ED415C8)')
L.append('    (fp_text reference U3 (at 0 -14.5) (layer F.SilkS)')
L.append('      (effects (font (size 1 1) (thickness 0.15)))')
L.append('    )')
L.append('    (fp_text value MC68HC000RC10 (at 0 14.5) (layer F.Fab)')
L.append('      (effects (font (size 1 1) (thickness 0.15)))')
L.append('    )')
L.append('    (fp_text user A1 (at 13.5 13) (layer F.SilkS)')
L.append('      (effects (font (size 1 1) (thickness 0.15)))')
L.append('    )')
L.append('    (fp_circle (center 11.43 11.43) (end 12.43 11.43) (layer F.SilkS) (width 0.3))')
for half, layer, w in ((13.0, "F.CrtYd", 0.05), (12.4, "F.SilkS", 0.12), (12.2, "F.Fab", 0.1)):
    pts = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for k in range(4):
        (x1, y1), (x2, y2) = pts[k], pts[(k + 1) % 4]
        L.append(f'    (fp_line (start {x1} {y1}) (end {x2} {y2}) (layer {layer}) (width {w}))')
for name, shape, x, y in pga_pads:
    pad_id = '""' if name == "~" else name
    line = (f'    (pad {pad_id} thru_hole {shape} (at {x} {y})'
            f' (size 1.7 1.7) (drill 0.9) (layers *.Cu *.Mask)')
    if name in pad_net:
        L.append(line)
        L.append(f'      {pad_net[name]})')
    else:
        L.append(line + ')')
L.append('  )')
src = src[:start] + "\n".join(L) + src[end:]

# ---- 4. move the oscillators -------------------------------------------------
n_osc = src.count(OSC_OLD_AT + "\n")
if n_osc != 2:
    sys.exit(f"expected 2 oscillator at-clauses, found {n_osc}")
src = src.replace(OSC_OLD_AT + "\n", OSC_NEW_AT + "\n")
print("oscillators X1/X2 moved to (72.39, 76.2)")

# ---- 4b. move J5/J6 bus pad rows into the new top strip ----------------------
# Their left ends (x 68.58..76.2, y 40.005) collide with the PGA's right
# columns, and J3 blocks a pure rightward shift. The board-edge extension
# created an empty strip above; move them there: +10.16 mm right, pads to
# y 34.29 (same row line as PGA row K, clear of it by 3.8 mm).
for old_at, new_at, ref in (
        ("    (at 99.06 43.815)", "    (at 109.22 38.1)", "J5"),
        ("    (at 99.06 36.195)", "    (at 109.22 30.48)", "J6")):
    if src.count(old_at + "\n") != 1:
        sys.exit(f"{ref} at-clause not found uniquely")
    src = src.replace(old_at + "\n", new_at + "\n")
print("J5/J6 pad rows moved to top strip (pads now x 78.74..139.7, y 34.29)")

# ---- 5. check module pads against the PGA & old-osc zones (rotation-aware) ---
conflicts = []
for m in re.finditer(r'  \(module ([^ ]+) \(layer', src):
    s = m.start()
    e = block_end(src, src.index("(", s))
    blk = src[s:e]
    if "PGA68" in m.group(1):
        continue
    at = re.search(r'\n    \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    mx, my = float(at.group(1)), float(at.group(2))
    ang = float(at.group(3) or 0)
    ref = re.search(r'fp_text reference (\S+)', blk).group(1)
    for p in re.finditer(r'\(pad [^\s]+ (?:thru_hole|smd|np_thru_hole|connect) \w+'
                         r' \(at ([-\d.]+) ([-\d.]+)', blk):
        dx, dy = rot(float(p.group(1)), float(p.group(2)), ang)
        px, py = mx + dx, my + dy
        if inside(px, py, PGA_ZONE) or inside(px, py, OSC_ZONE):
            conflicts.append((ref, m.group(1), round(px, 2), round(py, 2)))
if conflicts:
    print("!! component pads inside cleared zones:")
    for c in conflicts:
        print("   ", c)
    sys.exit("aborting -- resolve placement conflicts first")
print("no component-pad conflicts in PGA/osc zones")

# ---- 6. remove old traces ----------------------------------------------------
seg_re = re.compile(
    r'  \(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
    r'[^\n]*\(net (\d+)\)[^\n]*\)\n')
via_re = re.compile(
    r'  \(via \(at ([-\d.]+) ([-\d.]+)\)[^\n]*\(net (\d+)\)\)\n')

removed = {"seg": 0, "via": 0}

def drop_seg(m):
    x1, y1, x2, y2 = (float(m.group(i)) for i in range(1, 5))
    net = int(m.group(5))
    hit = any(inside(x, y, z) for x, y in ((x1, y1), (x2, y2))
              for z in (PGA_ZONE, OSC_ZONE))
    hit = hit or (net in u3_nets and (
        inside(x1, y1, DIP_ZONE) or inside(x2, y2, DIP_ZONE)))
    if hit:
        removed["seg"] += 1
        return ""
    return m.group(0)

def drop_via(m):
    x, y, net = float(m.group(1)), float(m.group(2)), int(m.group(3))
    if (inside(x, y, PGA_ZONE) or inside(x, y, OSC_ZONE)
            or (net in u3_nets and inside(x, y, DIP_ZONE))):
        removed["via"] += 1
        return ""
    return m.group(0)

src = seg_re.sub(drop_seg, src)
src = via_re.sub(drop_via, src)
print(f"removed segments: {removed['seg']}, vias: {removed['via']}")

# ---- 7. verify oscillator destination is clear of remaining copper -----------
osc_pads_new = [(72.39, 76.2), (64.77, 76.2), (64.77, 60.96), (72.39, 60.96)]

def seg_point_dist(px, py, x1, y1, x2, y2):
    vx, vy, wx, wy = x2 - x1, y2 - y1, px - x1, py - y1
    c1 = vx * wx + vy * wy
    if c1 <= 0:
        return math.hypot(px - x1, py - y1)
    c2 = vx * vx + vy * vy
    if c2 <= c1:
        return math.hypot(px - x2, py - y2)
    t = c1 / c2
    return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))

warn = []
for m in seg_re.finditer(src):
    x1, y1, x2, y2 = (float(m.group(i)) for i in range(1, 5))
    for px, py in osc_pads_new:
        if seg_point_dist(px, py, x1, y1, x2, y2) < 1.6:
            warn.append(("segment", m.group(0).strip()[:80]))
for m in via_re.finditer(src):
    x, y = float(m.group(1)), float(m.group(2))
    for px, py in osc_pads_new:
        if math.hypot(px - x, py - y) < 1.7:
            warn.append(("via", m.group(0).strip()[:80]))
if warn:
    print("!! copper near new oscillator pads (fix in GUI):")
    for w in warn:
        print("   ", w)
else:
    print("oscillator destination clear")

# ---- 8. extend board top edge ------------------------------------------------
edits = [
    (f"(gr_line (start 45.72 {OLD_TOP_Y}) (end 167.64 {OLD_TOP_Y})",
     f"(gr_line (start 45.72 {NEW_TOP_Y}) (end 167.64 {NEW_TOP_Y})"),
    (f"(gr_arc (start 45.72 {OLD_ARC_Y}) (end 43.18 {OLD_ARC_Y}) (angle 90)",
     f"(gr_arc (start 45.72 {NEW_ARC_Y}) (end 43.18 {NEW_ARC_Y}) (angle 90)"),
    (f"(gr_arc (start 167.64 {OLD_ARC_Y}) (end 170.18 {OLD_ARC_Y}) (angle -90)",
     f"(gr_arc (start 167.64 {NEW_ARC_Y}) (end 170.18 {NEW_ARC_Y}) (angle -90)"),
    (f"(gr_line (start 43.18 127) (end 43.18 {OLD_ARC_Y})",
     f"(gr_line (start 43.18 127) (end 43.18 {NEW_ARC_Y})"),
    (f"(gr_line (start 170.18 {OLD_ARC_Y}) (end 170.18 127)",
     f"(gr_line (start 170.18 {NEW_ARC_Y}) (end 170.18 127)"),
]
for old, new in edits:
    if old not in src:
        sys.exit(f"edge edit not found: {old}")
    src = src.replace(old, new)
print("board edge extended:", OLD_TOP_Y, "->", NEW_TOP_Y)

# GND zone outlines (F.Cu + B.Cu) follow the new top edge
n = src.count(f"(xy 43.18 {OLD_TOP_Y})") + src.count(f"(xy 170.18 {OLD_TOP_Y})")
if n != 4:
    sys.exit(f"expected 4 zone corner points at old top edge, found {n}")
src = src.replace(f"(xy 43.18 {OLD_TOP_Y})", f"(xy 43.18 {NEW_TOP_Y})")
src = src.replace(f"(xy 170.18 {OLD_TOP_Y})", f"(xy 170.18 {NEW_TOP_Y})")
print("GND zone outlines extended to new top edge")

# ---- 9. strip stale zone fills (recomputed on load; stale data makes ---------
# ----    KiCad 9's legacy-fill conversion hang during DRC) --------------------
parts, i, nfill = [], 0, 0
while True:
    j = src.find("(filled_polygon", i)
    if j < 0:
        parts.append(src[i:])
        break
    parts.append(src[i:j])
    i = block_end(src, j)
    nfill += 1
src = "".join(parts)
print(f"stripped {nfill} stale filled_polygon blocks")

# ---- 10. sanity & write ------------------------------------------------------
if src.count("(") != src.count(")"):
    sys.exit("paren imbalance -- not writing")
open(PCB, "w").write(src)
print("OK, written", PCB)
