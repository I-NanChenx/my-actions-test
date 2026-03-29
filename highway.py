import os
import requests
import subprocess
from datetime import datetime, timedelta

# 1. 環境變數
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
    except Exception as e:
        print(f"照片傳送失敗: {e}")

def main():
    send_tg_text("hello")

    try:
        # 1. 認證 Token
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

        # 4. 抓攝影機 (使用破解後的 N1 公里數密碼)
        cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
        cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
        cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res
        
        if isinstance(cctv_list, list):
            cctv_count = 0
            
            for c in cctv_list:
                if isinstance(c, dict):
                    name = c.get('CCTVName', '') or c.get('Location', '') or str(c.get('CCTVID', ''))
                    
                    # 鎖定條件：必須包含 "N1" (國一)，且公里數為 91~95 開頭
                    # 匹配例如：CCTV-N1-S-91.200-M
                    is_n1 = "N1" in name
                    is_hsinchu_area = any(f"-{km}." in name for km in range(91, 96))
                    
                    if is_n1 and is_hsinchu_area:
                        vid_url = c.get('VideoStreamURL', '')
                        if vid_url:
                            img_file = f"cctv_{cctv_count}.jpg"
                            try:
                                # 呼叫 ffmpeg 截圖
                                cmd = ["ffmpeg", "-y", "-i", vid_url, "-vframes", "1", "-q:v", "2", img_file]
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                                
                                if result.returncode == 0 and os.path.exists(img_file):
                                    # 成功截圖，發送照片
                                    send_tg_photo(f"📷 國一 {name} 即時畫面", img_file)
                                    cctv_count += 1
                                else:
                                    # 如果截圖失敗，印出原因
                                    err = result.stderr[-100:] if result.stderr else "截圖程式無回應"
                                    send_tg_text(f"⚠️ {name} 截圖失敗: {err}")
                            except Exception as e:
                                send_tg_text(f"⚠️ {name} 讀取異常: {str(e)}")
                                
                        if cctv_count >= 2: # 抓兩張就收工
                            break

            if cctv_count == 0:
                send_tg_text("⚠️ 有找到攝影機清單，但截圖全部超時或失敗 (高公局可能擋海外 IP)。")

    except Exception as e:
        send_tg_text(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
