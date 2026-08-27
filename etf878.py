import os
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))


def send_telegram(text):
    token = os.getenv("ETF878_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        print(f"❌ [00878] 找不到 ETF878_TOKEN({bool(token)}) 或 CHAT_ID({bool(chat_id)})")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("✅ [00878] 訊息發送成功！")
            return True
        print(f"❌ [00878] Telegram 發送失敗 ({res.status_code})：{res.text}")
        return False
    except Exception as e:
        print(f"❌ [00878] 發送 TG 失敗: {e}")
        return False


def check_strategy():
    print("--- [00878] 步驟 1: 正在從 Yahoo Finance 抓取資料 ---")
    stock = yf.Ticker("00878.TW")
    hist = stock.history(period="150d")

    if hist.empty:
        print("❌ [00878] 無法取得 00878 歷史資料 (DataFrame is empty)。")
        return

    print("--- [00878] 步驟 2: 正在計算均線數據 ---")
    current_price = round(hist['Close'].iloc[-1], 2)
    ma60 = round(hist['Close'].rolling(window=60).mean().iloc[-1], 2)

    # 計算 80 張市值 (80,000 股)
    total_value = current_price * 80000

    trigger_msg = ""
    if current_price <= ma60:
        trigger_msg = "🟢 <b>00878 觸發買點：股價低於季線。</b>"

    report = (f"{trigger_msg}\n\n" if trigger_msg else "") + \
             (f"📊 <b>00878 持股報告</b>\n"
              f"• 當前價格：{current_price}\n"
              f"• 季線(60MA)：{ma60}\n"
              f"• 您的 80 張市值：<b>${total_value:,.0f} TWD</b>")

    print("--- [00878] 步驟 3: 正在發送 Telegram 訊息 ---")
    send_telegram(report)


if __name__ == "__main__":
    print(f"🚀 [00878] 啟動 00878 監控 - {datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M')} (台灣時間)")
    try:
        check_strategy()
    except Exception as e:
        print(f"❌ [00878] 發生異常錯誤：{e}")
