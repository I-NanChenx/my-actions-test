import os
import requests
from datetime import datetime

# 1. 環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

def main():
    # 鐵律 1：先打招呼
    send_tg("hello")

    try:
        # 步驟 1: 取得 Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        
        if not token:
            send_tg("❌ Token 取得失敗")
            return
            
        headers = {'authorization': f'Bearer {token}'}

        # 步驟 2: 抓取「靜態路段字典」 (查出新竹的專屬 SectionID)
        dict_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Section/Freeway?$format=JSON"
        dict_res = requests.get(dict_url, headers=headers, timeout=10).json()
        
        target_ids = {}
        for item in dict_res:
            name = item.get('SectionName', '')
            # 只要名稱包含新竹與竹北，就把它的 ID 存起來
            if "新竹" in name and "竹北" in name:
                target_ids[item.get('SectionID')] = name
                
        if not target_ids:
            send_tg("⚠️ 字典庫裡找不到『新竹-竹北』，請確認官方是否改名。")
            return

        # 步驟 3: 抓取「即時路況」 (用剛查到的 ID 去對答案)
        live_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        live_res = requests.get(live_url, headers=headers, timeout=15).json()
        
        # 脫掉外層包裝
        data = live_res.get('LiveTraffics', live_res) if isinstance(live_res, dict) else live_res

        msg = f"<b>🚗 國一新竹段最新路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        for item in data:
            sid = item.get('SectionID')
            # 如果這個 ID 在我們的目標清單裡 -> 命中！
            if sid in target_ids:
                name = target_ids[sid]
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
                
        if found:
            send_tg(msg)
        else:
            send_tg("⚠️ 即時資料庫中目前缺乏該路段的分鐘數。")

    except Exception as e:
        send_tg(f"❌ 發生異常: {str(e)}")

if __name__ == "__main__":
    main()
