import os
import twstock
import requests
from datetime import datetime, timezone, timedelta

# ================= 參數設定區 =================
# 依照要求使用這兩個變數名稱
token = os.getenv("TSMC_TOKEN")
chat_id = os.getenv("CHAT_ID")

STOCK_ID = '3006' # 晶豪科

# 關鍵技術價位
SUPPORT_PRICE = 170.0    # 防守線
BREAKOUT_PRICE = 180.0   # 突破線
VOLUME_THRESHOLD = 50000 # 突破時的量能門檻

# 台灣時區設定
TW_TZ = timezone(timedelta(hours=8))
# ==============================================

def send_tg_message(message):
    if not token or not chat_id:
        print("❌ 錯誤：找不到 TSMC_TOKEN 或 CHAT_ID 環境變數")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"發送 TG 失敗: {e}")

def main():
    try:
        # 抓取即時報價
        realtime_data = twstock.realtime.get(STOCK_ID)
        
        if not realtime_data['success']:
            print(f"抓取失敗: {realtime_data.get('rtmessage')}")
            return

        info = realtime_data['realtime']
        # 處理盤中可能沒有成交價的情況
        latest_price_str = info.get('latest_trade_price') or info.get('bid', ['0'])[0]
        
        if latest_price_str == '-':
            print("目前無成交價 (可能尚未開盤或暫停交易)")
            return
            
        current_price = float(latest_price_str)
        current_volume = int(info.get('accumulate_trade_volume', 0))
        
        print(f"晶豪科(3006) 現價: {current_price} / 總量: {current_volume}")

        # 🚨 條件 1：跌破 170 元
        if current_price < SUPPORT_PRICE:
            msg = f"⚠️ **【晶豪科 (3006) 警報】跌破防守！**\n\n現價：`{current_price}`\n狀態：已跌破 170 元跳空缺口，結構破壞。"
            send_tg_message(msg)

        # 🚀 條件 2：帶量突破 180 元
        elif current_price >= BREAKOUT_PRICE and current_volume >= VOLUME_THRESHOLD:
            msg = f"🚀 **【晶豪科 (3006) 捷報】帶量突破！**\n\n現價：`{current_price}`\n量能：`{current_volume}`\n狀態：強勢站上 180 元頸線。"
            send_tg_message(msg)
        
        else:
            print("目前盤勢平穩，未達警報觸發門檻。")

    except Exception as e:
        print(f"程式執行異常: {e}")

if __name__ == "__main__":
    now = datetime.now(TW_TZ)
    # 僅在平日週一至週五執行
    if now.weekday() < 5:
        main()
    else:
        print("今日非交易日，不執行掃描。")
