import os, requests

def get_token():
    res = requests.post("https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", 
                        data={'grant_type': 'client_credentials', 
                              'client_id': os.getenv("TDX_ID"), 
                              'client_secret': os.getenv("TDX_SECRET")})
    return res.json().get('access_token')

if __name__ == "__main__":
    token = get_token()
    bot_token = os.getenv("TRAFFIC_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    # 抓取國一旅行時間
    data = requests.get("https://tdx.transportdata.tw/api/basic/v2/Road/Highway/TravelTime/ControlPoint/N1?$format=JSON", 
                        headers={'authorization': f'Bearer {token}'}).json()
    
    targets = ["新竹-竹北", "竹北-新竹"]
    msg = "<b>🚗 國一新竹段路況回報</b>\n"
    
    for item in data:
        if item.get('SectionName') in targets:
            min_time = item['TravelTime'] // 60
            status = "🚨 <b>NG 擁塞</b>" if min_time >= 12 else "🟢 順暢"
            msg += f"• {item['SectionName']}: <b>{min_time}分</b> ({status})\n"
            
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                  data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
