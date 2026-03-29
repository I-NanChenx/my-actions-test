import os
import requests
from datetime import datetime

# 1. 抓取環境變數 (加上 .strip() 防止隱形空格)
TDX_ID = os.getenv("TDX_ID", "").strip()
TDX_SECRET = os.getenv("TDX_SECRET", "").strip()
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

def send_tg(text):
    """發送訊息至 Telegram"""
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def main():
    print("--- 任務啟動 ---")
    send_tg("🚀 <b>最後衝刺：核心診斷啟動</b>\n正在向 TDX 請求國道路況資料...")

    # 步驟 1: 取得 Token
    try:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
        if not token:
            send_tg("❌ Token 取得失敗，請確認你的 TDX_ID 和 TDX_SECRET 是否貼反了。")
            return
    except Exception as e:
        send_tg(f"❌ 認證異常: {str(e)}")
        return

    # 步驟 2: 請求 API (我們改用最標準、最穩定的總表路徑)
    # 這個路徑是 TDX 官方最建議的入口
    api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON"
    headers = {'authorization': f'Bearer {token}', 'Accept': 'application/json'}
    
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        
        # 如果不是 200 OK，把 TDX 的真心話吐出來
        if res.status_code != 200:
            error_msg = f"❌ <b>TDX 拒絕請求 (代碼: {res.status_code})</b>\n"
            error_msg += f"原因：<code>{res.text}</code>\n"
            error_msg += "💡 <i>如果是 403，代表你的 TDX 帳號還沒訂閱『國道』資料。</i>"
            send_tg(error_msg)
            return

        data = res.json()
        
        # 步驟 3: 過濾新竹段
        msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n────────────────\n"
        found = False
        
        for item in data:
            name = item.get('SectionName', '')
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        if found:
            send_tg(msg)
        else:
            # 沒找到資料，但連線是成功的，印出第一筆地名幫忙診斷
            sample = data[0].get('SectionName', '無名稱') if data else "無資料"
            send_tg(f"⚠️ 連線成功但沒找到新竹段。範例資料地名：{sample}")

    except Exception as e:
        send_tg(f"❌ 執行崩潰：{str(e)}")

if __name__ == "__main__":
    main()
