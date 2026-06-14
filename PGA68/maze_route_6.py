#!/usr/bin/env python3
"""Maze-route the 6 nets FreeRouting left unconnected, through the fixed copper.

Approach: rasterize all existing copper (not on the target net) as per-layer
obstacle grids inflated by clearance, then 8-neighbour Dijkstra on F.Cu/B.Cu
with via transitions. Insert resulting tracks/vias, refill planes, save.
Run: /usr/bin/python3 maze_route_6.py
"""
import heapq
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
import pcbnew

PCB = "/home/delphic/win_share/Delphic/Make_68000_Great_Again/68k-nano/68000sbc.kicad_pcb"
G = 0.1                      # grid mm (fine, to keep quantization < clearance)
CLR = 0.25                  # clearance margin (design rule 0.1524, +margin)
TW = 0.254                  # my trace width
TH = TW / 2
VIA_D, VIA_DR = 0.6858, 0.3302
VIA_R = VIA_D / 2
VIA_PEN = 50                # via cost in cells (~5mm)
WIN = 30                    # per-net search window margin (mm)
F, B = 0, 2                 # pcb layer ids
LIDX = {F: 0, B: 1}         # grid layer index
EDGE_CLR = 0.3

b = pcbnew.LoadBoard(PCB)


def mm(v):
    return pcbnew.ToMM(v)


# --- board bbox / grid dims ---
bb = b.GetBoardEdgesBoundingBox()
ox, oy = mm(bb.GetLeft()) - 2, mm(bb.GetTop()) - 2
W = int((mm(bb.GetWidth()) + 4) / G) + 1
H = int((mm(bb.GetHeight()) + 4) / G) + 1
print(f"grid {W}x{H} @ {G}mm")


def gx(x):
    return (x - ox) / G


def gy(y):
    return (y - oy) / G


# the 6 nets and their two endpoints (from DRC). layer None => through-hole (both)
NETS = [
    ("/A22",    (53.49, 50.69, F),   (55.88, 106.68, None)),
    ("/~{RDU}", (129.54, 66.04, None), (132.08, 34.29, B)),
    ("/A5",     (111.76, 34.29, B),  (111.125, 63.5, F)),
    ("/A13",    (107.95, 95.25, F),  (109.855, 54.61, F)),
    ("/A1",     (133.985, 54.61, F), (129.54, 34.29, B)),
    ("/A4",     (114.3, 66.04, None), (116.84, 34.29, B)),
]


def build_obstacles(skip_net):
    """Returns (arrF, arrB, viablk): F/B trace-obstacle grids (inflated for a
    trace) and a via-placement-block grid (inflated for a via, union of both
    layers). skip_net: net code to exclude (the target)."""
    imgF = Image.new("1", (W, H), 0)
    imgB = Image.new("1", (W, H), 0)
    imgV = Image.new("1", (W, H), 0)       # via-block (both layers combined)
    dF, dB, dV = ImageDraw.Draw(imgF), ImageDraw.Draw(imgB), ImageDraw.Draw(imgV)

    def line(d, x1, y1, x2, y2, halfw):
        wpx = max(1, int(round(2 * halfw / G)))
        d.line([gx(x1), gy(y1), gx(x2), gy(y2)], fill=1, width=wpx)
        r = halfw / G
        for (cx, cy) in ((x1, y1), (x2, y2)):
            d.ellipse([gx(cx) - r, gy(cy) - r, gx(cx) + r, gy(cy) + r], fill=1)

    def disc(d, x, y, rad):
        r = rad / G
        d.ellipse([gx(x) - r, gy(y) - r, gx(x) + r, gy(y) + r], fill=1)

    for t in b.GetTracks():
        if t.GetNetCode() == skip_net:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetStart().x), mm(t.GetStart().y)
            oh = VIA_R
            disc(dF, x, y, oh + CLR + TH)
            disc(dB, x, y, oh + CLR + TH)
            disc(dV, x, y, oh + CLR + VIA_R)
        else:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            oh = mm(t.GetWidth()) / 2
            d = dF if t.GetLayer() == F else (dB if t.GetLayer() == B else None)
            if d:
                line(d, x1, y1, x2, y2, oh + CLR + TH)
            line(dV, x1, y1, x2, y2, oh + CLR + VIA_R)

    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == skip_net:
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            sz = p.GetSize()
            oh = max(mm(sz.x), mm(sz.y)) / 2
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            if th or p.IsOnLayer(F):
                disc(dF, x, y, oh + CLR + TH)
            if th or p.IsOnLayer(B):
                disc(dB, x, y, oh + CLR + TH)
            disc(dV, x, y, oh + CLR + VIA_R)

    arrF = np.array(imgF, dtype=bool)
    arrB = np.array(imgB, dtype=bool)
    viablk = np.array(imgV, dtype=bool)

    # board edge: block outside board outline (inset)
    mask = Image.new("1", (W, H), 1)
    dm = ImageDraw.Draw(mask)
    x0, y0 = mm(bb.GetLeft()) + EDGE_CLR, mm(bb.GetTop()) + EDGE_CLR
    x1, y1 = mm(bb.GetRight()) - EDGE_CLR, mm(bb.GetBottom()) - EDGE_CLR
    dm.rectangle([gx(x0), gy(y0), gx(x1), gy(y1)], fill=0)
    outside = np.array(mask, dtype=bool)
    arrF |= outside
    arrB |= outside
    viablk |= outside
    return arrF, arrB, viablk


def cell(x, y):
    return int(round(gx(x))), int(round(gy(y)))


def route(arrF, arrB, viablk, A, B_):
    """Dijkstra on (ix,iy,layer), 4-neighbour. Returns [(x_mm,y_mm,pcb_layer)]."""
    grids = [arrF, arrB]
    ax, ay, alyr = A
    bx, by, blyr = B_
    sx, sy = cell(ax, ay)
    gxx, gyy = cell(bx, by)
    starts = []
    for li, pl in ((0, F), (1, B)):
        if alyr is None or alyr == pl:
            if not grids[li][sy, sx]:
                starts.append((sx, sy, li))
    goalset = set()
    for li, pl in ((0, F), (1, B)):
        if blyr is None or blyr == pl:
            goalset.add((gxx, gyy, li))
    if not starts or not goalset:
        return None, "endpoint blocked"

    # search window around endpoints (speed)
    wx0 = max(0, min(sx, gxx) - int(WIN / G))
    wx1 = min(W - 1, max(sx, gxx) + int(WIN / G))
    wy0 = max(0, min(sy, gyy) - int(WIN / G))
    wy1 = min(H - 1, max(sy, gyy) + int(WIN / G))

    INF = 1e18
    dist = {}
    prev = {}
    pq = []
    for s in starts:
        dist[s] = 0
        heapq.heappush(pq, (0, s))
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1)]   # right-angle only
    found = None
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, INF):
            continue
        if u in goalset:
            found = u
            break
        ux, uy, ul = u
        g = grids[ul]
        for dx, dy in nb:
            nx, ny = ux + dx, uy + dy
            if wx0 <= nx <= wx1 and wy0 <= ny <= wy1 and not g[ny, nx]:
                v = (nx, ny, ul)
                nd = d + 1
                if nd < dist.get(v, INF):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        # via: switch layer at same cell, only if via fits here
        ol = 1 - ul
        if not grids[ol][uy, ux] and not viablk[uy, ux]:
            v = (ux, uy, ol)
            nd = d + VIA_PEN
            if nd < dist.get(v, INF):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if not found:
        return None, "no path"

    # backtrack
    path = []
    cur = found
    while cur is not None:
        cx, cy, cl = cur
        path.append((ox + cx * G, oy + cy * G, F if cl == 0 else B))
        cur = prev.get(cur)
    path.reverse()
    # snap exact endpoints
    path[0] = (ax, ay, path[0][2])
    path[-1] = (bx, by, path[-1][2])
    return path, "ok"


def simplify(path):
    """Collapse collinear same-layer runs; emit segments and vias."""
    segs, vias = [], []
    i = 0
    n = len(path)
    while i < n - 1:
        x1, y1, l1 = path[i]
        x2, y2, l2 = path[i + 1]
        if l1 != l2:               # via
            vias.append((x1, y1))
            i += 1
            continue
        # extend collinear run on same layer
        j = i + 1
        dx, dy = x2 - x1, y2 - y1
        while j + 1 < n and path[j + 1][2] == l1:
            x3, y3, _ = path[j + 1]
            cx, cy = x3 - path[j][0], y3 - path[j][1]
            if abs(dx * cy - dy * cx) < 1e-6:   # collinear
                j += 1
            else:
                break
        ex, ey, _ = path[j]
        if abs(ex - x1) > 1e-6 or abs(ey - y1) > 1e-6:
            segs.append((x1, y1, ex, ey, l1))
        i = j
    return segs, vias


def add_to_board(net, segs, vias):
    code = net.GetNetCode()
    for x1, y1, x2, y2, lyr in segs:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        t.SetWidth(pcbnew.FromMM(TW))
        t.SetLayer(lyr)
        t.SetNetCode(code)
        b.Add(t)
    for x, y in vias:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        v.SetWidth(pcbnew.FromMM(VIA_D))
        v.SetDrill(pcbnew.FromMM(VIA_DR))
        v.SetNetCode(code)
        b.Add(v)


done = []
for name, A, Bp in NETS:
    net = b.FindNet(name)
    if net is None:
        print(f"{name}: net not found"); continue
    arrF, arrB, viablk = build_obstacles(net.GetNetCode())
    path, status = route(arrF, arrB, viablk, A, Bp)
    if path is None:
        print(f"{name}: FAILED ({status})")
        continue
    segs, vias = simplify(path)
    add_to_board(net, segs, vias)
    print(f"{name}: routed, {len(segs)} segs, {len(vias)} vias")
    done.append(name)

print(f"\nrouted {len(done)}/6: {done}")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("saved")
