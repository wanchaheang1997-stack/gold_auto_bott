import requests
import os
from datetime import datetime
import pytz

# --- បងដាក់ TOKEN និង GROUP_ID ធម្មតា ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')

# --- សរសេរលេខ ID ផ្ទាល់ចូលក្នុងកូដតែម្តង ដើម្បីកុំឱ្យច្រឡំជាមួយ Secrets ---
TOPIC_ANALYSIS_ID = 8   # លេខ 8 តាម Link ដែលបងផ្ញើមក
TOPIC_ALERTS_ID = 18    # លេខ 18 តាម Link ដែលបងផ្ញើមក

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id
    }
    response = requests.post(url, data=payload)
    print(f"Sent to Topic {topic_id}: {response.json()}")

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    
    # ១. ផ្ញើទៅ Analysis (Topic ID: 8)
    send_telegram(f"✅ **TEST Analysis Topic (ID: 8)**\n⏰ ម៉ោង៖ `{now_kh.strftime('%H:%M:%S')}`", TOPIC_ANALYSIS_ID)
    
    # ២. ផ្ញើទៅ Alerts (Topic ID: 18)
    send_telegram(f"🚨 **TEST Alerts Topic (ID: 18)**\n🔥 ប្រសិនបើសារនេះលោតចូល Topic 2.Alert គឺជោគជ័យហើយ!", TOPIC_ALERTS_ID)

if __name__ == "__main__":
    main()
    
