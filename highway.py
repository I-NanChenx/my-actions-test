import os
import requests
from datetime import datetime

# 1. 抓取環境變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """通用的 Telegram 發送函數"""
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def main():
    print("--- 深度偵錯任務啟動 ---")
    send_telegram("🔍 <b>開始 URL 深度掃描...</b>\n正在嘗試不同 API 路徑以解決 404 問題。")

    # 步驟 1: 取得 Token
    try:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token:
            send_telegram("❌ Token 取得失敗")
            return
    except Exception as e:
        send_telegram(f"❌ 認證異常: {e}")
        return

    # 步驟 2: 定義多個可能的路徑 (TDX API 有時會變動路徑)
    urls = [
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON",
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint?$format=JSON",
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime?$format=JSON"
    ]
    
    successful_data = None
    
    for url in urls:
        try:
            headers = {'authorization': f'Bearer {token}'}
            res = requests.get(url, headers=headers, timeout=15)
            data = res.json()
            
            if isinstance(data, list):
                successful_data = data
                send_telegram(f"✅ 成功連線！\n路徑：<code>{url.split('/')[-1]}</code>\n取得 {len(data)} 筆資料。")
                break
            else:
                print(f"URL 失敗: {url} -> {data}")
        except:
            continue

    if not successful_data:
        send_telegram("❌ 所有嘗試的路徑均回傳 404 或格式錯誤。")
        return

    # 步驟 3: 執行新竹段過濾
    msg = f"<b>🚗 國一新竹段即時路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
    found = False
    
    for item in successful_data:
        # 相容不同 API 的欄位名稱
        name = item.get('SectionName') or item.get('ControlPointName') or item.get('RoadName', '未知')
        if "新竹" in name and "竹北" in name:
            t = item.get('TravelTime', 0) // 60
            status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
            msg += f"• {name}: <b>{t}分</b> ({status})\n"
            found = True
    
    if found:
        send_telegram(msg)
    else:
        # 如果沒找到，至少給我看前三筆，好讓我判斷關鍵字
        debug_list = "\n".join([f"- {i.get('SectionName') or i.get('RoadName')}" for i in successful_data[:3]])
        send_telegram(f"⚠️ 找不到新竹/竹北。資料庫前三筆範例：\n{debug_list}")

if __name__ == "__main__":
    main()
