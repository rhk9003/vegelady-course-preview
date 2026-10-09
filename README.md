# 羽試國考培育學院・免費先修班銷售頁預覽

單一版本：D&J 依定位與考生需求重寫的文案（文案正本在 D&J 客戶資料夾 `個人客戶/羽試培育工作室/03_文案素材/銷售頁/羽試_先修班銷售頁_文案.md`）。網址：https://rhk9003.github.io/vegelady-course-preview/ （舊的 `version-b/` 會自動轉到這裡）。

照片、Logo 與部分原文來自 https://go.vegelady.com/ 、https://vegelady.com/ ，於 2026-10-09 讀取。素材權利屬原權利人，本儲存庫僅作版型提案預覽。版型沿用 `rhk9003/vstory-course-preview` 的結構，配色改為羽試原站的磚紅色系（#a66440）與 Noto Serif TC。

沒有新增課綱、開課日期或成果保證；標「待確認」的地方等客戶回覆（贈品條件、場次、學員類科、申論批改原圖）。報名按鈕連到目前的報名表。本預覽沒有分析追蹤或後端。頁面有 noindex 標記；這是公開預覽，noindex 不代表存取保護。

## 文字修改層

開啟 `?edit=1` 直接進入修改模式，或按右下角「提出文字修改」。可框選同一段落中的部分文字，也可點選整段，再填入改稿與補充說明。原文保留，高亮標記與修改清單並存。

- 草稿用 localStorage 存在這台裝置的瀏覽器，沒有自動傳送或雲端同步。
- 「下載修改單」產生可閱讀的 HTML；「複製給 Dennis」產生純文字。使用者需自行傳送。
- 「下載備份／匯入備份」用 JSON；匯入會驗證原文位置與版本，保留既有草稿，衝突時整份拒絕，不部分覆蓋。
- 版本號寫在 `_build/build.py` 的 `PAGES`（目前 `yushi-lp-2026-10-09`）。改了頁面文字要同步提高版本號，舊草稿會因原文不符被拒絕匯入，不會套錯位置。
- `review-core.js` 是無 DOM 的驗證與匯出邏輯；`review.js` 是頁面互動，從 `<body>` 的 `data-review-page`／`data-review-revision`／`data-review-title` 讀設定；`review.css` 是獨立樣式。
- 本機測試：`node --test review-core.test.cjs`。

## 改頁面

頁面原始檔在 `_src/index.html`：區塊用 `data-sec="區塊名稱"`，可修改的文字用 `data-c`（不可巢狀）。改完執行：

```
python3 _build/build.py
```

會重新產生根目錄 `index.html`，並自動編上 `data-copy-id`。共用的 `<head>`、預覽列與頁尾在 `build.py` 裡。
