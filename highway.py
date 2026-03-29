import os, requests
from datetime import datetime

def get_traffic():
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 1. 換取 Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret})
        access_token = auth_res.json().get('access_token')
        
        # 2. 抓取「所有」路段資料 (拿掉 N1 字樣，避免 API 找不到路徑)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data = requests.get(url, headers=headers).json()
        
        # 錯誤檢查
        if isinstance(data, dict) and "message" in data:
            print(f"❌ API 錯誤：{data.get('message')}")
            return

        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 過濾「國道1號」且包含「新竹」與「竹北」的路段
        for item in data:
            name = item.get('SectionName', '')
            # 判斷路段名稱
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            msg += "⚠️ 目前無匹配路段數據 (新竹-竹北)。"

        # 3. 發送 Telegram
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 交通回報執行成功")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
