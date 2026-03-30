name: Stock Monitor (3006)

on:
  workflow_dispatch:
  schedule:
    # 台灣時間 週一至週五 09:00 - 13:35 (每 5 分鐘執行一次)
    # 換算 UTC 為 01:00 - 05:35
    - cron: '*/5 1-5 * * 1-5'

jobs:
  check-stock:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install requests twstock

      - name: Run Monitor
        env:
          # 這裡會從 GitHub Secrets 抓資料，並餵給程式碼裡的變數名稱
          TSMC_TOKEN: ${{ secrets.TSMC_TOKEN }}
          CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python stock.py
