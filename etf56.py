import os, requests, yfinance as yf

def check_strategy():
    token = os.getenv("ETF56_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    stock = yf.Ticker("0056.TW")
    hist = stock.history(period="150d")
    current_price = round(hist['Close'].iloc[-1], 2)
    ma60 = round(hist['Close'].rolling(window=60).mean().iloc[-1], 2)

    if current_price <= ma60:
        msg = f"⚠️ <b>0056 跌破季線！</b>\n當前價格：{current_price}，建議關注加碼機會。"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    check_strategy()
