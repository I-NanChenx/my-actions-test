import os
import requests
from datetime import datetime

def get_traffic():
    # 1. 抓取環境變數
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    try:
        # 2. 換取 TDX AccessToken
        auth_res = requests.post(
            "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
            data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret},
            timeout=10
        )
        auth_data = auth_res.json()
        access_token = auth_data.get('access_token')

        if not access_token:
            print(f"❌ TDX 認證失敗！回傳訊息：{auth_data}")
            return

        # 3. 抓取路況
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data_res = requests.get(url, headers=headers, timeout=10)
        data = data_res.json()

        # 🚨 重要：檢查回傳資料是否為「列表」
        if not isinstance(data, list):
            print(f"❌ API 回傳格式錯誤（可能被拒絕存取）。回傳內容：{data}")
            return

        # 4. 篩選路段
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        for item in data:
            # 確保 item 是字典格式才執行 .get
            if isinstance(item, dict):
                name = item.get('SectionName', '')
                if "新竹" in name and "竹北" in name:
                    t = item.get('TravelTime', 0) // 60
                    status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                    msg += f"• {name}: <b>{t}分</b> ({status})\n"
                    found = True

        if not found:
            msg += "⚠️ 目前無特定路段資料。"

        # 5. 發送 Telegram
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務完成")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
