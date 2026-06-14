#!/usr/bin/env python3
"""Import the 4-layer FreeRouting session into the (already 4-layer, already
renamed) 68000sbc.kicad_pcb and save. Run with /usr/bin/python3.
"""
import sys
import pcbnew

PCB = "/home/delphic/win_share/Delphic/Make_68000_Great_Again/68k-nano/68000sbc.kicad_pcb"
SES = "/tmp/68000sbc_4l.ses"

b = pcbnew.LoadBoard(PCB)
print("copper layers:", b.GetCopperLayerCount())
before = len(b.GetTracks())
ok = pcbnew.ImportSpecctraSES(b, SES)
after = len(b.GetTracks())
print("ImportSpecctraSES:", ok, "| tracks", before, "->", after)
if not ok:
    sys.exit("SES import failed")
pcbnew.SaveBoard(PCB, b)
print("saved routed 4-layer board")
