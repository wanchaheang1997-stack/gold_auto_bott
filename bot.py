import requests
import os
from datetime import datetime
import pytz

# ១. ទាញយក Token ពី GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')

# ២. ព័ត៌មាន Group និង Topic (បងបានផ្ដល់ឱ្យ)
GROUP_ID = "-1003709011282"
TOPIC_ANALYSIS = "8"
TOPIC_ALERTS = "18"

def send_msg(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id
    }
    response = requests.post(url, data=payload)
    # បង្ហាញលទ្ធផលក្នុង GitHub Actions Log ដើម្បីឱ្យយើងដឹងថា error អី
    print(f"Sending to Topic {topic_id}: {response.json()}")

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    kh_time = datetime.now(kh_tz).strftime('%H:%M:%S')

    print(f"--- កំពុងចាប់ផ្តើមតេស្តនៅម៉ោង: {kh_time} ---")

    # តេស្តផ្ញើចូលបន្ទប់ Analysis
    test_1 = f"🔔 **Titanium321 | TEST 1**\n📍 បញ្ជូនទៅកាន់: Analysis (Topic 8)\n⏰ ម៉ោងនៅខ្មែរ: {kh_time}\n✅ ស្ថានភាព: កំពុងតេស្តការតភ្ជាប់..."
    send_msg(test_1, TOPIC_ANALYSIS)

    # តេស្តផ្ញើចូលបន្ទប់ Alerts
    test_2 = f"⚠️ **Titanium321 | TEST 2**\n📍 បញ្ជូនទៅកាន់: Alerts (Topic 18)\n✍️ Analyzed by: E11\n🚀 ស្ថានភាព: Bot កំពុងដំណើរការ!"
    send_msg(test_2, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
