# Bill of Materials — 68k nano (PGA-68 / 4-layer edition)

Generated from the actual footprints in the current board **`68000sbc.kicad_pcb`**
(the re-placed, re-routed v2 layout). Board: **4-layer, 127.0 × 97.25 mm**, all
parts **through-hole (THT)** — hand-solderable.

> This BOM supplements the original `bom.txt` / `README.original.md`. The
> **electrical design is unchanged** from Matt Sarnoff's *68k nano*; only the CPU
> package (DIP-64 → PGA-68) and the board layout differ. For *how the computer
> works and how to build it*, read **`README.original.md`** first.

Legend — **Qty** = number on the board · **SKU** = reference part numbers from the
original BOM (Jameco / Mouser), where available.

---

## A. Active devices (ICs)

| Ref | Part | Package | Qty | SKU | Notes |
|-----|------|---------|:---:|-----|-------|
| **U3** | **MC68HC000RC10** CPU | **PGA-68** | 1 | — | **You supply this** — it is the whole reason for the fork |
| U1 | 74HC139 dual 2-to-4 decoder | DIP-16 | 1 | | Address decode |
| U2 | 74HC14 hex inverting Schmitt trigger | DIP-14 | 1 | | Reset / signal conditioning |
| U4, U6 | AS6C4008-55PCN SRAM 512K×8 | DIP-32 (600 mil) | 2 | Jameco 242448 / Mouser 913-AS6C4008-55PCN | 1 MB total |
| U5, U7 | AT28C256 EEPROM 32K×8 | DIP-28 (600 mil) | 2 | Jameco 74843 / Mouser 556-AT28C25615PU | Firmware ROM |
| U8 | TL16C550(C) UART | DIP-40 (600 mil) | 1 | Jameco 288809 | Serial port |

## B. Oscillator (populate ONE)

| Ref | Part | Package | Qty | Notes |
|-----|------|---------|:---:|-------|
| X1 **or** X2 | Full-can crystal oscillator | DIP-14 (X1) **or** DIP-8 (X2) | **1** | X1 and X2 are **two alternative footprints for the same clock** (same CPUCLK net) — fit only one |

> ⚠️ **Frequency:** the schematic marks **12 MHz**, but U3 is an **RC10 (rated
> 10 MHz)**. 12 MHz is ~20 % overclock. To stay in spec, buy an **8 MHz or 10 MHz**
> oscillator. 12 MHz often works on HCMOS parts but is not guaranteed.

## C. Passives

| Ref | Part | Package / rating | Qty | Notes |
|-----|------|------------------|:---:|-------|
| C1–C10 | 0.1 µF ceramic | THT, 5.0 mm pitch | 10 | Per-IC decoupling |
| C11, C12 | 10 µF electrolytic, ≥16 V | radial D5.0 mm, 2.5 mm pitch | 2 | Power filtering |
| R1, R2 | 10 kΩ, 1/4 W | axial DIN0204 | 2 | Pull-ups |
| R3 | 1 kΩ, 1/4 W | axial DIN0204 | 1 | |
| R4–R7 | LED series resistor 330 Ω–1 kΩ | axial DIN0204 | 4 | Value per LED colour/brightness |
| RN1 | 10 kΩ bussed resistor network | **SIP-7** (common pin) | 1 | Bus pull-ups |

## D. Diodes / LEDs

| Ref | Part | Package | Qty | Notes |
|-----|------|---------|:---:|-------|
| D1, D2 | 1N5817 Schottky (1N4148 also works) | DO-41 / DO-35, 7.62 mm pitch | 2 | Power OR-ing |
| D3 | LED "POWER" | 5 mm | 1 | Power indicator |
| D4 | LED (activity) | 5 mm | 1 | |
| D5 | LED "CARD" | 5 mm | 1 | |
| D6 | LED "HALT" | 5 mm | 1 | |

## E. Connectors / switches / mechanical

| Ref | Part | Spec | Qty | Notes |
|-----|------|------|:---:|-------|
| J1 | USB-B PCB socket (horizontal) | USB-B 1HSxx Horizontal | 1 | Jameco 2096245 |
| J2 | 1×6 right-angle header | 2.54 mm | 1 | FTDI serial |
| J3 | 1×7 header | 2.54 mm vertical | 1 | RTC (SparkFun BOB-10160) — optional |
| J4 | 2×22 header | **2.00 mm** vertical | 1 | CF / IDE interface |
| J5, J6 | 1×25 expansion pad rows | 2.54 mm (PCB pads) | 0–2 | EXPANSION — fit headers only if used |
| JP1 | 1×3 header + jumper | 2.54 mm vertical | 1 | Power select |
| SW1, SW2 | 6 mm tactile switch | THT | 2 | RESET / BTN1 |
| H1–H4 | M2.5 screw + standoff/spacer | 2.7 mm hole | 4 sets | Mounting holes |

## F. IC sockets (recommended — footprints are the "Socket" variants)

| For | Socket | Qty |
|-----|--------|:---:|
| U1 | DIP-16 | 1 |
| U2 | DIP-14 | 1 |
| U4, U6 | DIP-32 (600 mil / wide) | 2 |
| U5, U7 | DIP-28 (600 mil / wide) | 2 |
| U8 | DIP-40 (600 mil / wide) | 1 |
| X1/X2 | DIP-14 or DIP-8 (optional — oscillator can be soldered) | 1 |
| **U3** | **PGA-68 socket** (specialty part, optional — solder directly if unavailable) | 1 |

> For U5/U7 (EEPROM), if you reflash often, use a **ZIF-28 socket** (Jameco 102745
> / Aries 28-526-10). A PGA-68 socket for U3 is a specialty item; soldering the CPU
> directly avoids it.

## G. The PCB itself

| Item | Spec |
|------|------|
| Layers | **4** — F.Cu signal / In1.Cu GND plane / In2.Cu VCC plane / B.Cu signal |
| Size | 127.0 × 97.25 mm |
| Trace / via | 0.254 mm trace; 0.69 / 0.33 mm via (both standard-process at JLCPCB) |
| Order | Export Gerbers + drill → fab as a **4-layer** board |

## H. Buying checklist

1. **U3 you supply** (MC68HC000RC10, PGA-68) — prerequisite of this fork.
2. **Buy only one oscillator**, and prefer **≤10 MHz** to keep the RC10 in spec
   (the design currently marks 12 MHz, which is overclocking).
3. **Sockets:** all seven DIP ICs use socket-variant footprints — buy the sockets
   too. The U3 PGA-68 socket is optional.
4. **J4 is 2.00 mm pitch** (everything else is 2.54 mm) — don't buy the wrong header.
5. **Optional:** J3 (RTC), J5/J6 (expansion headers), and a CF↔IDE adapter, as needed.
6. Peripherals mentioned by the original BOM: SparkFun DeadOn RTC BOB-10160;
   CompactFlash → 2.5" 44-pin IDE adapter.

---

## Layout verification (why this board is correct)

The DIP-64 → PGA-68 conversion was verified end-to-end:

- **Netlist identical to the original DIP board** — the PGA footprint's pad numbers
  equal the DIP-64 pin numbers, so the schematic and every net are reused unchanged.
- **Physical pin placement matches the datasheet** — all 68 pads were checked
  against the Motorola/Freescale *M68000 User's Manual* Fig 11-2 (68-lead PGA,
  bottom view); the 10×10 grid and the four NC pads (A1, J4, K1, K10) match
  exactly, with the correct bottom-view→top-view mirror. See `PGA68/verify_pins.py`
  and `PGA68/pin_mapping_DIP64_to_PGA68.md`.
- **DRC (KiCad 9):** 0 unconnected pads, 0 shorts, 0 clearance violations, 0
  footprint errors. The remaining 14 violations are non-electrical and do not block
  fabrication — courtyard overlaps (decoupling caps/resistors hugging their ICs)
  and a solder-mask web between adjacent different-net pads on connector J1.

---
*Generated 2026-06-20 from the v2 PCB (49 footprints) and `bom.txt`.*
