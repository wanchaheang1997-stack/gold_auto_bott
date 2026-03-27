import requests
import os
from datetime import datetime
import pytz

TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = "-1003709011282"

# សាកល្បងដូរ Topic ID មកលេខផ្សេង ឬទុកចោល (បើមិនច្បាស់)
TOPIC_ANALYSIS = "8" 

def send_msg(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # ព្យាយាមផ្ញើបែបមាន Topic
    payload_with_topic = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id
    }
    
    # ព្យាយាមផ្ញើបែបធម្មតា (បើ Topic ID ខុស ក៏វានឹងលោតចូល Group ដែរ)
    payload_normal = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown"
    }
    
    # រត់ការផ្ញើ
    r = requests.post(url, data=payload_with_topic)
    if not r.json().get("ok"):
        requests.post(url, data=payload_normal)

def main():
    # ទាញទិន្នន័យ Oanda
    api_url = "https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token=csqi9p1r01qs8636p630csqi9p1r01qs8636p63g"
    data = requests.get(api_url).json()
    price = float(data['c'])
    
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    kh_time = datetime.now(kh_tz).strftime('%H:%M:%S')

    # បង្ខំឱ្យផ្ញើសារ Report ភ្លាមៗ (មិនបាច់ចាំលក្ខខណ្ឌម៉ោង ៨ ទេ ដើម្បីតេស្តឱ្យឃើញ)
    msg = (
        f"🚀 **Titanium321 | Live Update**\n"
        f"💰 តម្លៃមាសបច្ចុប្បន្ន: **${price:,.2f}**\n"
        f"⏰ ម៉ោងតេស្ត: {kh_time}\n"
        f"✍️ Analyzed by: E11"
    )
    
    send_msg(msg, TOPIC_ANALYSIS)

if __name__ == "__main__":
    main()
    
