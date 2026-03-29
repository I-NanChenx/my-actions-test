import os
import requests
from datetime import datetime

# 1. 環境變數 (嚴格對應你指定的 ID)
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg(text):
    """專門負責傳送 Telegram 訊息"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 環境變數沒抓到 TRAFFIC_TOKEN 或 CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"TG 發送失敗: {e}")

def main():
    print("--- 任務啟動 ---")
    
    # 【鐵律 1】先傳 hello！
    send_tg("hello")

    # 【鐵律 2】只抓路況，避開 404
    try:
        # 取得 TDX Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        
        token = auth_res.json().get('access_token')
        if not token:
            send_tg("⚠️ TDX 認證失敗，請檢查 TDX_ID 與 TDX_SECRET。")
            return

        # 抓取「全台路段」總表 (最穩定的 API，不會有 Resource Not Found)
        api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(api_url, headers=headers, timeout=15)
        
        if res.status_code != 200:
            send_tg(f"⚠️ TDX 伺服器異常，狀態碼: {res.status_code}")
            return

        data = res.json()
        if not isinstance(data, list):
            send_tg(f"⚠️ TDX 回傳格式錯誤: {str(data)[:50]}")
            return
        
        # 過濾新竹-竹北
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        for item in data:
            name = item.get('SectionName', '')
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if found:
            send_tg(msg)
        else:
            send_tg("⚠️ 目前 TDX 總表內沒有新竹到竹北的數據。")

    except Exception as e:
        send_tg(f"❌ 系統發生異常: {str(e)}")

    print("--- 任務完成 ---")

if __name__ == "__main__":
    main()
