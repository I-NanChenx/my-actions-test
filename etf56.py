import os, requests, yfinance as yf

def send_56():
    token = os.getenv("ETF56_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    stock = yf.Ticker("0056.TW")
    price = stock.fast_info.last_price
    
    msg = f"<b>📊 元大 0056 報告</b>\n當前價格：<b>{price:.2f}</b>"
    
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    send_56()
