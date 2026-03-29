import os, requests
from datetime import datetime

def get_traffic():
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 1. 取得 Access Token
        auth_res = requests.post("https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
                                data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret})
        access_token = auth_res.json().get('access_token')
        
        if not access_token:
            print("❌ Token 取得失敗，請檢查 Client ID/Secret")
            return

        # 2. 抓取「全台灣國道」旅行時間，避免單一路徑找不到的情況
        # 這是最穩定的 API 入口
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data = requests.get(url, headers=headers).json()
        
        if isinstance(data, dict) and "message" in data:
            print(f"❌ API 錯誤：{data.get('message')}")
            return

        msg = f"<b>🚗 國一新竹段即時路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 定義我們要找的目標
        # 因為你住關新路，去台元上班，我們鎖定這兩個區段
        for item in data:
            name = item.get('SectionName', '')
            # 國道一號通常會寫在 RoadName 或是 SectionName 裡
            road_name = item.get('RoadName', '')
            
            # 判斷標準：必須是「國道 1 號」且包含「新竹」與「竹北」
            if ("國道1號" in road_name or "N1" in road_name) and ("新竹" in name and "竹北" in name):
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            msg += "⚠️ 目前無匹配路段數據 (新竹-竹北)。"
            # 如果還是找不到，把前三筆印在 Log 裡幫忙診斷
            if data:
                print(f"DEBUG: 第一筆路段名：{data[0].get('SectionName')} 路名：{data[0].get('RoadName')}")

        # 3. 發送 Telegram
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務執行成功")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
