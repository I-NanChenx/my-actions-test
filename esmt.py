import os
import twstock
import requests
from datetime import datetime, timezone, timedelta

# ================= 參數設定區 =================
# 這裡對應 GitHub Secrets 的名稱
TG_BOT_TOKEN = os.getenv("ESMT_TOKEN")
TG_CHAT_ID = os.getenv("CHAT_ID")
STOCK_ID = '3006' # 晶豪科

# 關鍵技術價位設定
SUPPORT_PRICE = 170.0    # 絕對防守線
BREAKOUT_PRICE = 180.0   # 進攻確認線
VOLUME_THRESHOLD = 50000 # 突破時的預期基本量能

# 設定台灣時區 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))
# ==============================================

def send_telegram_message(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 錯誤：找不到 Telegram Token 或 Chat ID")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TG_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"TG 回應狀態: {res.status_code}")
    except Exception as e:
        print(f"發送 TG 失敗: {e}")

def check_stock_status():
    try:
        # 抓取即時報價 (twstock 可能因台股網頁改版而不穩定，建議後續可改用其他 API)
        realtime_data = twstock.realtime.get(STOCK_ID)
        
        if not realtime_data['success']:
            print(f"無法獲取資料。原因: {realtime_data.get('rtmessage', '未知')}")
            return

        # 取得最新價格與量能
        info = realtime_data['realtime']
        # 有時候 latest_trade_price 會是 '-'，改取最高/最低/買入價
        latest_price_str = info.get('latest_trade_price') or info.get('bid', ['0'])[0]
        
        if latest_price_str == '-':
            print("目前無成交價 (可能尚未開盤)")
            return
            
        current_price = float(latest_price_str)
        current_volume = int(info.get('accumulate_trade_volume', 0))
        
        print(f"現價: {current_price} / 總量: {current_volume}")

        # 🚨 條件 1：跌破 170 元
        if current_price < SUPPORT_PRICE:
            msg = f"⚠️ **【晶豪科 (3006) 警報】跌破防守線！**\n\n現價：`{current_price}`\n狀態：已跌破 170 元跳空缺口。"
            send_telegram_message(msg)

        # 🚀 條件 2：帶量突破 180 元
        elif current_price >= BREAKOUT_PRICE and current_volume >= VOLUME_THRESHOLD:
            msg = f"🚀 **【晶豪科 (3006) 捷報】帶量突破！**\n\n現價：`{current_price}`\n量能：`{current_volume}`\n狀態：強勢站上 180 元頸線。"
            send_telegram_message(msg)
        
        else:
            print("尚未觸發警報條件。")

    except Exception as e:
        print(f"監控發生錯誤: {e}")

if __name__ == "__main__":
    now = datetime.now(TW_TZ)
    print(f"--- 執行掃描: {now.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 判斷是否為平日 (0-4 是週一到週五)
    if now.weekday() < 5:
        check_stock_status()
    else:
        print("今日非交易日。")
