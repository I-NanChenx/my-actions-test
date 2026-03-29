import os, requests, yfinance as yf
from datetime import datetime

# 1. 抓取環境變數 (使用你要求的 ID)
TDX_ID = os.getenv("TDX_ID", "").strip()
TDX_SECRET = os.getenv("TDX_SECRET", "").strip()
TRAFFIC_TOKEN = os.getenv("TRAFFIC_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TRAFFIC_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def main():
    print("--- 深度診斷模式啟動 ---")
    
    # 第一階段：認證取得 Token
    try:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')
    except Exception as e:
        send_tg(f"❌ 認證階段崩潰: {str(e)}")
        return

    # 第二階段：地毯式嘗試不同 API 路徑 (解決 404 的必殺技)
    # 這裡列出 TDX 常見的三種路段入口
    test_urls = [
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section/N1?$format=JSON",
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section?$format=JSON",
        "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint?$format=JSON"
    ]
    
    final_data = None
    for url in test_urls:
        print(f"嘗試路徑: {url}")
        res = requests.get(url, headers={'authorization': f'Bearer {token}'}, timeout=15)
        if res.status_code == 200:
            final_data = res.json()
            break
            
    if not final_data:
        send_tg("❌ <b>掃描全數失敗 (404)</b>\n這極大機率是你的 TDX 帳號尚未手動訂閱『國道』資料集。請登入 TDX 官網確認『國道』權限是否已開啟。")
        return

    # 第三階段：股市資產報告 (既然路況卡住，先看資產壓壓驚)
    stock_msg = ""
    try:
        stocks = yf.Tickers("2891.TW 00878.TW")
        # 計算 38 張中信金與 80 張 00878
        v2891 = stocks.tickers["2891.TW"].fast_info.last_price * 38000
        v878 = stocks.tickers["00878.TW"].fast_info.last_price * 80000
        stock_msg = (f"<b>📈 資產市值：{(v2891 + v878):,.0f} 元</b>\n"
                     f"• 中信金 (38張): {v2891:,.0f}\n"
                     f"• 00878 (80張): {v878:,.0f}\n"
                     f"────────────────\n")
    except:
        stock_msg = "⚠️ 股市資料暫時抓不到。\n"

    # 第四階段：過濾路況 (相容不同 API 的地名欄位)
    msg = f"<b>🚗 國一新竹段即時路況</b>\n"
    found = False
    for item in final_data:
        name = item.get('SectionName') or item.get('ControlPointName') or ''
        if "新竹" in name and "竹北" in name:
            t = item.get('TravelTime', 0) // 60
            status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
            msg += f"• {name}: <b>{t}分</b> ({status})\n"
            found = True
            
    if not found:
        msg += f"⚠️ 已連線但沒找到新竹段，範例地名：{final_data[0].get('SectionName', '無')}"
    
    send_tg(stock_msg + msg)
    print("--- 任務完成 ---")

if __name__ == "__main__":
    main()
