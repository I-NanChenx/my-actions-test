import os
import requests
from datetime import datetime

# 1. 抓取環境變數 (請確認 GitHub Secrets 名稱對應)
TDX_ID = os.getenv("TDX_ID")
TDX_SECRET = os.getenv("TDX_SECRET")
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    """發送訊息至 Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 錯誤：找不到 Telegram Token 或 Chat ID，請檢查 Secrets 設定。")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code != 200:
            print(f"❌ Telegram 發送失敗，狀態碼：{res.status_code}，回應：{res.text}")
        else:
            print("✅ Telegram 訊息發送成功")
    except Exception as e:
        print(f"❌ Telegram 連線異常: {e}")

def main():
    print("--- 任務啟動 ---")
    
    # 【核心測試】先丟 Hello，這步失敗代表 Secrets 或 Bot 設定有問題
    send_telegram("👋 <b>Hello! Traffic Bot 測試連線中...</b>\n正在開始抓取路況資料。")

    # 1. TDX 認證
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
        error_msg = f"❌ TDX 認證失敗：{e}"
        print(error_msg)
        send_telegram(error_msg)
        return

    # 2. 抓取路況 (使用最穩定的 Section API)
    try:
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        
        # 偵錯：如果不是 list，就把回傳的錯誤印出來
        if not isinstance(data, list):
            error_detail = f"❌ API 回傳異常格式：{data}"
            print(error_detail)
            send_telegram(error_detail)
            return

        # 3. 過濾新竹段關鍵字
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        msg += "────────────────\n"
        found = False
        
        for item in data:
            name = item.get('SectionName', '')
            # 只要包含「新竹」與「竹北」
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if not found:
            msg += "目前暫無匹配的新竹/竹北路段數據。"

        send_telegram(msg)
        print("--- 任務完成 ---")

    except Exception as e:
        print(f"❌ 執行出錯: {e}")
        send_telegram(f"❌ 程式執行出錯: {e}")

if __name__ == "__main__":
    main()
