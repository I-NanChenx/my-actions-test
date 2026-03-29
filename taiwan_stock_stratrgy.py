import os
import requests
import yfinance as yf
from datetime import datetime

# 共用的發送函數
def send_telegram(token, chat_id, message):
    if not token or not chat_id:
        print("跳過：遺失 Token 或 Chat ID")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def get_analysis(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="100d")
    current_price = df['Close'].iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    
    # 判斷買入點：低於季線就是綠燈
    if current_price < ma60:
        advice = "🟢 <b>低於季線，適合分批買進！</b>"
    else:
        advice = "🔴 <b>高於季線，建議不追高。</b>"
    return current_price, ma60, advice

if __name__ == "__main__":
    # 設定：標的、名稱、對應的 Token 環境變數
    configs = [
        {"symbol": "2330.TW", "name": "台積電", "token_key": "TSMC_TOKEN"},
        {"symbol": "00878.TW", "name": "國泰 00878", "token_key": "ETF878_TOKEN"},
        {"symbol": "0056.TW", "name": "元大 0056", "token_key": "ETF56_TOKEN"}
    ]
    
    # 從 Secret 抓取唯一的 Chat ID
    chat_id = os.getenv("MY_CHAT_ID")

    for item in configs:
        token = os.getenv(item['token_key'])
        try:
            price, m60, advice = get_analysis(item['symbol'])
            now = datetime.now().strftime("%H:%M")
            
            msg = (f"<b>📊 {item['name']} 報告</b>\n"
                   f"時間：{now}\n"
                   f"當前價：{price:.2f}\n"
                   f"季線位：{m60:.2f}\n"
                   f"────────────────\n"
                   f"建議：{advice}")
            
            send_telegram(token, chat_id, msg)
            print(f"{item['name']} 已發送")
        except Exception as e:
            print(f"{item['name']} 失敗: {e}")
