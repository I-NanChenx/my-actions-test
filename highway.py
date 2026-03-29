import os
import requests
from datetime import datetime

# 1. 抓取環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """發送訊息至 Telegram"""
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def main():
    print("--- 偵錯任務啟動 ---")
    
    # 步驟 1: 先傳 Hello
    send_telegram("👋 <b>偵錯模式啟動</b>\n正在嘗試抓取全台路段總表，避開 404 錯誤...")

    # 步驟 2: 取得 Token
    try:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token:
            send_telegram("❌ Token 取得失敗，請檢查 Secret 設定。")
            return
    except Exception as e:
        send_telegram(f"❌ 認證異常: {e}")
        return

    # 步驟 3: 抓取總表 (不指定 N1，避免 Resource Not Found)
    try:
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        
        # 如果還是噴錯，把錯誤訊息抓出來
        if isinstance(data, dict):
            error_msg = f"❌ API 依舊報錯：\n<code>{str(data)}</code>"
            send_telegram(error_detail)
            return

        # 步驟 4: 偵錯回報 (把前 5 筆資料傳給你看看)
        debug_msg = f"<b>📊 API 偵錯資訊</b>\n"
        debug_msg += f"• 總路段數: {len(data)}\n"
        debug_msg += f"• 前 5 筆路段名稱範例：\n"
        for item in data[:5]:
            debug_msg += f"  - {item.get('SectionName')} ({item.get('RoadName')})\n"
        
        send_telegram(debug_msg)

        # 步驟 5: 執行原本的過濾邏輯
        traffic_msg = f"<b>🚗 國一新竹段即時路況</b>\n────────────────\n"
        found = False
        for item in data:
            name = item.get('SectionName', '')
            road = item.get('RoadName', '')
            # 只要包含「新竹」與「竹北」
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                traffic_msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if found:
            send_telegram(traffic_msg)
        else:
            send_telegram("⚠️ 總表內找不到包含『新竹-竹北』的路段。")

        print("--- 偵錯任務完成 ---")

    except Exception as e:
        send_telegram(f"❌ 程式執行崩潰：{str(e)}")

if __name__ == "__main__":
    main()
