#!/usr/bin/env python3
"""Convert 68000sbc to 4 copper layers and export a fresh Specctra DSN.

Strategy: all 4 copper layers as signal/routing layers so FreeRouting can escape
the PGA inner pins (2 signal layers can't). GND/VCC pours are added on the inner
layers AFTER routing (see add_pours.py). Mirrors the ref/pad renames needed for
Specctra I/O (duplicate REF** holes + unnamed PGA NC pads).

Run with KiCad python: /usr/bin/python3 convert_4layer.py
"""
import pcbnew

PCB = "/home/delphic/win_share/Delphic/Make_68000_Great_Again/68k-nano/68000sbc.kicad_pcb"
DSN = "/tmp/68000sbc_4l.dsn"

b = pcbnew.LoadBoard(PCB)
print("copper layers before:", b.GetCopperLayerCount())

# cosmetic renames so Specctra export succeeds and stays consistent for import
n = 0
for f in b.GetFootprints():
    if f.GetReference() == "REF**":
        n += 1
        f.SetReference("H%d" % n)
u3 = b.FindFootprintByReference("U3")
i = 0
for p in u3.Pads():
    if p.GetNumber() == "":
        i += 1
        p.SetNumber("NC%d" % i)
print(f"renamed {n} mounting holes, {i} NC pads")

b.SetCopperLayerCount(4)
print("copper layers after:", b.GetCopperLayerCount())
# report the enabled copper layer names/ids
for lid in b.GetEnabledLayers().CuStack():
    print("  cu layer", lid, b.GetLayerName(lid))

pcbnew.SaveBoard(PCB, b)
print("saved 4-layer board")

ok = pcbnew.ExportSpecctraDSN(b, DSN)
print("DSN export:", ok, "->", DSN)
