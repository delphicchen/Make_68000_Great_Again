#!/usr/bin/env python3
"""Add inner-layer power/ground pours after routing: GND on In1.Cu, VCC on
In2.Cu, covering the board outline (inset slightly). KiCad clears them around
other-net copper automatically. Run with /usr/bin/python3 add_pours.py
"""
import sys
import pcbnew

PCB = "/home/delphic/win_share/Delphic/Make_68000_Great_Again/68k-nano/68000sbc.kicad_pcb"
INSET_MM = 0.5

b = pcbnew.LoadBoard(PCB)

# layer ids by name
cu = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
print("copper layers:", cu)

def net_code(name):
    n = b.FindNet(name)
    if n is None:
        sys.exit(f"net {name} not found")
    return n.GetNetCode()

gnd, vcc = net_code("GND"), net_code("VCC")

# board outline bbox, inset
bb = b.GetBoardEdgesBoundingBox()
x0 = pcbnew.ToMM(bb.GetLeft()) + INSET_MM
y0 = pcbnew.ToMM(bb.GetTop()) + INSET_MM
x1 = pcbnew.ToMM(bb.GetRight()) - INSET_MM
y1 = pcbnew.ToMM(bb.GetBottom()) - INSET_MM
corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
print("pour rect mm:", [(round(a, 2), round(c, 2)) for a, c in corners])

def add_pour(layer_name, code, label):
    z = pcbnew.ZONE(b)
    z.SetLayer(cu[layer_name])
    z.SetNetCode(code)
    z.SetLocalClearance(pcbnew.FromMM(0.25))
    z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    poly = z.Outline()
    poly.NewOutline()
    for x, y in corners:
        poly.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    b.Add(z)
    print(f"added {label} pour on {layer_name}")
    return z

add_pour("In1.Cu", gnd, "GND")
add_pour("In2.Cu", vcc, "VCC")

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
print("filled all zones:", b.GetAreaCount(), "zones total")

pcbnew.SaveBoard(PCB, b)
print("saved board with inner power pours")
