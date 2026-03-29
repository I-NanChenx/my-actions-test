import os
import requests
from datetime import datetime, timedelta

# 1. 抓取環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_tg(text):
    """恢復最原始、絕對會通的發送機制"""
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def main():
    # 鐵律：先打招呼
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

        # 步驟 2: 抓取「靜態路段字典」
        dict_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Section/Freeway?$format=JSON"
        dict_res = requests.get(dict_url, headers=headers, timeout=10).json()
        
        dict_list = dict_res.get('Sections', dict_res) if isinstance(dict_res, dict) else dict_res
        if not isinstance(dict_list, list): return

        target_ids = {}
        for item in dict_list:
            if isinstance(item, dict):
                name = item.get('SectionName', '')
                if "新竹" in name and "竹北" in name:
                    target_ids[item.get('SectionID')] = name
                
        if not target_ids: return

        # 步驟 3: 抓取「即時路況」
        live_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        live_res = requests.get(live_url, headers=headers, timeout=15).json()
        
        live_list = live_res.get('LiveTraffics', live_res) if isinstance(live_res, dict) else live_res
        if not isinstance(live_list, list): return

        tw_time = datetime.utcnow() + timedelta(hours=8)
        msg = f"<b>🚗 國一新竹段最新路況 ({tw_time.strftime('%H:%M')})</b>\n────────────────\n"
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

        # 步驟 4: 安全抓取 CCTV 攝影機 (加上 try-except，就算壞掉也不影響主路況)
        try:
            cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
            cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
            cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res
            
            if isinstance(cctv_list, list):
                msg += "────────────────\n<b>📷 沿線攝影機連結</b>\n"
                cctv_count = 0
                for c in cctv_list:
                    if isinstance(c, dict):
                        name = c.get('CCTVName', '') or c.get('Location', '')
                        if "國道1號" in name and ("新竹" in name or "竹北" in name):
                            vid_url = c.get('VideoStreamURL', '')
                            if vid_url:
                                msg += f"• <a href='{vid_url}'>{name}</a>\n"
                                cctv_count += 1
                                if cctv_count >= 2: break
        except:
            pass # 攝影機抓失敗就默默跳過，確保上面的分鐘數能送出去

        if found:
            send_tg(msg)
        else:
            send_tg("⚠️ 找到了地名，但目前缺乏分鐘數數據。")

    except Exception as e:
        send_tg(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
