
import os, requests, yfinance as yf

def send_878():
    token = os.getenv("ETF878_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    stock = yf.Ticker("00878.TW")
    price = stock.fast_info.last_price
    
    # 你持有 80 張 (80,000 股)
    total_value = price * 80000
    
    msg = f"<b>📊 國泰 00878</b>\n當前價格：{price:.2f}\n持股市值：${total_value:,.0f}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    send_878()
