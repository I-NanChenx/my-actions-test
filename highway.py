import os, requests
from datetime import datetime

# 從環境變數抓取金鑰
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """通用的 Telegram 發送函數"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, data=payload)
    return res.status_code

def get_traffic():
    """抓取國道路況邏輯"""
    try:
        # 1. 取得 Access Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        access_token = auth_res.json().get('access_token')

        if not access_token:
            return "❌ TDX Token 取得失敗，請檢查 Client ID/Secret。"

        # 2. 抓取總表 (改用 Section 終端，最穩定的路徑)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {access_token}'}
        data = requests.get(url, headers=headers, timeout=10).json()

        if not isinstance(data, list):
            return f"❌ API 資料格式異常：{data}"

        # 3. 過濾目標
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        for item in data:
            name = item.get('SectionName', '')
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        return msg if found else "⚠️ 沒找到包含新竹/竹北的路段資料。"

    except Exception as e:
        return f"❌ 執行發生異常：{str(e)}"

if __name__ == "__main__":
    # 第一步：先傳 Hello 測試連線
    print("🚀 正在發送 Hello 測試訊息...")
    hello_status = send_telegram("👋 Hello! Traffic Bot 已連線，正在為您檢查路況...")
    
    if hello_status == 200:
        print("✅ Hello 訊息發送成功！")
        
        # 第二步：執行真正的路況抓取
        print("🔍 正在抓取 TDX 路況...")
        traffic_report = get_traffic()
        send_telegram(traffic_report)
        print("✅ 路況回報已發送")
    else:
        print(f"❌ Hello 訊息發送失敗，狀態碼：{hello_status}")
        print("請檢查 TRAFFIC_BOT_TOKEN 與 TELEGRAM_CHAT_            print(f"❌ 資料格式錯誤：預期為 List，但收到 {type(data)}")
            return

        # 3. 過濾新竹段
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 關鍵字組合 (住關新路去台元上班，必看這兩段)
        targets = ["新竹", "竹北"]

        for item in data:
            name = item.get('SectionName', '')
            # 判斷：必須包含「新竹」與「竹北」且屬於「國道1號」
            if all(k in name for k in targets) and ("國道1號" in item.get('RoadName', '') or "N1" in item.get('RoadName', '')):
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True

        if not found:
            msg += "⚠️ 目前無匹配路段數據 (新竹-竹北)。"

        # 4. 發送至 TRAFFIC_BOT
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                     data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ 任務成功結束")

    except Exception as e:
        print(f"❌ 發生異常：{str(e)}")

if __name__ == "__main__":
    get_traffic()
