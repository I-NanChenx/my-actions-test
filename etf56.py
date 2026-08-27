import os
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))


def send_telegram(text):
    token = os.getenv("ETF56_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        print(f"❌ [0056] 找不到 ETF56_TOKEN({bool(token)}) 或 CHAT_ID({bool(chat_id)})")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("✅ [0056] 訊息發送成功！")
            return True
        print(f"❌ [0056] Telegram 發送失敗 ({res.status_code})：{res.text}")
        return False
    except Exception as e:
        print(f"❌ [0056] 發送 TG 失敗: {e}")
        return False


def send_56():
    print("--- [0056] 步驟 1: 正在從 Yahoo Finance 抓取資料 ---")
    stock = yf.Ticker("0056.TW")
    price = stock.fast_info.last_price

    if price is None:
        print("❌ [0056] 無法取得 0056 即時價格。")
        return

    msg = f"<b>📊 元大 0056 報告</b>\n當前價格：<b>{price:.2f}</b>"

    print("--- [0056] 步驟 2: 正在發送 Telegram 訊息 ---")
    send_telegram(msg)


if __name__ == "__main__":
    print(f"🚀 [0056] 啟動 0056 監控 - {datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M')} (台灣時間)")
    try:
        send_56()
    except Exception as e:
        print(f"❌ [0056] 發生異常錯誤：{e}")
