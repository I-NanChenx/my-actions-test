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
            res = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=15)
            if res.status_code != 200:
                send_tg_text(f"❌ 照片上傳失敗: {res.text}")
    except Exception as e:
        send_tg_text(f"❌ 檔案讀取失敗: {e}")

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

        # 3. 抓路況
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

        # 4. 抓攝影機 (破解官方命名)
        cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
        cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
        cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res
        
        if isinstance(cctv_list, list):
            cctv_count = 0
            sample_names = [] # 拿來偷看官方命名的清單
            
            for c in cctv_list:
                if isinstance(c, dict):
                    name = c.get('CCTVName', '') or c.get('Location', '')
                    
                    # 收集國道一號的攝影機名字當範本
                    if "國道1號" in name or "國1" in name:
                        if len(sample_names) < 5:
                            sample_names.append(name)
                            
                    # 原本的過濾條件
                    is_target_area = any(k in name for k in ["91", "92", "93", "94", "95"])
                    if ("國1" in name or "國道1" in name or "國道一" in name) and is_target_area:
                        vid_url = c.get('VideoStreamURL', '')
                        if vid_url:
                            img_file = f"cctv_{cctv_count}.jpg"
                            try:
                                cmd = ["ffmpeg", "-y", "-i", vid_url, "-vframes", "1", "-q:v", "2", img_file]
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                                if result.returncode == 0 and os.path.exists(img_file):
                                    send_tg_photo(f"📷 {name}", img_file)
                                    cctv_count += 1
                            except:
                                pass
                        if cctv_count >= 2:
                            break
            
            # 破解時刻：如果沒抓到照片，就把官方命名印出來！
            if cctv_count == 0:
                debug_msg = "⚠️ 找不到 91K~95K 的攝影機。\n💡 <b>TDX 官方命名範例如下，請看他們到底怎麼取名：</b>\n"
                for s in sample_names:
                    debug_msg += f"• <code>{s}</code>\n"
                send_tg_text(debug_msg)

    except Exception as e:
        send_tg_text(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
