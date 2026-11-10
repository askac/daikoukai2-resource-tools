# 大航海時代 II 資源工具

[English](README.md) | 繁體中文（台灣）

這是一套用於檢視與重建《大航海時代 II》（Uncharted Waters II / Daikoukai
Jidai II）內部資源檔案的小型工具，並附上原始套件架構與文字呈現的觀察筆記。
本工具集專注於內部資源編修；完整中文化安裝器不在其範圍內。

若要處理原版遊戲，請自行從
[Steam 官方商店頁面](https://store.steampowered.com/app/628170/)購買合法副本。
工具的輸入是另外準備好的**遊戲內部資源檔案**，不接受下載取得的 Windows
套件作為輸入。如何準備這些資源檔案，不在本專案的操作流程內。

本 repo 包含 Python 原始碼、自製範例產生器與說明文件，不包含遊戲資料、翻譯文、
字型、模擬器執行檔、磁碟映像、執行檔 patch、套件解包程式或資源解密程式。
本機提取出的檔案可能包含受著作權保護的內容；匯出操作不會使其成為本 repo
可散布的原始碼，也不會賦予重新散布的權利。

## 環境需求

Python 3.10 以上，僅使用標準函式庫。執行自製範例不需要安裝額外套件、遊戲或
模擬器，也不需要網路連線。Windows 可將下列指令中的 `python` 改成 `py -3`。

## 自製範例

請在 repo 目錄內執行。每次指定的輸出路徑都必須尚未存在。

```sh
python examples/make_demo.py work/demo
python resource_tool.py text-export work/demo/MESSAGE.DAT --width 2 --kind message -o work/text.json
```

以支援 UTF-8 的編輯器開啟 `work/text.json`，將第一筆記錄 `texts` 內的
`DEMO ONE` 改為 `EDITED`，保留索引、schema、版面配置資訊與來源摘要值。
接著重建為另一個檔案：

```sh
python resource_tool.py text-import work/demo/MESSAGE.DAT work/text.json -o work/message-edited.dat
```

若要提取索引色圖片並匯入編修結果：

```sh
python resource_tool.py image-export work/demo/GRAPHICS.BIN 0 -o work/frame.bmp
python resource_tool.py image-import work/demo/GRAPHICS.BIN 0 work/frame.bmp -o work/graphics-edited.bin
```

BMP 使用自製灰階色盤顯示**色彩索引**，並非遊戲實際顯示的顏色。編修時須保留
8 位元索引色格式、尺寸、色盤與索引順序。工具會拒絕轉成 RGB、色盤最佳化或其他
不支援的 BMP 格式。匯入時會保留原有影格空間，因此即使圖片外觀正常，若壓縮後
無法放入原本配置的空間，仍會拒絕更新。

內部封存檔可依從 0 開始的項目索引檢視與更新：

```sh
python resource_tool.py archive-list work/demo/GRAPHICS.LZW
python resource_tool.py archive-extract work/demo/GRAPHICS.LZW 0 -o work/extracted.bin
python resource_tool.py archive-replace work/demo/GRAPHICS.LZW 0 work/graphics-edited.bin -o work/archive-edited.lzw
```

範例會產生自製 ASCII 標籤與空白幾何像素資料，不會重建或下載原版遊戲素材。

## 支援範圍

| 輸入 | 可執行操作 | 限制 |
| --- | --- | --- |
| 以偏移量索引的文字資料檔 | 匯出可編輯的 UTF-8 JSON；匯入 CP932 文字 | 保留記錄偏移量、字串數量、控制符號與容量限制。 |
| 索引色影格集合 | 將單一影格匯出為 BMP；匯入單一編修影格 | 保留尺寸、影格配置空間與其他影格的所有位元組。 |
| LW11 / LS10 / LS11 資源封存檔 | 列出、提取與替換項目 | 保留偏移量、檔案總長與項目解壓後長度；壓縮後資料須放得進原配置空間。 |

已知的文字配置包括 `MENU.DAT`（`--width 2 --kind menu`）、
`MESSAGE.DAT`（`--width 2 --kind message`）與
`SNR*.MES`（`--width 4 --kind scenario`）。這些參數用來選擇資料配置，
不表示所有同名檔案都相容；工具會在更新前驗證實際結構。

文字匯入目前僅支援資源既有的 CP932 編碼，不會安裝新的繁體中文字形、產生字型，
或加入自訂字碼對應。能成功編碼的字元，也不代表特定遊戲字型一定能顯示。
執行檔內字串、固定名稱表、遊玩存檔與執行時掛鉤，都不在這個初版工具集的範圍內。

## 輸出行為與驗證

所有指令都會先驗證輸入並在記憶體中完成結果，再開啟輸出檔。既有檔案不會被覆寫，
包括輸入檔本身。寫入後會完成 flush 並讀回比對；若寫入失敗，會回報錯誤並移除
這次新建但未完成的輸出。請保留原始輸入檔，以便回復。

文字 JSON 的摘要值用來偵測匯入時使用的來源是否與匯出時不同，並非版本白名單。
能否處理資源，取決於格式解析、邊界、數量與重建檢查。本工具沒有另外的執行時
安裝器或模擬器整合。

```sh
python -B -m unittest discover -s tests -v
```

測試涵蓋自製資料、未修改資料的重建、指定範圍的編修、無效配置、容量不足、
控制符號變動、來源不一致、跨目錄使用 CLI，以及保留既有輸出。
這些測試不等同於遊戲內、模擬器或搖桿功能驗證。

## 文件與權利說明

- [套件架構觀察](docs/architecture.zh-TW.md)
- [資源格式與更新方式](docs/formats.zh-TW.md)
- [字型視覺觀察](docs/typography.zh-TW.md)
- [原始碼來源與授權狀態](PROVENANCE.zh-TW.md)
- [Agent 協作規範](AGENT.zh-TW.md)

自製工具原始碼、文件與自製範例採用 [MIT 授權](LICENSE)。此授權不會賦予第三方
遊戲內容、翻譯文、字型或模擬器軟體的使用權利。本專案與遊戲發行商沒有隸屬關係，
也未獲其背書；文件中的名稱僅用於辨識工具與觀察所針對的對象。
