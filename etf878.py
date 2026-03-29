import os, requests, yfinance as yf

def send_telegram(text):
    token = os.getenv("ETF878_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json=payload) # 這裡簡化，邏輯同上

def check_strategy():
    stock = yf.Ticker("00878.TW")
    hist = stock.history(period="150d")
    current_price = round(hist['Close'].iloc[-1], 2)
    ma60 = round(hist['Close'].rolling(window=60).mean().iloc[-1], 2)
    
    # 計算 80 張市值 (80,000 股)
    total_value = current_price * 80000
    
    trigger_msg = ""
    if current_price <= ma60:
        trigger_msg = "🟢 <b>00878 觸發買點：股價低於季線。</b>"
    
    # 即使沒觸發買點，也可以發送每日市值回報 (可自行選擇是否要 if trigger_msg)
    report = (f"{trigger_msg}\n\n" if trigger_msg else "") + \
             (f"📊 <b>00878 持股報告</b>\n"
              f"• 當前價格：{current_price}\n"
              f"• 您的 80 張市值：<b>${total_value:,.0f} TWD</b>")
    
    # 此處設定為「有觸發才傳」或「天天傳」
    token = os.getenv("ETF878_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": report, "parse_mode": "HTML"})

if __name__ == "__main__":
    check_strategy()
