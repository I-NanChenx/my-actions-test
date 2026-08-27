import os
import requests
import subprocess
import traceback
from datetime import datetime, timezone, timedelta

# 1. 環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 台灣時區設定
TW_TZ = timezone(timedelta(hours=8))


def send_tg_text(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"❌ [traffic] 找不到 TRAFFIC_TOKEN({bool(BOT_TOKEN)}) 或 CHAT_ID({bool(CHAT_ID)})")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        if res.status_code == 200:
            print("✅ [traffic] 路況訊息發送成功！")
            return True
        print(f"❌ [traffic] Telegram 發送失敗 ({res.status_code})：{res.text}")
        return False
    except Exception as e:
        print(f"❌ [traffic] 發送 TG 失敗: {e}")
        return False


def send_tg_photo(caption, img_path):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"❌ [traffic] 找不到 TRAFFIC_TOKEN({bool(BOT_TOKEN)}) 或 CHAT_ID({bool(CHAT_ID)})")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(img_path, "rb") as f:
            res = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption},
                                files={"photo": f}, timeout=15)
        if res.status_code == 200:
            print(f"✅ [traffic] 照片發送成功：{caption}")
            return True
        print(f"❌ [traffic] 照片發送失敗 ({res.status_code})：{res.text}")
        return False
    except Exception as e:
        print(f"❌ [traffic] 照片傳送失敗: {e}")
        send_tg_text(f"❌ 照片傳送失敗: {e}")
        return False


def main():
    tw_time = datetime.now(TW_TZ)
    print(f"🚀 [traffic] 啟動國道路況監控 - {tw_time.strftime('%Y-%m-%d %H:%M')} (台灣時間)")

    try:
        # 1. 認證 Token
        print("--- [traffic] 步驟 1: 正在向 TDX 取得 access token ---")
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token:
            print(f"❌ [traffic] TDX 認證失敗 ({auth_res.status_code})：{auth_res.text[:300]}")
            return
        print("✅ [traffic] TDX 認證成功")
        headers = {'authorization': f'Bearer {token}'}

        # 2. 抓字典找 ID
        print("--- [traffic] 步驟 2: 正在抓取國道路段字典 ---")
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
        print(f"[traffic] 符合條件的路段：{len(target_ids)} 個")

        # 3. 抓即時路況分鐘數
        print("--- [traffic] 步驟 3: 正在抓取即時路況 ---")
        live_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/Freeway?$format=JSON"
        live_res = requests.get(live_url, headers=headers, timeout=15).json()
        live_list = live_res.get('LiveTraffics', live_res) if isinstance(live_res, dict) else live_res

        # 🌟 智慧判斷方向：中午 12 點前算早上(北上)，12 點後算下午(南下)
        is_morning = tw_time.hour < 12
        direction_cctv = "-N-" if is_morning else "-S-"
        direction_zh = "北上 (往竹北)" if is_morning else "南下 (往新竹)"
        print(f"[traffic] 判定方向：{direction_zh}")

        msg = f"<b>🚗 國一 {direction_zh} 沿線路況 ({tw_time.strftime('%H:%M')})</b>\n────────────────\n"
        found = False

        if isinstance(live_list, list):
            for item in live_list:
                if isinstance(item, dict):
                    sid = item.get('SectionID')
                    if sid in target_ids:
                        name = target_ids[sid]
                        # 讓文字路況也優先顯示對應方向
                        if (is_morning and "新竹到竹北" in name) or (not is_morning and "竹北到新竹" in name):
                            t = (item.get('TravelTime') or 0) // 60
                            status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                            msg += f"• 區間預估: <b>{t}分</b> ({status})\n"
                            found = True

        if found:
            send_tg_text(msg)
        else:
            print("[traffic] 找不到對應方向的即時路況資料，略過文字訊息。")

        # 4. 抓攝影機 (鎖定單一方向，91K 到 95K)
        print("--- [traffic] 步驟 4: 正在抓取 CCTV 清單 ---")
        cctv_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/CCTV/Freeway?$format=JSON"
        cctv_res = requests.get(cctv_url, headers=headers, timeout=10).json()
        cctv_list = cctv_res.get('CCTVs', cctv_res) if isinstance(cctv_res, dict) else cctv_res

        if isinstance(cctv_list, list):
            cctv_count = 0
            target_cctvs = []

            for c in cctv_list:
                if isinstance(c, dict):
                    name = c.get('CCTVName', '') or c.get('Location', '') or str(c.get('CCTVID', ''))
                    vid_url = c.get('VideoStreamURL', '')

                    if not vid_url:
                        continue

                    # 鎖定國一 (N1)、且方向正確 (-N- 或 -S-)
                    if "N1" in name and direction_cctv in name:
                        for km in range(91, 96):
                            if f"-{km}." in name:
                                target_cctvs.append({'name': name, 'url': vid_url, 'km': km})
                                break

            # 依照公里數排序
            target_cctvs = sorted(target_cctvs, key=lambda x: x['name'])
            print(f"[traffic] 符合條件的攝影機：{len(target_cctvs)} 支（最多擷取 5 張）")

            # 開始截圖，最多抓 5 張
            for cctv in target_cctvs:
                img_file = f"cctv_{cctv_count}.jpg"
                try:
                    cmd = ["ffmpeg", "-y", "-i", cctv['url'], "-vframes", "1", "-q:v", "2", img_file]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

                    if result.returncode == 0 and os.path.exists(img_file):
                        send_tg_photo(f"📷 {cctv['name']}", img_file)
                        cctv_count += 1
                    else:
                        print(f"⚠️ [traffic] ffmpeg 擷圖失敗 ({cctv['name']})：{result.stderr.strip()[-200:]}")
                except Exception as e:
                    print(f"⚠️ [traffic] 擷圖異常 ({cctv['name']}): {e}")

                if cctv_count >= 5:
                    break

            print(f"[traffic] 本次共發送 {cctv_count} 張畫面。")
        else:
            print("[traffic] CCTV 清單格式非預期，略過擷圖。")

    except Exception as e:
        print(f"❌ [traffic] 發生崩潰: {e}")
        traceback.print_exc()
        send_tg_text(f"❌ 發生崩潰: {e}")
        raise


if __name__ == "__main__":
    main()
