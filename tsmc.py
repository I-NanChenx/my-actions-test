import os, requests
from datetime import datetime

def get_traffic():
    # 從環境變數讀取
    tdx_id = os.getenv("TDX_ID")
    tdx_secret = os.getenv("TDX_SECRET")
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    print(f"DEBUG: 正在嘗試與 TDX 連線...")
    
    try:
        # 1. 換取 AccessToken
        auth_res = requests.post(
            "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
            data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret},
            timeout=10
        )
        auth_data = auth_res.json()
        access_token = auth_data.get('access_token')

        if not access_token:
            print(f"❌ 錯誤：無法取得 Token。TDX 回傳：{auth_data}")
            return

        # 2. 抓取路況
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data_res = requests.get(url, headers=headers, timeout=10)
        data = data_res.json()

        if not isinstance(data, list):
            print(f"❌ 錯誤：路況資料格式不正確。回傳：{data}")
            return

        msg = f"<b>🚗 國一新竹段即時路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False

        for item in data:
            name = item.get('SectionName', '')
            if "新竹" in name and "竹北" in name:
                t = item['TravelTime'] // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            print("⚠️ 警告：在 TDX 資料中找不到新竹/竹北路段。")
            msg += "暫無特定路段數據。"

        # 3. 發送 Telegram
        send_res = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                                data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        
        if send_res.status_code == 200:
            print("✅ 訊息發送成功！")
        else:
            print(f"❌ Telegram 發送失敗：{send_res.text}")

    except Exception as e:
        print(f"❌ 程式執行發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
