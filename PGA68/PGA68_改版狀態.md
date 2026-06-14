# 68k-nano PGA-68 改版狀態（2026-06-12）

## 已完成

| 項目 | 內容 |
|------|------|
| Footprint | `PadRows.pretty/MC68HC000_PGA68.kicad_mod`（pad 號 = DIP-64 pin 號，直接相容原符號）|
| 腳位對照 | `pin_mapping_DIP64_to_PGA68.md`（含底視圖示意圖）|
| 原理圖 | U3 → `PadRows:MC68HC000_PGA68`，value → `MC68HC000RC10` |
| PCB U3 | DIP-64 換成 PGA-68，中心 **(63.5, 45.72)**（右移一格避開左上固定孔）|
| X1/X2 振盪器 | 原位置撞 PGA 左下角 → 移到 **(72.39, 76.2)**，靠近 CLK pad E1 |
| J5/J6 匯流排 pad 排 | 左端撞 PGA 右側 → 移到新頂邊條帶 **(pads x 78.74–139.7, y 34.29)** |
| 舊走線清除 | 194 segments + 43 vias（PGA 區、舊振盪器區、舊 DIP 區 U3 網路）|
| 板邊 | 頂邊上移 6.445mm（y 38.735 → 32.29），GND 鋪銅輪廓同步擴展 |
| 舊 zone 填充 | 已清除 16 塊 stale `filled_polygon`（會讓 KiCad 9 DRC 卡死；開檔後按 B 重算）|

## DRC 驗證結果（kicad-cli 9.0.2）

- **短路：0**、銅箔/邊緣衝突：無新增
- 未連接項目：171（= 待佈線的 ratsnest，預期中）
- track/via_dangling 111：清走線留下的殘端，GUI 裡用
  「Edit → Cleanup Tracks & Vias → 刪除懸空走線」一鍵清掉
- 其餘（text_height、silk、lib_mismatch 等）為原板既有問題

## 重現方式

```bash
cd 68k-nano
cp 68000sbc.kicad_pcb.backup_original 68000sbc.kicad_pcb
python3 ../rebuild_pga_pcb.py
```

## 待完成（KiCad GUI）

1. 開 `68000sbc.pro`（KiCad 9 會提示格式升級，正常）
2. 按 **B** 重算鋪銅
3. Cleanup Tracks & Vias 清除懸空殘端
4. 依 ratsnest 佈線：58 個 PGA 信號 pad、X1/X2、J5/J6 左段
   （VCC/GND 多數會被 GND pour / 電源走線吃掉）
5. C2（振盪器去耦）建議移到新振盪器旁
6. DRC 全過 → 出 Gerber → 嘉立創
