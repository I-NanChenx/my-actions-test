import os, requests, yfinance as yf
from datetime import datetime

def send_telegram(text):
    token = os.getenv("TSMC_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def check_strategy():
    stock = yf.Ticker("2330.TW")
    hist = stock.history(period="150d")
    if hist.empty: return

    current_price = round(hist['Close'].iloc[-1], 2)
    ma20 = round(hist['Close'].rolling(window=20).mean().iloc[-1], 2)
    ma60 = round(hist['Close'].rolling(window=60).mean().iloc[-1], 2)
    ma120 = round(hist['Close'].rolling(window=120).mean().iloc[-1], 2)

    diff_ma120 = round(((current_price - ma120) / ma120) * 100, 2)
    
    trigger_msg = ""
    if current_price <= ma120:
        trigger_msg = "🚨 <b>【資金池 C 觸發】台積電跌破半年線！</b>\n請準備動用黑天鵝戰備金，進行危機入市！"
    elif current_price <= ma60:
        trigger_msg = "⚠️ <b>【資金池 B 觸發】台積電跌破季線！</b>\n這是一個勝率極高的波段加碼點，請準備零股承接。"
    elif current_price <= ma20:
        trigger_msg = "🔔 <b>【資金池 B 觸發】台積電回測月線！</b>\n短期回檔，可視情況啟動第一筆零股低接。"

    if trigger_msg:
        final_message = (f"{trigger_msg}\n\n"
                         f"📊 <b>即時數據摘要</b>\n"
                         f"• 最新股價：<b>{current_price}</b> 元\n"
                         f"• 半年線 (120MA)：{ma120} 元 (乖離 {diff_ma120}%)")
        send_telegram(final_message)

if __name__ == "__main__":
    check_strategy()
