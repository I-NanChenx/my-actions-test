import os, requests
from datetime import datetime

def get_traffic():
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 1. 取得 Token
        auth_res = requests.post("https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
                                data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret})
        access_token = auth_res.json().get('access_token')
        
        if not access_token:
            print(f"❌ Token 取得失敗：{auth_res.json()}")
            return

        # 2. 取得資料
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
        data = requests.get(url, headers={'authorization': f'Bearer {access_token}'}).json()
        
        print(f"📊 成功抓取資料，共有 {len(data)} 個路段")

        msg = f"<b>🚗 交通連線測試 ({datetime.now().strftime('%H:%M')})</b>\n"
        found = False
        
        # 為了除錯，我們把前五個路段名稱印在 Log 裡看它長怎樣
        for i, item in enumerate(data[:10]):
            print(f"路段範例 {i}: {item.get('SectionName')}")

        for item in data:
            if isinstance(item, dict):
                name = item.get('SectionName', '')
                # 修改判斷邏輯：只要包含「新竹」或「竹北」其中一個字就先抓出來
                if "新竹" in name or "竹北" in name:
                    t = item.get('TravelTime', 0) // 60
                    msg += f"• {name}: <b>{t}分</b>\n"
                    found = True

        if not found:
            msg += "⚠️ 沒找到包含新竹/竹北的路段。"
            print("❌ 關鍵字比對失敗，請檢查 Log 裡的路段名稱。")

        # 3. 強制發送訊息 (測試用)
        res = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                            data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        
        print(f"Telegram 回應: {res.status_code}, {res.text}")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
