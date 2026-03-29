import os
import requests
import yfinance as yf
from datetime import datetime

# 通用發送函數
def send_telegram(token, chat_id, message):
    if not token or not chat_id:
        print("錯誤：缺少 Token 或 Chat ID，無法發送訊息。")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("訊息傳送成功")
    except Exception as e:
        print(f"傳送失敗: {e}")

# 獲取價格與均線邏輯
def get_analysis(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="100d")
    if df.empty:
        return None, None, "無法取得資料"
        
    current_price = df['Close'].iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    
    # 判斷買入點（低於季線 MA60 為好買點）
    if current_price < ma60:
        advice = "🟢 <b>低於季線，適合分批買進！</b>"
    else:
        advice = "🔴 <b>高於季線，建議不追高。</b>"
    return current_price, ma60, advice

if __name__ == "__main__":
    # 標的設定清單：token_env 必須對應 YAML 裡的 env 名稱
    stock_list = [
        {"symbol": "2330.TW", "name": "台積電", "token_env": "TSMC_TOKEN"},
        {"symbol": "00878.TW", "name": "國泰 00878", "token_env": "ETF878_TOKEN"},
        {"symbol": "0056.TW", "name": "元大 0056", "token_env": "ETF56_TOKEN"}
    ]

    # 從環境變數抓取共用的 Chat ID
    common_chat_id = os.getenv("CHAT_ID")

    for stock in stock_list:
        # 動態抓取對應的 Bot Token
        bot_token = os.getenv(stock['token_env'])
        
        try:
            price, m60, advice = get_analysis(stock['symbol'])
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            message = (f"<b>📊 {stock['name']} 報告 ({stock['symbol']})</b>\n"
                       f"時間：{now}\n"
                       f"當前價格：{price:.2f}\n"
                       f"季線支撐：{m60:.2f}\n"
                       f"────────────────\n"
                       f"建議：{advice}")
            
            send_telegram(bot_token, common_chat_id, message)
        except Exception as e:
            print(f"{stock['name']} 處理錯誤: {e}")
