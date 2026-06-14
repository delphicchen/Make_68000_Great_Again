#!/usr/bin/env python3
"""Import a FreeRouting .ses session back into 68000sbc.kicad_pcb.

Mirrors the renames done for the DSN export (duplicate REF** mounting holes and
the 4 unnamed PGA NC pads block Specctra I/O), then applies the routed wires/vias
and saves. Run with KiCad's python: /usr/bin/python3 import_ses.py

The SES routing is keyed by net name, so these cosmetic renames don't affect the
imported copper; we keep H1-4 (cleaner than 4 identical REF**).
"""
import sys
import pcbnew

PCB = "/home/delphic/win_share/Delphic/Make_68000_Great_Again/68k-nano/68000sbc.kicad_pcb"
SES = "/tmp/68000sbc.ses"

b = pcbnew.LoadBoard(PCB)

n = 0
for f in b.GetFootprints():
    if f.GetReference() == "REF**":
        n += 1
        f.SetReference("H%d" % n)
print("mounting holes renamed:", n)

u3 = b.FindFootprintByReference("U3")
i = 0
for p in u3.Pads():
    if p.GetNumber() == "":
        i += 1
        p.SetNumber("NC%d" % i)
print("U3 NC pads renamed:", i)

before = len(b.GetTracks())
ok = pcbnew.ImportSpecctraSES(b, SES)
after = len(b.GetTracks())
print("ImportSpecctraSES:", ok, "| tracks", before, "->", after)
if not ok:
    sys.exit("SES import failed")

pcbnew.SaveBoard(PCB, b)
print("saved", PCB)
