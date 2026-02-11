# admission-result-crawler

A Python web crawler that monitors graduate school admission announcements and sends real-time notifications via Telegram.

## 功能特點 (Features)

- 🔍 自動爬取指定網站的榜單資訊 (Automatically crawls designated websites for admission lists)
- ⏰ 使用 GitHub Actions 每 20 分鐘自動檢查 (Uses GitHub Actions to check every 20 minutes)
- 📱 透過 Telegram 即時通知 (Real-time notifications via Telegram)
- 🎯 支援多個網址同時監控 (Supports monitoring multiple URLs simultaneously)
- 🔧 彈性關鍵字配置 (Flexible keyword configuration)

## 設定步驟 (Setup Instructions)

### 1. 設定 Telegram Bot

1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 發送 `/newbot` 並跟隨指示建立新 bot
3. 取得你的 bot token (格式: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. 找到 [@userinfobot](https://t.me/userinfobot) 取得你的 Chat ID

### 2. 設定 GitHub Secrets

在你的 GitHub repository 中設定以下 secrets:

1. 前往 `Settings` > `Secrets and variables` > `Actions`
2. 新增以下 secrets:
   - `TELEGRAM_BOT_TOKEN`: 你的 Telegram bot token
   - `TELEGRAM_CHAT_ID`: 你的 Telegram chat ID

### 3. 配置監控網址

編輯 `config.json` 檔案，加入你要監控的網址:

```json
{
  "urls": [
    "https://example.com/admissions",
    "https://school.edu.tw/admission-results"
  ],
  "keywords": [
    "榜單",
    "放榜",
    "admission",
    "result",
    "錄取",
    "名單"
  ],
  "check_interval": 1200
}
```

### 4. 啟用 GitHub Actions

將程式碼推送到 `main` 分支後，GitHub Actions 會自動啟動，每 20 分鐘檢查一次。

你也可以在 `Actions` 標籤頁手動觸發執行。

## 本地測試 (Local Testing)

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# 執行爬蟲
python crawler.py
```

## 排程說明 (Schedule Details)

- 排程: 每 20 分鐘執行一次
- Cron 表達式: `*/20 * * * *`
- 也可以手動在 GitHub Actions 介面觸發執行

## 檔案結構 (File Structure)

```
admission-result-crawler/
├── crawler.py              # 主要爬蟲程式
├── config.json             # 配置檔案
├── requirements.txt        # Python 依賴套件
├── .github/
│   └── workflows/
│       └── check-results.yml  # GitHub Actions 工作流程
└── README.md              # 說明文件
```

## 注意事項 (Notes)

- GitHub Actions 的免費方案有使用限制，請注意使用量
- 確保監控的網站允許爬蟲訪問
- 建議設定合理的檢查頻率，避免對目標網站造成負擔
- 關鍵字搜尋不區分大小寫 (Case-insensitive keyword matching)

## 授權 (License)

MIT License
