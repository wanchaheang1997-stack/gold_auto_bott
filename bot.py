import requests
import os
import yfinance as yf
from datetime import datetime
import pytz

TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    requests.post(url, data=payload)

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    
    # សារតេស្តសម្រាប់ Topic Analysis
    test_analysis = f"✅ **BOT CONNECTION TEST (Analysis)**\n⏰ ម៉ោងនៅខ្មែរ: `{now_kh.strftime('%H:%M:%S')}`\n🤖 Status: Online & Ready!"
    send_telegram(test_analysis, TOPIC_ANALYSIS)
    
    # សារតេស្តសម្រាប់ Topic Alerts
    test_alert = f"🚨 **BOT CONNECTION TEST (Alerts)**\n🔥 Status: Liquidity Scanning is Active!"
    send_telegram(test_alert, TOPIC_ALERTS)
    
    print("Test messages sent to Telegram!")

if __name__ == "__main__":
    main()
    
