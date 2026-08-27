import os
import sys
import requests
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))

VIDEO_URL = os.getenv("VIDEO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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


def summarize_video(video_url):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = (
        "請觀看這部影片，並用繁體中文整理成清楚的重點筆記/摘要，"
        "適合想快速掌握影片內容的讀者閱讀。"
        "請包含：影片主旨、關鍵重點或數據、結論與建議。"
        "使用簡短條列式重點，避免過多行銷語氣，也不要加入影片沒有提到的內容。"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=types.Content(
            parts=[
                types.Part(file_data=types.FileData(file_uri=video_url)),
                types.Part(text=prompt),
            ]
        ),
    )
    return response.text


def main():
    tw_time = datetime.now(TW_TZ)
    print(f"🚀 [video] 啟動影片摘要工作流 - {tw_time.strftime('%Y-%m-%d %H:%M')} (台灣時間)")

    if not VIDEO_URL:
        print("❌ [video] 未提供 VIDEO_URL")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("❌ [video] 找不到 GEMINI_API_KEY")
        send_tg_text("❌ 影片摘要失敗：找不到 GEMINI_API_KEY，請確認 GitHub Secrets 設定。")
        sys.exit(1)

    print(f"--- [video] 步驟 1: 使用 Gemini 分析影片 {VIDEO_URL} ---")
    try:
        summary = summarize_video(VIDEO_URL)
    except Exception as e:
        print(f"❌ [video] Gemini 分析失敗: {e}")
        send_tg_text(f"❌ 影片摘要失敗（Gemini 分析錯誤）：{e}")
        sys.exit(1)

    if not summary:
        print("❌ [video] Gemini 沒有回傳內容")
        send_tg_text("❌ 影片摘要失敗：Gemini 沒有回傳內容。")
        sys.exit(1)

    print("--- [video] 步驟 2: 發送摘要到 Telegram ---")
    header = f"🎬 影片重點筆記\n{VIDEO_URL}\n\n"
    chunks = split_message(header + summary)

    ok = True
    for i, chunk in enumerate(chunks, 1):
        prefix = f"（{i}/{len(chunks)}）\n" if len(chunks) > 1 else ""
        if not send_tg_text(prefix + chunk):
            ok = False

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
