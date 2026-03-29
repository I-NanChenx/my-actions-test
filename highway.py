import os
import requests
from datetime import datetime

# 1. 抓取環境變數 (使用你要求的 ID)
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """發送訊息至 Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Missing TRAFFIC_TOKEN or CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram message sent successfully")
        else:
            print(f"Telegram failed: {res.text}")
    except Exception as e:
        print(f"Telegram connection error: {e}")

def get_traffic():
    """抓取國道一號新竹段路況"""
    print("--- Start Traffic Check ---")
    try:
        # 1. 取得 Access Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        auth_res.raise_for_status()
        token = auth_res.json().get('access_token')

        # 2. 抓取路況 (改用 Section 總表，最穩定的路徑)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            print("API error: Data is not a list")
            return "TDX API system error. Please check log."

        # 3. 過濾新竹段關鍵字
        msg = f"<b>🚗 國一新竹段即時路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 遍歷所有路段，找新竹與竹北
        for item in data:
            name = item.get('SectionName', '')
            if "新竹" in name and "竹北" in name:
                # TravelTime 是秒，轉為分鐘
                t = item.get('TravelTime', 0) // 60
                # 判定塞車門檻 (12分以上顯示 NG)
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if not found:
            msg += "目前暫無匹配的新竹/竹北路段數據。"
            
        return msg

    except Exception as e:
        print(f"Error occurred: {e}")
        return f"System Error: {str(e)}"

def main():
    # 執行路況抓取
    report = get_traffic()
    
    # 發送通知
    send_telegram(report)
    print("--- Task Completed ---")

if __name__ == "__main__":
    main()        }, timeout=10)
        auth_res.raise_for_status()
        token = auth_res.json().get('access_token')

        # 2. 抓取全線路段資料 (避開 N1 關鍵字，直接用 Section 總表最穩定)
        api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(api_url, headers=headers, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            print(f"❌ API 回傳異常: {data}")
            return "⚠️ TDX 系統回應格式錯誤，請稍後再試。"

        # 3. 過濾新竹-竹北區段
        msg = f"<b>🚗 國一新竹段即時路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        # 你的通勤核心路段關鍵字
        for item in data:
            name = item.get('SectionName', '')
            # 只要路段名稱同時包含「新竹」與「竹北」
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if not found:
            msg += "⚠️ 目前找不到匹配的新竹/竹北路段數據。"
            
        return msg

    except Exception as e:
        print(f"❌ 執行異常: {e}")
        return f"⚠️ 系統執行發生錯誤: {str(e)}"

def main():
    print("--- 任務啟動 ---")
    
    # 執行路況抓取
    traffic_msg = get_traffic()
    
    # 發送通知
    send_telegram(traffic_msg)
    
    print("--- 任務完成 ---")

if __name__ == "__main__":
    main()
