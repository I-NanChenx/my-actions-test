import os, requests
from datetime import datetime

def get_traffic():
    # 抓取環境變數 (請確認 GitHub Secrets 名字對應)
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 1. 取得 Access Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': tdx_id, 
            'client_secret': tdx_secret
        }, timeout=10)
        auth_res.raise_for_status()
        access_token = auth_res.json().get('access_token')

        # 2. 抓取路況 (改用最通用的 Section 終端，不帶 /N1 避免 404)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        
        print(f"DEBUG: 正在請求 URL: {url}")
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            print(f"❌ API 錯誤：{res.status_code} - {res.text}")
            return
            
        data = res.json()
        
        # 確保是清單格式
        if not isinstance(data, list):
            print(f"❌ 資料格式錯誤：預期為 List，但收到 {type(data)}")
            return

        # 3. 過濾新竹段
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 關鍵字組合 (住關新路去台元上班，必看這兩段)
        targets = ["新竹", "竹北"]

        for item in data:
            name = item.get('SectionName', '')
            # 判斷：必須包含「新竹」與「竹北」且屬於「國道1號」
            if all(k in name for k in targets) and ("國道1號" in item.get('RoadName', '') or "N1" in item.get('RoadName', '')):
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            msg += "⚠️ 目前無匹配路段數據 (新竹-竹北)。"

        # 4. 發送至 TRAFFIC_BOT
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務成功結束")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
