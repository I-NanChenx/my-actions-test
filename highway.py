import os
import requests
from datetime import datetime

# 1. 抓取環境變數 (嚴格遵守你指定的名稱)
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
            print(f"Telegram sent: {text[:20]}...")
        else:
            print(f"Telegram failed: {res.text}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_traffic():
    """抓取國道一號新竹段路況"""
    try:
        # TDX 認證取得 Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        auth_res.raise_for_status()
        token = auth_res.json().get('access_token')

        # 抓取路況總表 (最穩定路徑，避開 404)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            return "TDX API 回傳格式異常，請檢查後台。"

        # 過濾目標：新竹 & 竹北
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
        
        return msg if found else "⚠️ 目前找不到匹配的新竹/竹北路段數據。"

    except Exception as e:
        return f"路況抓取失敗: {str(e)}"

def main():
    print("---
