# 原始碼來源與授權狀態

[English](PROVENANCE.md) | 繁體中文（台灣）

這個獨立 repo 於 2026-11-10 從本機開發的資源格式工具中選取程式邏輯並整理而成。
它使用全新的 Git 歷史，執行時不依賴原先用於研究格式的工作目錄。

| 模組 | 所選取程式邏輯的來源 |
| --- | --- |
| `resource_tools/text_banks.py` | 偏移量表讀取與重建取自 `catalog_localization.py`；固定配置空間的更新檢查改寫自 `build_localization_poc.py`。 |
| `resource_tools/images.py` | 影格索引、解碼與編碼取自 `ending_cards.py`。 |
| `resource_tools/archives.py` | Wyle 串流編解碼取自 `opening_cards.py`；目錄與未壓縮項目的處理參考 `build_hdd.py`。 |
| `resource_tools/bitmap.py` | 新增的標準函式庫 BMP 交換實作，使用自製索引色盤。 |
| `resource_tool.py`、範例與測試 | 新增的獨立 CLI、自製測試資料與驗證。 |

本 repo 僅選取上表所列的資源格式邏輯，沒有整份複製原始工具檔案。
主機操作、解密、執行檔 patch、特定遊戲翻譯資料、字形資料及來源版本雜湊常數
均未納入。實作參考的研究 commit 為 `e9fb138`；該私人 repo 的歷史未包含在
這個 repo 內。

範例標籤與像素測試資料都是新製作的示範內容。格式標記數值、編解碼常數與
控制符號語法用於描述支援的格式，並非隨附的原版資源。

## 授權

擁有者於 2026-11-10 決定，自製工具原始碼、文件與自製範例採用
[MIT 授權](LICENSE)。此授權不會賦予第三方軟體、遊戲內容、翻譯文或字型的
使用權利。

本 repo 未隨附任何完整的第三方相依套件，實作僅使用 Python 標準函式庫。
這份來源清單並非獨立法律意見，也不是證明作者身分的鑑識證據。
