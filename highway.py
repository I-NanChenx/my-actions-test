import os
import requests
import subprocess
from datetime import datetime, timedelta

TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg_text(text):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def send_tg_photo(caption, img_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(img_path, "rb") as f:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=15)
    except:
        pass

def main():
    send_tg_text("hello")

    try:
        # 1. 認證
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token: return
        headers = {'authorization': f'Bearer {token}'}

        # 2. 抓字典找 ID
        dict_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Section/Freeway?$format=JSON"
        dict_res = requests.get(dict_url, headers=headers, timeout=10).json()
        dict_list = dict_res.get('Sections', dict_res) if isinstance(dict_res, dict) else dict_res
        
        target_ids = {}
        if isinstance(dict_list, list):
            for item in dict_list:
                if isinstance(item, dict):
                    name = item.get('SectionName', '')
                    if "新竹" in name and "竹北" in name:
                        target_ids[item.get('SectionID')] = name

        # 3. 抓即時路況分鐘數
        live_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        live_res = requests.get(live_url, headers=headers, timeout=15).json()
        live_list = live_res.get('LiveTraffics', live_res) if isinstance(live_res, dict) else live_res

        tw_time = datetime.utcnow() + timedelta(hours=8)
        msg = f"<b>🚗 國一新竹段最新路況 ({tw_time.strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        if isinstance(live_list, list):
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
            send_tg_text(msg)

        # 4. 抓攝影機
        cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
        cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
        cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res
        
        if isinstance(cctv_list, list):
            sample_names = [] 
            
            for c in cctv_list:
                if isinstance(c, dict):
                    # 把能抓到的名字或 ID 通通抓出來
                    name = c.get('CCTVName', '') or c.get('Location', '') or str(c.get('CCTVID', '未知ID'))
                    
                    # 這次不限制任何條件！只要前 5 支的名字！
                    if len(sample_names) < 5 and name:
                        sample_names.append(name)
            
            # 因為目前還不知道正確關鍵字，我們直接印出範例清單
            debug_msg = "⚠️ <b>攝影機偵錯模式</b>\n💡 TDX 官方命名範例如下，請看這 5 支的名字：\n"
            for s in sample_names:
                debug_msg += f"• <code>{s}</code>\n"
            
            send_tg_text(debug_msg)

    except Exception as e:
        send_tg_text(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
