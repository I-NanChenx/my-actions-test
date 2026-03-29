import os, requests
from datetime import datetime

# 交通專用的 Token 與 TDX 金鑰
token = os.getenv("TRAFFIC_TOKEN")
chat_id = os.getenv("CHAT_ID")
tdx_id = os.getenv("TDX_ID")
tdx_secret = os.getenv("TDX_SECRET")

def get_traffic():
    # 1. 換取 TDX AccessToken
    auth_res = requests.post("https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
                            data={'grant_type': 'client_credentials', 'client_id': tdx_id, 'client_secret': tdx_secret})
    access_token = auth_res.json().get('access_token')
    
    # 2. 抓取路況
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON"
    data = requests.get(url, headers={'authorization': f'Bearer {access_token}'}).json()
    
    msg = f"<b>🚗 國一路況 ({datetime.now().strftime('%H:%M')})</b>\n"
    for item in data:
        name = item.get('SectionName', '')
        if "新竹" in name and "竹北" in name:
            t = item['TravelTime'] // 60
            status = "🚨 NG" if t >= 12 else "🟢 順暢"
            msg += f"• {name}: <b>{t}分</b> ({status})\n"
            
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    get_traffic()
