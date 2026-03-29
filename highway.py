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

        # 2. 取得資料 (修正：路徑改為 Section，這才包含「新竹-竹北」這種區間名稱)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section/N1?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data = requests.get(url, headers=headers).json()
        
        # 錯誤檢查
        if isinstance(data, dict) and "message" in data:
            print(f"❌ API 回傳錯誤：{data['message']}")
            # 如果 Section 也找不到，我們印出建議
            print("💡 建議檢查 TDX 官網 API 測試頁面，確認 N1 路線是否開放 Section 查詢。")
            return
            
        if not isinstance(data, list):
            data = [data] if isinstance(data, dict) else []

        print(f"📊 成功獲取資料，包含 {len(data)} 筆路段")

        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 針對你的通勤路線過濾
        targets = ["新竹", "竹北"]

        for item in data:
            if isinstance(item, dict):
                name = item.get('SectionName', '')
                # 只要路段名稱同時包含「新竹」與「竹北」
                if all(k in name for k in targets):
                    # TravelTime 是秒，轉為分鐘
                    t = item.get('TravelTime', 0) // 60
                    status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                    msg += f"• {name}: <b>{t}分</b> ({status})\n"
                    found = True

        if not found:
            msg += "⚠️ 目前沒找到包含新竹與竹北的區間資料。\n"
            if data:
                print(f"DEBUG: 第一筆路段名稱為 {data[0].get('SectionName')}")

        # 3. 發送訊息
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務執行完畢")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
