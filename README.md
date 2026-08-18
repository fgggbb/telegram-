# Telegram FloodWait Keep-Alive

透過循環呼叫 Telegram MTProto `send_code_request` 接口，在 `FLOOD_WAIT` 限制自動解除前再次觸發，實現限制狀態的持續累積。

## 專案結構

```
├── main.py          # 主腳本
├── requirements.txt # 依賴套件
└── railway.json     # Railway 部署配置
```

## 環境變數

| 變數 | 說明 | 必填 |
|------|------|------|
| `API_ID` | 來自 [my.telegram.org](https://my.telegram.org) 的 API ID（純數字） | 是 |
| `API_HASH` | 來自 my.telegram.org 的 API Hash | 是 |
| `TARGET_PHONE` | 目標手機號，國際格式（如 `+989146006014`） | 是 |
| `INTERVAL_HOURS` | 觸發間隔（小時），預設 `20` | 否 |

## 本地運行

```bash
pip install -r requirements.txt
$env:API_ID="34680582"
$env:API_HASH="3c1ec8bffb7548302bf57fba50211cb8"
$env:TARGET_PHONE="+989146006014"
python main.py
```

## Railway 部署

1. 將本倉庫連接至 Railway（Deploy from GitHub）
2. 在 **Variables** 頁填入上述環境變數
3. Railway 自動構建並後台常駐運行
4. 於 **Logs** 觀察輸出

## 運作機制

- 每次運行以 `:memory:` session 呼叫 `send_code_request`，不接收也不驗證短信碼
- 成功：記錄日誌，等待 `INTERVAL_HOURS` 後再次觸發
- 觸發 `FloodWait`：讀取剩餘秒數，在限制解除前 1 小時再次觸發
- 其他錯誤：等待 1 小時後重試

## 風險提示

1. **永久封號**：限制時間隨觸發次數指數增長，最終可能導致 Telegram 永久封禁該手機號，屆時無法登入。
2. **IP 段限制**：同一出口 IP 頻繁請求可能導致該 IP 被 Telegram 暫時限制，影響該 IP 下其他帳號。
3. **主裝置需保持線上**：若主裝置（手機／桌面）長期離線，已登入 session 可能過期，屆時無法通過掃碼恢復。

## 前置條件

- 目標帳號已開啟 2FA（兩步驟驗證）並綁定 Email
- 主裝置 Telegram 客戶端保持線上
