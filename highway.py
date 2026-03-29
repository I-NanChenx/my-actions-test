import os, requests
from datetime import datetime

def get_traffic():
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 1. 取得 Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret})
        auth_data = auth_res.json()
        access_token = auth_data.get('access_token')
        
        if not access_token:
            print(f"❌ Token 取得失敗：{auth_data}")
            return

        # 2. 取得資料
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data = requests.get(url, headers=headers).json()
        
        # 修正：確保 data 一定是列表，如果 API 只回傳一個物件就把它包成列表
        if isinstance(data, dict):
            # 如果回傳的是錯誤訊息 (例如 {"message": "..."})
            if "message" in data:
                print(f"❌ API 回傳錯誤：{data['message']}")
                return
            data = [data] # 將單一字典包進清單
            
        print(f"📊 成功獲取資料，包含 {len(data)} 筆路段")

        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 過濾目標關鍵字
        targets = ["新竹", "竹北"]

        for item in data:
            name = item.get('SectionName', '')
            # 只要路段名稱同時包含「新竹」與「竹北」
            if all(k in name for k in targets):
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            msg += "⚠️ 沒找到包含新竹/竹北的路段。\n"
            # 增加偵錯資訊，看看路段到底叫什麼
            if len(data) > 0:
                msg += f"<i>(API 第一筆路段：{data[0].get('SectionName', '無名稱')})</i>"

        # 3. 發送訊息
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務執行完畢")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
