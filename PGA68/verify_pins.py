#!/usr/bin/env python3
"""Verify the DIP-64 -> PGA-68 conversion pin-by-pin.

Run with KiCad's python from anywhere in the repo:
    /usr/bin/python3 PGA68/verify_pins.py

Checks:
 (1) Netlist integrity: U3 pad N -> net, original DIP board vs current PGA board.
     The original DIP board is read from git history (the pre-conversion commit);
     if git/that commit isn't available this section is skipped.
 (2) Physical placement: each footprint pad's actual grid location vs the
     MC68000 datasheet PGA pinout (Fig 11-2, bottom view), using the standard
     68000 DIP-64 pinout as independent ground truth.
"""
import os
import re
import subprocess
import sys
import tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                       # repo root (68k-nano)
NEW = os.path.join(REPO, "68000sbc.kicad_pcb")
ORIG_COMMIT = "87066cf"                            # last pre-conversion commit


def get_orig_board():
    """Extract the pre-conversion 68000sbc.kicad_pcb from git, or None."""
    try:
        data = subprocess.check_output(
            ["git", "-C", REPO, "show", f"{ORIG_COMMIT}:68000sbc.kicad_pcb"],
            stderr=subprocess.DEVNULL)
        fd, path = tempfile.mkstemp(suffix=".kicad_pcb")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path
    except Exception:
        return None


# --- standard MC68000 DIP-64 pinout: pin -> signal ---------------------------
DIP = {
    1: "D4", 2: "D3", 3: "D2", 4: "D1", 5: "D0", 6: "AS", 7: "UDS", 8: "LDS",
    9: "RW", 10: "DTACK", 11: "BG", 12: "BGACK", 13: "BR", 14: "VCC",
    15: "CLK", 16: "GND", 17: "HALT", 18: "RESET", 19: "VMA", 20: "E",
    21: "VPA", 22: "BERR", 23: "IPL2", 24: "IPL1", 25: "IPL0", 26: "FC2",
    27: "FC1", 28: "FC0", 29: "A1", 30: "A2", 31: "A3", 32: "A4", 33: "A5",
    34: "A6", 35: "A7", 36: "A8", 37: "A9", 38: "A10", 39: "A11", 40: "A12",
    41: "A13", 42: "A14", 43: "A15", 44: "A16", 45: "A17", 46: "A18",
    47: "A19", 48: "A20", 49: "VCC", 50: "A21", 51: "A22", 52: "A23",
    53: "GND", 54: "D15", 55: "D14", 56: "D13", 57: "D12", 58: "D11",
    59: "D10", 60: "D9", 61: "D8", 62: "D7", 63: "D6", 64: "D5",
}

# --- datasheet PGA pinout (bottom view): (row,col) -> signal -----------------
PGA = {
    ("K", 1): "NC", ("K", 2): "FC2", ("K", 3): "FC0", ("K", 4): "A1",
    ("K", 5): "A3", ("K", 6): "A4", ("K", 7): "A6", ("K", 8): "A7",
    ("K", 9): "A9", ("K", 10): "NC",
    ("J", 1): "BERR", ("J", 2): "IPL0", ("J", 3): "FC1", ("J", 4): "NC",
    ("J", 5): "A2", ("J", 6): "A5", ("J", 7): "A8", ("J", 8): "A10",
    ("J", 9): "A11", ("J", 10): "A14",
    ("H", 1): "E", ("H", 2): "IPL2", ("H", 3): "IPL1",
    ("H", 8): "A13", ("H", 9): "A12", ("H", 10): "A16",
    ("G", 1): "VMA", ("G", 2): "VPA", ("G", 9): "A15", ("G", 10): "A17",
    ("F", 1): "HALT", ("F", 2): "RESET", ("F", 9): "A18", ("F", 10): "A19",
    ("E", 1): "CLK", ("E", 2): "GND", ("E", 9): "VCC", ("E", 10): "A20",
    ("D", 1): "BR", ("D", 2): "VCC", ("D", 9): "GND", ("D", 10): "A21",
    ("C", 1): "BGACK", ("C", 2): "BG", ("C", 3): "RW",
    ("C", 8): "D13", ("C", 9): "A23", ("C", 10): "A22",
    ("B", 1): "DTACK", ("B", 2): "LDS", ("B", 3): "UDS", ("B", 4): "D0",
    ("B", 5): "D3", ("B", 6): "D6", ("B", 7): "D9", ("B", 8): "D11",
    ("B", 9): "D14", ("B", 10): "D15",
    ("A", 1): "NC", ("A", 2): "AS", ("A", 3): "D1", ("A", 4): "D2",
    ("A", 5): "D4", ("A", 6): "D5", ("A", 7): "D7", ("A", 8): "D8",
    ("A", 9): "D10", ("A", 10): "D12",
}
SIG_LOC = {}
for loc, sig in PGA.items():
    SIG_LOC.setdefault(sig, set()).add(loc)

ROWS_TTB = ["K", "J", "H", "G", "F", "E", "D", "C", "B", "A"]


def pad_nets(path):
    b = pcbnew.LoadBoard(path)
    u3 = b.FindFootprintByReference("U3")
    out = {}
    for p in u3.Pads():
        out[p.GetNumber()] = (p.GetNetname(),
                              pcbnew.ToMM(p.GetX() - u3.GetX()),
                              pcbnew.ToMM(p.GetY() - u3.GetY()))
    return out


def grid_of(x, y):
    """footprint (top-view) mm -> datasheet bottom-view (row,col)."""
    col = 10 - round((x + 11.43) / 2.54)
    ri = round((y + 11.43) / 2.54)
    if not (0 <= ri <= 9) or not (1 <= col <= 10):
        return None
    return (ROWS_TTB[ri], col)


new = pad_nets(NEW)

# ====================  (1) NETLIST INTEGRITY  ===============================
print("=" * 64)
print("(1) NETLIST INTEGRITY  — U3 pad -> net, original DIP vs new PGA")
print("=" * 64)
orig_path = get_orig_board()
diffs = 0
if orig_path:
    orig = pad_nets(orig_path)
    os.unlink(orig_path)
    for n in range(1, 65):
        s = str(n)
        on, nn = orig.get(s, ("<missing>",))[0], new.get(s, ("<missing>",))[0]
        if on != nn:
            diffs += 1
            print(f"  pad {n:2}: DIP='{on}'  PGA='{nn}'   <-- DIFFERENT")
    print(f"pads 1-64 compared; net differences: {diffs}")
else:
    diffs = None
    print(f"  (skipped: could not read {ORIG_COMMIT}:68000sbc.kicad_pcb from git)")

# ====================  (2) PHYSICAL PLACEMENT  =============================
print("\n" + "=" * 64)
print("(2) PHYSICAL PLACEMENT — footprint pad location vs datasheet PGA")
print("=" * 64)
bad = 0
for n in range(1, 65):
    sig = DIP[n]
    _, x, y = new[str(n)]
    g = grid_of(x, y)
    if g is None or g not in SIG_LOC.get(sig, set()):
        bad += 1
        print(f"  pad {n:2} sig={sig:5} at grid {g} "
              f"datasheet={sorted(SIG_LOC.get(sig, set()))}   <-- MISPLACED")
print(f"pads 1-64 checked against datasheet; misplaced: {bad}")

print("\nNC pads (should sit on datasheet NC cells K1,K10,J4,A1):")
for num, (net, x, y) in new.items():
    if not num.isdigit():
        g = grid_of(x, y)
        print(f"  pad '{num}' at grid {g}  "
              f"{'OK' if g in SIG_LOC['NC'] else 'NOT an NC cell!'}")

ok = (diffs in (0, None)) and bad == 0
print("\nSUMMARY: net-diffs=%s  misplaced=%d  ->  %s"
      % (diffs, bad, "PASS" if ok else "CHECK ABOVE"))
sys.exit(0 if ok else 1)
