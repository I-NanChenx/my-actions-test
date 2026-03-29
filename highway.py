import os
import requests
import subprocess
from datetime import datetime, timedelta

# 1. 抓取環境變數
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
                send_tg_text(f"❌ 照片上傳 TG 失敗: {res.text}")
    except Exception as e:
        send_tg_text(f"❌ 讀取照片檔案失敗: {e}")

def main():
    send_tg_text("hello")

    try:
        # 步驟 1: 取得 Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token: return
            
        headers = {'authorization': f'Bearer {token}'}

        # 步驟 2: 抓取「靜態路段字典」找 ID
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

        # 步驟 3: 抓即時路況分鐘數
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

        # 步驟 4: 抓取攝影機並「強制截圖」 (加入錯誤回報)
        cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
        cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
        cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res
        
        if isinstance(cctv_list, list):
            cctv_count = 0
            for c in cctv_list:
                if isinstance(c, dict):
                    name = c.get('CCTVName', '') or c.get('Location', '')
                    if "國道1號" in name and ("新竹" in name or "竹北" in name):
                        vid_url = c.get('VideoStreamURL', '')
                        if vid_url:
                            img_file = f"cctv_{cctv_count}.jpg"
                            try:
                                # 呼叫截圖工具，並把時間拉長到 15 秒
                                cmd = ["ffmpeg", "-y", "-i", vid_url, "-vframes", "1", "-q:v", "2", img_file]
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                                
                                if result.returncode == 0 and os.path.exists(img_file):
                                    send_tg_photo(f"📷 {name} 畫面", img_file)
                                    cctv_count += 1
                                else:
                                    # 如果失敗，把最後 200 個字的錯誤原因傳到手機
                                    err = result.stderr[-200:] if result.stderr else "未知錯誤"
                                    send_tg_text(f"⚠️ {name} 截圖失敗！原因：\n<code>{err}</code>")
                                    
                            except subprocess.TimeoutExpired:
                                send_tg_text(f"⚠️ {name} 讀取影片超時 (可能被擋海外 IP)")
                            except Exception as e:
                                send_tg_text(f"⚠️ 系統錯誤: {e}")
                                
                        if cctv_count >= 2:
                            break

    except Exception as e:
        send_tg_text(f"❌ 發生崩潰: {str(e)}")

if __name__ == "__main__":
    main()
