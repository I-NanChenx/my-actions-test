import os
import sys
import requests
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SUMMARY_FILE = os.getenv("SUMMARY_FILE") or "latest_summary.txt"

TELEGRAM_LIMIT = 3800  # 留一些餘裕，避開 Telegram 4096 字元上限


def send_tg_text(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"❌ [video] 找不到 TELEGRAM_TOKEN({bool(BOT_TOKEN)}) 或 CHAT_ID({bool(CHAT_ID)})")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
        if res.status_code == 200:
            print("✅ [video] 訊息發送成功！")
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
