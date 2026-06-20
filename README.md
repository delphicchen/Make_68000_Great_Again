# 68k nano — PGA-68 / 4-layer edition

A hardware fork of **[68k nano](https://github.com/74hc595/68k-nano)**, Matt
Sarnoff's minimal single-board Motorola 68000 computer, **adapted to use a
PGA-68 packaged CPU (MC68HC000RC) instead of the original DIP-64**, and
re-laid-out on a **4-layer** board.

The electrical design — the memory map, glue logic, RAM/ROM/UART, the ROM
firmware, and all software — is Matt Sarnoff's original work, used here under the
BSD-3-Clause license (see below). **This fork only changes the CPU package and the
physical board layout; the schematic netlist is unchanged.**

> ⚠️ This is an unofficial derivative and is **not affiliated with, nor endorsed
> by, the original author.**

---

## What this fork changes

- **CPU package: DIP-64 → PGA-68.** New footprint `PadRows:MC68HC000_PGA68` whose
  **pad numbers equal the DIP-64 pin numbers**, so the existing `CPU_NXP_68000`
  schematic symbol and the entire netlist are reused unchanged.
- **4-layer stackup.** A PGA's inner pins cannot "escape" on two layers, so the
  board is now: `F.Cu` / `B.Cu` signal, **`In1.Cu` = GND plane, `In2.Cu` = VCC
  plane**.
- **Re-laid-out and re-routed.** Main components repositioned to clear the PGA;
  the board is fully auto-routed from the command line (FreeRouting headless) with
  a small custom maze router closing any nets FreeRouting leaves. Result:
  **0 unconnected, 0 copper/clearance DRC violations.**
- **Verified pin-by-pin.** Every pad was checked two ways — (1) it carries the
  same net as the original DIP board, and (2) its physical grid location matches
  the Motorola M68000 datasheet PGA pinout (Fig 11-2). See `PGA68/verify_pins.py`.

## This fork's additions — see [`PGA68/`](PGA68/)

> The notes in `PGA68/` are written in 中文 (Traditional Chinese).

| File | What it is |
|------|------------|
| `pin_mapping_DIP64_to_PGA68.md` | DIP-64 ↔ PGA-68 pin map + datasheet bottom-view chart |
| `verify_pins.py` | Pin-by-pin verification (netlist + datasheet placement) |
| `4層佈線完成報告.md` | Routing completion report (layers, DRC, file list) |
| `convert_4layer.py`, `import_ses_4l.py`, `add_pours.py`, `maze_route_6.py`, `rebuild_pga_pcb.py` | The conversion / routing scripts |
| `顯示器擴充指南.md` | Adding a display (ESP32/FabGL serial terminal, or a bus video card) |
| `設計隨筆.md` | Design notes (compute-power irony, "smart peripheral" philosophy) |

Board files:

- **`68000sbc.kicad_pcb`** — the board, opens by default with the
  `68000sbc.kicad_pro` project. 4-layer layout with components re-placed and the
  board fully re-routed; DRC-clean (0 unconnected, 0 copper/clearance violations).
- `68000sbc_v1.kicad_pcb` — the earlier layout, kept for reference (open directly
  in the PCB editor).
- `68000sbc.sch` (schematic, shared), and the footprint
  `PadRows.pretty/MC68HC000_PGA68.kicad_mod`.

A reusable, board-agnostic version of the headless routing workflow also exists as
a Claude Code skill (`kicad-autoroute`); it is not part of this repo.

---

## The original design & full documentation

**Everything about how the computer actually works** — features, the memory map,
the bill of materials, how to build it, and the ROM firmware (boot process,
interactive command shell, serial loader, debugger, system-call API) — is from the
original project and is preserved unchanged here as
**[`README.original.md`](README.original.md)** (and `API.md`, `bom.txt`, `code/`).

- **Original project:** *68k nano* by **Matt Sarnoff** — <https://github.com/74hc595/68k-nano>
- <https://msarnoff.org> · [@txsector](https://twitter.com/txsector)

If you want to actually build and run this, **read `README.original.md` first** —
the part counts, firmware, and usage are all there. This PGA-68 board needs the
same BOM, just with a PGA-socketed `MC68HC000RC` in place of the DIP-64 CPU. A full
English purchasing list for *this* board — generated from the actual footprints,
with sockets, the 4-layer PCB spec, and build notes — is in **[`BOM.md`](BOM.md)**.

## License

BSD 3-Clause License — Copyright (c) 2020 Matt Sarnoff. See [`LICENSE`](LICENSE).

The PGA-68 conversion work added in this fork (the footprint, the `PGA68/` scripts
and notes, and the board re-layout) is contributed under the same BSD-3-Clause
terms.
