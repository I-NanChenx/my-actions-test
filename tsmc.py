import os
import requests
import yfinance as yf
from datetime import datetime

def send_telegram(message):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload).raise_for_status()
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

if __name__ == "__main__":
    # 獲取台積電 (2330) 資訊
    stock = yf.Ticker("2330.TW")
    price = stock.fast_info.last_price
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"<b>📊 台積電 (2330) 自動回報</b>\n時間：{now}\n當前股價：<b>{price:.2f} TWD</b>"
    
    send_telegram(msg)
    print(f"已發送訊息，股價：{price}")
