import os
import requests
from datetime import datetime

# 1. 抓取環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

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
            send_tg("❌ Token 取得失敗，請檢查金鑰。")
            return
            
        headers = {'authorization': f'Bearer {token}'}

        # 步驟 2: 抓取「靜態路段字典」
        dict_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Section/Freeway?$format=JSON"
        dict_res = requests.get(dict_url, headers=headers, timeout=10).json()
        
        # 🛡️ 防禦機制：確保回傳的是 List，否則直接印出錯誤
        dict_list = dict_res.get('Sections', dict_res) if isinstance(dict_res, dict) else dict_res
        if not isinstance(dict_list, list):
            send_tg(f"❌ TDX 字典庫異常，回傳內容：\n<code>{str(dict_res)[:100]}</code>")
            return

        target_ids = {}
        for item in dict_list:
            # 🛡️ 防禦機制：確保 item 是字典才操作
            if isinstance(item, dict):
                name = item.get('SectionName', '')
                if "新竹" in name and "竹北" in name:
                    target_ids[item.get('SectionID')] = name
                
        if not target_ids:
            send_tg("⚠️ 字典庫裡找不到『新竹-竹北』。官方可能修改了命名。")
            return

        # 步驟 3: 抓取「即時路況」
        live_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        live_res = requests.get(live_url, headers=headers, timeout=15).json()
        
        # 🛡️ 防禦機制：確保回傳的是 List
        live_list = live_res.get('LiveTraffics', live_res) if isinstance(live_res, dict) else live_res
        if not isinstance(live_list, list):
            send_tg(f"❌ TDX 即時庫異常，回傳內容：\n<code>{str(live_res)[:100]}</code>")
            return

        msg = f"<b>🚗 國一新竹段最新路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        for item in live_list:
            if isinstance(item, dict):
                sid = item.get('SectionID')
                if sid in target_ids:
                    name = target_ids[sid]
                    t = item.get('TravelTime', 0) // 60
                    status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                    msg += f"• {name}: <b>{t}分</b> ({status})\n"
                    found = True
                
        if found:
            send_tg(msg)
        else:
            send_tg("⚠️ 找到了地名，但即時庫裡沒有當下的分鐘數。")

    except Exception as e:
        send_tg(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
