import os
import requests
from datetime import datetime

def get_access_token():
    """向 TDX 申請暫時性存取憑證"""
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv("TDX_CLIENT_ID"),
        'client_secret': os.getenv("TDX_CLIENT_SECRET")
    }
    response = requests.post(auth_url, data=data)
    return response.json().get('access_token')

def get_traffic_data(token):
    """抓取國道一號 (N1) 旅行時間"""
    # 這裡抓取國道一號的所有路段旅行時間
    api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
    headers = {'authorization': f'Bearer {token}'}
    response = requests.get(api_url, headers=headers)
    data = response.json()
    
    # 針對你的通勤路徑：關新路(新竹) <-> 台元(竹北)
    # 我們鎖定「新竹-竹北」與「竹北-新竹」這兩段
    targets = ["新竹-竹北", "竹北-新竹"]
    results = []
    
    for item in data:
        section = item.get('SectionName', '')
        if any(t == section for t in targets):
            results.append({
                "name": section,
                "time": item.get('TravelTime', 0) // 60 # 秒轉分
            })
    return results

if __name__ == "__main__":
    # 從 GitHub Secrets 抓取路況專用的 Bot Token 與共用的 Chat ID
    bot_token = os.getenv("TRAFFIC_BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    try:
        access_token = get_access_token()
        data = get_traffic_data(access_token)
        
        now = datetime.now().strftime("%H:%M")
        msg = f"<b>🚗 國一新竹段即時路況 ({now})</b>\n"
        msg += "────────────────\n"
        
        if not data:
            msg += "目前暫無特定路段數據。"
        else:
            for item in data:
                # 策略判斷：超過 10 分鐘代表開始塞車
                status = "🔴 擁塞" if item['time'] > 10 else "🟢 順暢"
                msg += f"• {item['name']}: <b>{item['time']} 分</b> ({status})\n"
        
        # 發送 Telegram 訊息
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("路況回報成功")
        
    except Exception as e:
        print(f"路況程式出錯: {e}")
