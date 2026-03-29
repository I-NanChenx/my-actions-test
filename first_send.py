import os
import requests

def send_telegram(message):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

if __name__ == "__main__":
    # 你可以在這裡放入抓取資料的邏輯
    send_telegram("來自 GitHub Actions 的第一封自動化通知！")
    print("Done!")
