import os
import requests
from datetime import datetime

# 1. 從 GitHub Actions 的 env 區塊抓取變數
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_tdx_token():
    """向 TDX 申請暫時性 Access Token"""
    print("--- 步驟 1: 正在申請 TDX Token ---")
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    
    if not TDX_ID or not TDX_SECRET:
        print("❌ 錯誤：找不到 TDX_ID 或 TDX_SECRET，請檢查 GitHub Secrets 設定。")
        return None

    try:
        response = requests.post(auth_url, data={
            'grant_type': 'client_credentials',
            'client_id': TDX_ID,
            'client_secret': TDX_SECRET
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Token 申請失敗，狀態碼：{response.status_code}")
            print(f"回應內容：{response.text}")
            return None
            
        token = response.json().get('access_token')
        print("✅ Token 取得成功")
        return token
    except Exception as e:
        print(f"❌ Token 申請發生異常：{e}")
        return None

def get_highway_data(token):
    """抓取國道一號 (N1) 即時旅行時間"""
    print("--- 步驟 2: 正在抓取國道路況資料 ---")
    # 取得國一全線資料
    api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
    headers = {'authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ 路況資料抓取失敗，狀態碼：{response.status_code}")
            return None
            
        data = response.json()
        print(f"✅ 成功抓取到 {len(data)} 筆路段資料")
        return data
    except Exception as e:
        print(f"❌ 路況資料抓取發生異常：{e}")
        return None

def send_to_telegram(message):
    """發送訊息至 TRAFFIC_BOT"""
    print("--- 步驟 3: 正在發送 Telegram 訊息 ---")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 錯誤：找不到 TRAFFIC_TOKEN 或 CHAT_ID。")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Telegram 訊息發送成功！")
        else:
            print(f"❌ Telegram 發送失敗：{res.text}")
    except Exception as e:
        print(f"❌ Telegram 發送發生異常：{e}")

if __name__ == "__main__":
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🚀 啟動路況監控任務 - {now}")

    # 執行流程
    access_token = get_tdx_token()
    
    if access_token:
        traffic_data = get_highway_data(access_token)
        
        if traffic_data:
            # 篩選關心的路段
            targets = ["新竹", "竹北"]
            msg = f"<b>🚗 國一新竹段路況回報 ({now[-5:]})</b>\n"
            msg += "────────────────\n"
            found_count = 0

            for item in traffic_data:
                section_name = item.get('SectionName', '')
                # 只要路段名稱包含「新竹」且包含「竹北」
                if all(k in section_name for k in targets):
                    travel_time = item.get('TravelTime', 0) // 60
                    
                    # 你的 NG 邏輯：超過 12 分鐘判定為極度擁塞
                    if travel_time >= 12:
                        status = "🚨 <b>NG 擁塞</b>"
                    elif travel_time >= 8:
                        status = "🟡 車多"
                    else:
                        status = "🟢 順暢"
                        
                    msg += f"• {section_name}: <b>{travel_time} 分</b>\n  └ 狀態: {status}\n"
                    found_count += 1

            if found_count > 0:
                send_to_telegram(msg)
            else:
                print("⚠️ 警告：在 TDX 回傳資料中找不到任何包含『新竹』與『竹北』的路段。")
    
    print("🏁 任務結束")
