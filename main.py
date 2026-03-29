import os
import requests

def send_telegram(message):
    # 這裡的名稱必須對應 YAML 裡的 env 設定
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    # 注意：bot 後面直接接 token，中間沒有斜線
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id, 
        "text": message,
        "parse_mode": "HTML" # 支援粗體等格式
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status() # 如果失敗會噴出錯誤
        print("Telegram 訊息傳送成功！")
    except Exception as e:
        print(f"傳送失敗：{e}")

if __name__ == "__main__":
    # 測試執行
    send_telegram("<b>GitHub Actions 通知</b>\n您的自動化腳本已成功啟動！")
