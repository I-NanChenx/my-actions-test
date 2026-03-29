import os
import requests
import yfinance as yf
from datetime import datetime

def send_telegram(token, chat_id, message):
    if not token or not chat_id:
        print("錯誤：缺少 Token 或 Chat ID")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="100d")
    current_price = df['Close'].iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    
    # 判斷買入點（可根據需求調整邏輯）
    if current_price < ma60:
        advice = "🟢 <b>低於季線，適合分批佈局！</b>"
    else:
        advice = "🔴 <b>高於均線，暫不追高。</b>"
    return current_price, ma60, advice

if __name__ == "__main__":
    # 定義標的與對應的 Token 環境變數名稱
    stock_configs = [
        {"symbol": "2330.TW", "name": "台積電", "token_env": "TSMC_TOKEN"},
        {"symbol": "00878.TW", "name": "國泰 00878", "token_env": "ETF878_TOKEN"},
        {"symbol": "0056.TW", "name": "元大 0056", "token_env": "ETF56_TOKEN"}
    ]

    # 取得共用的 Chat ID
    common_chat_id = os.getenv("COMMON_CHAT_ID")

    for stock in stock_configs:
        # 取得專屬該標的的 Bot Token
        bot_token = os.getenv(stock['token_env'])
        
        try:
            price, m60, advice = get_stock_data(stock['symbol'])
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            message = (f"<b>📊 {stock['name']} 報告</b>\n"
                       f"時間：{now}\n"
                       f"當前價格：{price:.2f}\n"
                       f"季線支撐：{m60:.2f}\n"
                       f"────────────────\n"
                       f"建議：{advice}")
            
            send_telegram(bot_token, common_chat_id, message)
            print(f"{stock['name']} 發送成功")
        except Exception as e:
            print(f"{stock['name']} 執行失敗: {e}")    try:
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

