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

def analyze_tsmc():
    stock = yf.Ticker("2330.TW")
    # 抓取過去 100 天的資料來計算均線
    df = stock.history(period="100d")
    
    current_price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    
    # 簡單的買入邏輯判斷
    status = "🔍 觀望中"
    if current_price < ma60:
        status = "🟢 <b>低於季線 (MA60)，適合分批佈局！</b>"
    elif current_price < ma20:
        status = "🟡 <b>跌破月線 (MA20)，可以開始留意。</b>"
    else:
        status = "🔴 <b>高於均線，建議不追高。</b>"
        
    return current_price, ma20, ma60, status

if __name__ == "__main__":
    try:
        price, m20, m60, advice = analyze_tsmc()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        msg = (f"<b>📊 TSMC (2330) 投資參考</b>\n"
               f"時間：{now}\n"
               f"────────────────\n"
               f"當前股價：<b>{price:.2f}</b>\n"
               f"月線 (MA20)：{m20:.2f}\n"
               f"季線 (MA60)：{m60:.2f}\n"
               f"────────────────\n"
               f"建議：{advice}")
        
        send_telegram(msg)
        print("分析報告已發送")
    except Exception as e:
        send_telegram(f"發生錯誤：{str(e)}")
