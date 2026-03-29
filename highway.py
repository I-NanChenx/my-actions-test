import os
import requests
from datetime import datetime

# 1. 抓取環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg(text):
    """傳送 Telegram 訊息"""
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def main():
    print("--- 任務啟動 ---")
    
    # 鐵律：先傳 hello
    send_tg("hello")

    try:
        # 1. 取得 TDX Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        
        token = auth_res.json().get('access_token')
        if not token:
            send_tg("⚠️ TDX 認證失敗，無法取得 Token。")
            return

        # 2. 🔥 改用全新版 API：高速公路即時路況 (Live/Freeway)
        api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(api_url, headers=headers, timeout=15)
        
        # 檢查是否還是 404 或其他錯誤
        if res.status_code != 200:
            send_tg(f"⚠️ TDX 伺服器異常，狀態碼: {res.status_code}\n回應: {res.text[:100]}")
            return

        data = res.json()
        
        # 預防 TDX 把它包裝在 LiveTraffics 字典裡
        if isinstance(data, dict) and 'LiveTraffics' in data:
            data = data['LiveTraffics']
        elif not isinstance(data, list):
            send_tg(f"⚠️ 資料格式非預期:\n<code>{str(data)[:100]}</code>")
            return
        
        # 3. 過濾新竹-竹北
        msg = f"<b>🚗 國一新竹段最新路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        for item in data:
            # 兼容不同欄位命名
            name = item.get('SectionName', '')
            if not name:
                name = str(item.get('SectionID', ''))
            
            # 過濾關鍵字
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                speed = item.get('TravelSpeed', 0)
                status = "🚨 <b>NG 擁塞</b>" if speed < 60 or t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> (時速 {speed}km/h {status})\n"
                found = True
        
        # 4. 發送結果或偵錯資料
        if found:
            send_tg(msg)
        else:
            # 如果成功連上新 API 但沒找到路段，印出第一筆資料的「真實結構」
            sample = str(data[0]) if data else "無資料"
            debug_msg = (f"✅ <b>404 已解決！成功連線最新 API！</b>\n\n"
                         f"⚠️ 但找不到『新竹-竹北』，可能是官方改了地名。\n"
                         f"💡 <b>請看最新資料庫長怎樣：</b>\n<code>{sample[:250]}</code>")
            send_tg(debug_msg)

    except Exception as e:
        send_tg(f"❌ 系統發生崩潰: {str(e)}")

    print("--- 任務完成 ---")

if __name__ == "__main__":
    main()
