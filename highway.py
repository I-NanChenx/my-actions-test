import os
import requests
from datetime import datetime

# 1. 抓取環境變數 (嚴格遵守你的 ID)
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """發送訊息至 Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 錯誤：找不到 TRAFFIC_TOKEN 或 CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Telegram 訊息發送成功")
        else:
            print(f"❌ Telegram 發送失敗：{res.text}")
    except Exception as e:
        print(f"❌ Telegram 連線異常: {e}")

def main():
    print("--- 任務啟動 ---")
    
    # 步驟 1: 先傳 Hello 確認通訊
    send_telegram("👋 <b>Hello! Traffic Bot 已連線</b>\n正在繞過 404 錯誤，嘗試抓取全台路段資料...")

    # 步驟 2: TDX 認證取得 Token
    try:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials',
            'client_id': TDX_ID,
            'client_secret': TDX_SECRET
        }, timeout=10)
        auth_res.raise_for_status()
        token = auth_res.json().get('access_token')
        print("✅ TDX Token 取得成功")
    except Exception as e:
        send_telegram(f"❌ TDX 認證失敗：{e}")
        return

    # 步驟 3: 抓取路況 (修正版：不指定 /N1，直接抓 Section 總表)
    try:
        # 這是最穩定的 API 入口，不會報 Resource Not Found
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        
        # 如果回傳不是列表，代表 API 又噴錯了
        if not isinstance(data, list):
            error_detail = f"❌ API 依舊異常：{data.get('message', '未知錯誤')}"
            print(error_detail)
            send_telegram(error_detail)
            return

        # 步驟 4: 在總表裡過濾新竹-竹北
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        for item in data:
            name = item.get('SectionName', '')
            # 只要路段名稱同時包含「新竹」與「竹北」
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if not found:
            msg += "⚠️ 目前沒撈到包含『新竹-竹北』的特定路段。"

        send_telegram(msg)
        print("--- 任務完成 ---")

    except Exception as e:
        print(f"❌ 執行異常: {e}")
        send_telegram(f"❌ 程式崩潰：{str(e)}")

if __name__ == "__main__":
    main()
