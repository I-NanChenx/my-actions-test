import os
import sys
import requests
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SUMMARY_FILE = os.getenv("SUMMARY_FILE") or "latest_summary.txt"

TELEGRAM_LIMIT = 3800  # 留一些餘裕，避開 Telegram 4096 字元上限


def log_bot_identity():
    """印出目前 TELEGRAM_TOKEN 對應的 Bot 帳號，方便確認要去哪個 bot 點 /start。
    不會印出 token 本身。"""
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            info = res.json().get("result", {})
            username = info.get("username")
            first_name = info.get("first_name")
            print(f"🤖 [video] TELEGRAM_TOKEN 對應的 Bot：@{username}（{first_name}）")
            print(f"🤖 [video] 如果 Telegram 沒收到訊息，請先在 Telegram 搜尋 @{username} 並點擊 /start")
        else:
            print(f"⚠️ [video] 無法取得 Bot 資訊 ({res.status_code})：{res.text}")
    except Exception as e:
        print(f"⚠️ [video] 取得 Bot 資訊失敗: {e}")


def send_tg_text(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"❌ [video] 找不到 TELEGRAM_TOKEN({bool(BOT_TOKEN)}) 或 CHAT_ID({bool(CHAT_ID)})")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
        if res.status_code == 200:
            result = res.json().get("result", {})
            chat = result.get("chat", {})
            chat_label = chat.get("title") or chat.get("username") or chat.get("first_name") or CHAT_ID
            print(f"✅ [video] 訊息發送成功！已送達對話：{chat_label}（chat_id: {chat.get('id', CHAT_ID)}）")
            return True
        print(f"❌ [video] Telegram 發送失敗 ({res.status_code})：{res.text}")
        return False
    except Exception as e:
        print(f"❌ [video] 發送 TG 失敗: {e}")
        return False


def split_message(text, limit=TELEGRAM_LIMIT):
    """依行切割，避免訊息超過 Telegram 單則訊息的字數上限。"""
    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def main():
    tw_time = datetime.now(TW_TZ)
    print(f"🚀 [video] 啟動摘要發送工作流 - {tw_time.strftime('%Y-%m-%d %H:%M')} (台灣時間)")

    log_bot_identity()

    print(f"--- [video] 讀取摘要檔案: {SUMMARY_FILE} ---")

    if not os.path.exists(SUMMARY_FILE):
        print(f"❌ [video] 找不到摘要檔案: {SUMMARY_FILE}")
        sys.exit(1)

    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        summary = f.read().strip()

    if not summary:
        print(f"❌ [video] 摘要檔案是空的: {SUMMARY_FILE}")
        sys.exit(1)

    print("--- [video] 發送摘要到 Telegram ---")
    chunks = split_message(summary)

    ok = True
    for i, chunk in enumerate(chunks, 1):
        prefix = f"（{i}/{len(chunks)}）\n" if len(chunks) > 1 else ""
        if not send_tg_text(prefix + chunk):
            ok = False

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
