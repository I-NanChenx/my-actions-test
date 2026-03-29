import os
import requests
import yfinance as yf
from datetime import datetime

# 1. 抓取環境變數 (已依照你的要求更新 ID)
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
            print(f"❌ Telegram 發送失敗: {res.text}")
    except Exception as e:
        print(f"❌ Telegram 連線異常: {e}")

def get_assets_report():
    """計算持股總市值 (38張中信金 + 80張00878)"""
    try:
        # 抓取 2891.TW 與 00878.TW
        tickers = yf.Tickers("2891.TW 00878.TW")
        p_2891 = tickers.tickers["2891.TW"].fast_info.last_price
        p_00878 = tickers.tickers["00878.TW"].fast_info.last_price
        
        # 計算市值 (張數轉股數)
        v_2891 = p_2891 * 38000
        v_00878 = p_00878 * 80000
        total = v_2891 + v_00878
        
        report = f"<b>📈 個人資產日報 (持股現況)</b>\n"
        report += f"• 中信金 (38張): <b>{v_2891:,.0f}</b> ({p_2891:.2f})\n"
        report += f"• 00878 (80張): <b>{v_00878:,.0f}</b> ({p_00878:.2f})\n"
        report += f"• <b>持股總市值: {total:,.0f}</b>\n"
        return report
    except Exception as e:
        print(f"❌ 資產計算出錯: {e}")
        return "⚠️ 市值計算暫時無法連線。\n"

def get_traffic_report():
    """抓取國道一號新竹段路況"""
    try:
        # 取得 TDX Token
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        auth_res = requests.post(auth_url, data={
            'grant_type': 'client_credentials', 
            'client_id': TDX_ID, 
            'client_secret': TDX_SECRET
        }, timeout=10)
        token = auth_res.json().get('access_token')

        # 抓取國一全線路況 (Section API 較穩定)
        api_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/Section/N1?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(api_url, headers=headers, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            return "⚠️ 路況資料讀取異常 (API 回傳非清單)。\n"

        traffic_msg = f"<b>🚗 國一新竹段路況 ({datetime.now().strftime('%H:%M')})</b>\n"
        found = False
        for item in data:
            name = item.get('SectionName', '')
            # 針對你通勤的「新竹-竹北」區間
            if "新竹" in name and "竹北" in name:
                t = item.get('TravelTime', 0) // 60
                status = "🚨 <b>NG 擁塞</b>" if t >= 12 else "🟢 順暢"
                traffic_msg += f"• {name}: <b>{t}分</b> ({status})\n"
                found = True
        
        return traffic_msg if found else "⚠️ 目前找不到新竹-竹北的路況數據。\n"
    except Exception as e:
        print(f"❌ 路況抓取出錯: {e}")
        return "⚠️ 路況系統連線失敗。\n"

def main():
    print("--- 任務啟動 ---")
    
    # 1. 取得資產報告
    asset_report = get_assets_report()
    
    # 2. 取得路況報告
    traffic_report = get_traffic_report()
    
    # 3. 組合並發送
    full_message = f"{asset_report}\n────────────────\n{traffic_report}"
    send_telegram(full_message)
    
    print("--- 任務完成 ---")

if __name__ == "__main__":
    main()
