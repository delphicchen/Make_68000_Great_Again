# KiCad 專案重置與 FreeRouting 自動佈線指南

## 專案現況更新
專案目前已經透過 `git reset --hard` 和 `git clean -fd` 徹底重置為原始狀態。所有先前的修改（包含錯誤的佈線、懸空的走線與過孔）都已經被抹除。`68k-nano` 目錄現在處於最乾淨的初始狀態（即原本的 DIP-64 配置）。

> **備份提醒**：先前的 PGA-68 腳位對照表 (`pin_mapping_DIP64_to_PGA68.md`) 以及自訂的 PGA 封裝檔 (`PadRows.pretty`) 已經被安全地備份到上一層 `Make_68000_Great_Again` 目錄中。日後若要再次嘗試 DIP 轉 PGA，可以直接從該處取用。

---

## 如何安裝與使用 FreeRouting (Linux 環境)

由於這是一張 2 層板，且如果未來要將 68 根針腳的 PGA 封裝擠入極小的面積內，純手動佈線或是用腳本強制佈線都非常容易產生大量 DRC 錯誤（短路、走線交叉）。使用專業的拓撲自動佈線演算法是最佳解法。

以下提供兩種安裝與使用 FreeRouting 的方法（強烈推薦方法一）：

### 方法一：透過 KiCad 內建外掛管理器（最推薦 🌟）

這是最簡單、最不會出錯的方式，能無縫整合 KiCad 9 的匯出/匯入流程。

1. **開啟 KiCad 主程式**（KiCad Project Manager，不需要打開特定專案）。
2. 點擊首頁的 **「外掛程式與內容管理器 (Plugin and Content Manager)」**。
3. 在頂部的搜尋列中輸入 `Freerouting`。
4. 找到 **Freerouting** 外掛後，點擊 **[Install] (安裝)**。
5. 點擊視窗左下方的 **[Apply Pending Changes] (套用變更)** 完成安裝。
6. **如何使用**：
   - 開啟你的 PCB 編輯器 (`.kicad_pcb` 檔)。
   - 在上方工具列會出現一個新的 **Freerouting 圖示**。
   - 點擊該圖示，外掛會自動匯出電路板資料、開啟 FreeRouting 進行演算，完成後再一鍵將結果匯回 KiCad，省去所有繁瑣步驟。

### 方法二：手動下載獨立執行檔 (Standalone App)

如果你偏好將軟體獨立執行，或者外掛程式有相容性問題，可以採用此方法。

1. **安裝 Java 執行環境**：
   打開終端機，輸入以下指令確保系統有 Java：
   ```bash
   sudo apt update
   sudo apt install default-jre
   ```

2. **下載 FreeRouting 程式**：
   - 前往官方 GitHub Releases 頁面：[freerouting/freerouting](https://github.com/freerouting/freerouting/releases)
   - 下載最新版的 `freerouting-x.x.x.jar`（或是 `.deb` 安裝檔直接安裝）。

3. **啟動 FreeRouting**：
   如果你下載的是 `.jar` 檔，在終端機輸入：
   ```bash
   java -jar freerouting-x.x.x.jar
   ```

4. **手動匯出與匯入流程**：
   - **在 KiCad 中匯出**：在 PCB 編輯器中，選擇 `檔案 (File)` -> `匯出 (Export)` -> `Specctra DSN`，將目前的電路板狀態存成 `.dsn` 檔。
   - **在 FreeRouting 佈線**：打開 FreeRouting 程式，載入剛才的 `.dsn` 檔，點擊上方的自動佈線按鈕讓它跑完。
   - **儲存結果**：佈線完成後，在 FreeRouting 中選擇匯出為 `.ses` (Specctra Session) 檔。
   - **在 KiCad 中匯入**：回到 KiCad PCB 編輯器，選擇 `檔案 (File)` -> `匯入 (Import)` -> `Specctra Session`，讀入該 `.ses` 檔，佈線就會完美呈現在畫面上。

---

## 下一步建議

1. 先在目前乾淨的 **DIP-64 原始版本**上，試著用 FreeRouting 跑一次自動佈線，熟悉軟體的操作手感。
2. 熟悉後，再將備份的 PGA 封裝匯入，替換掉 DIP 封裝，並再次利用 FreeRouting 解決高密度的佈線挑戰。

祝你有個好夢！明天睡醒再繼續挑戰！