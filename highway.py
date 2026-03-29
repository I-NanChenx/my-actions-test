import os
import requests
import yfinance as yf
from datetime import datetime

def send_tsmc():
    # 1. 抓取環境變數 (請確保 YAML 裡左邊名稱是 TSMC_TOKEN)
    token = os.getenv("TSMC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    print(f"🚀 啟動台監控 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if not token or not chat_id:
        print(f"❌ 錯誤：找不到 TSMC_TOKEN({bool(token)}) 或 CHAT_ID({bool(chat_id)})")
        return

    try:
        # 2. 抓取資料 (使用 2330.TW)
        print("--- 步驟 1: 正在從 Yahoo Finance 抓取資料 ---")
        stock = yf.Ticker("2330.TW")
        # 抓取 150 天資料以計算 120MA
        hist = stock.history(period="150d")

        if hist.empty:
            print("❌ 錯誤：無法取得台積電歷史資料 (DataFrame is empty)。")
            # 嘗試抓取即時價格作為備案
            price = stock.fast_info.last_price
            print(f"💡 備案：僅抓取到即時價格 {price}，但無法計算均線。")
            return

        # 3. 計算數據
        print("--- 步驟 2: 正在計算均線數據 ---")
        current_price = round(hist['Close'].iloc[-1], 2)
        ma20 = round(hist['Close'].rolling(window=20).mean().iloc[-1], 2)
        ma60 = round(hist['Close'].rolling(window=60).mean().iloc[-1], 2)
        ma120 = round(hist['Close'].rolling(window=120).mean().iloc[-1], 2)

        # 4. 判斷策略
        advice = "🔴 股價高於均線，建議觀望。"
        status_emoji = "⏳"

        if current_price <= ma120:
            advice = "🚨 <b>【資金池 C 觸發】台積電跌破半年線！</b>\n請準備動用黑天鵝戰備金，進行危機入市！"
            status_emoji = "🚨"
        elif current_price <= ma60:
            advice = "⚠️ <b>【資金池 B 觸發】台積電跌破季線！</b>\n這是一個勝率極高的波段加碼點。"
            status_emoji = "⚠️"
        elif current_price <= ma20:
            advice = "🔔 <b>【資金池 B 觸發】台積電回測月線！</b>\n短期回檔，可視情況啟動第一筆零股低接。"
            status_emoji = "🔔"

        # 5. 組裝訊息
        msg = (f"{status_emoji} <b>TSMC (2330.TW) 策略報告</b>\n"
               f"────────────────\n"
               f"• x：<b>{current_price}</b>\n"
               f"• 月線(x)：{ma20}\n"
               f"• 季線(x)：{ma60}\n"
               f"• 半年線(x)：{ma120}\n"
               f"────────────────\n"
               f"💡 策略建議：\n{advice}")

        # 6. 發送 Telegram
        print("--- 步驟 3: 正在發送 Telegram 訊息 ---")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        res = requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=10)
        
        if res.status_code == 200:
            print("✅ 訊息發送成功！")
        else:
            print(f"❌ Telegram 發送失敗：{res.text}")

    except Exception as e:
        print(f"❌ 發生異常錯誤：{str(e)}")

if __name__ == "__main__":
    send_tsmc()
