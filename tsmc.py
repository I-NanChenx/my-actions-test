import os, requests, yfinance as yf

def send_tsmc():
    token = os.getenv("TSMC_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    stock = yf.Ticker("2330.TW")
    price = stock.fast_info.last_price
    
    msg = f"<b>📊 台積電 (2330)</b>\n當前股價：<b>{price:.2f}</b>"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    send_tsmc()
