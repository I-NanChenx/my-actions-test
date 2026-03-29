import os
import requests

print("=== 🚨 程式開始執行 🚨 ===")

# 1. 檢查環境變數有沒有成功抓到
BOT_TOKEN = os.getenv("TRAFFIC_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print(f"👉 Token 讀取狀態: {'✅ 成功' if BOT_TOKEN else '❌ 失敗 (沒有抓到 TRAFFIC_TOKEN)'}")
print(f"👉 Chat ID 讀取狀態: {'✅ 成功' if CHAT_ID else '❌ 失敗 (沒有抓到 CHAT_ID)'}")

def send_tg(text):
    print(f"準備發送訊息給 Telegram: {text}")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 因為缺少 Token 或 ID，放棄發送！")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    print(f"正在呼叫網址: {url[:35]}... (隱藏後半段)")
    
    try:
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print(f"TG 伺服器回應狀態碼: {res.status_code}")
        print(f"TG 伺服器詳細回應: {res.text}")
    except Exception as e:
        print(f"❌ 網路連線 Telegram 發生嚴重錯誤: {e}")

# 鐵律：先打招呼
send_tg("hello")

print("=== 🏁 程式執行結束 🏁 ===")
