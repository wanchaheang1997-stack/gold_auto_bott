import requests
import os
from datetime import datetime
import pytz

# ទាញយក Token ពី GitHub Secret (ដែលអ្នកបានដាក់ក្នុង Settings រួចហើយ)
TOKEN = os.getenv('8383024930:AAGEah4KoRZ-9pbFOVi_mvgHVTrSWVIkGWo')

# ព័ត៌មានក្រុម និងបន្ទប់ដែលអ្នកបានផ្តល់ឱ្យ
GROUP_ID = "-1003709011282"
TOPIC_ANALYSIS = "8"
TOPIC_ALERTS = "18"

def get_oanda_gold_price():
    """ទាញតម្លៃមាស XAU/USD ពី Oanda Broker Feed"""
    try:
        # ប្រើ Finnhub API ដើម្បីទាញតម្លៃមាសពី Oanda
        api_url = "https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token=csqi9p1r01qs8636p630csqi9p1r01qs8636p63g"
        res = requests.get(api_url).json()
        return float(res['c']) # 'c' គឺជាតម្លៃ Current Price
    except Exception as e:
        print(f"Error fetching price: {e}")
        return 0

def send_msg(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "Markdown",
        "message_thread_id": topic_id
    }
    requests.post(url, data=payload)

def main():
    price = get_oanda_gold_price()
    if price == 0: return 

    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    kh_time = datetime.now(kh_tz)

    # ១. ផ្ញើការវិភាគ (រត់ចន្លោះម៉ោង ៨:០០ ដល់ ៨:១៥ ព្រឹក)
    if kh_time.hour == 8 and kh_time.minute < 15:
        report = f"📊 **DAILY GOLD ANALYSIS (OANDA)**\n⏰ ម៉ោង: {kh_time.strftime('%H:%M')}\n💰 តម្លៃបច្ចុប្បន្ន: ${price:,.2f}\n📈 Bias: {'🟢 Bullish' if price < 2650 else '🔴 Bearish'}"
        send_msg(report, TOPIC_ANALYSIS)

    # ២. Alert តំបន់ទិញលក់ (អ្នកអាចចូលមកកែលេខ ២៦៤០ ឬ ២៦៧០ នេះបានរាល់ព្រឹក)
    if price <= 2640:
        send_msg(f"🚨 **OANDA BUY ALERT!**\n💰 តម្លៃមាសចុះដល់: ${price:,.2f}\n🔥 តំបន់គួរពិចារណា BUY!", TOPIC_ALERTS)
    elif price >= 2670:
        send_msg(f"🚨 **OANDA SELL ALERT!**\n💰 តម្លៃមាសឡើងដល់: ${price:,.2f}\n🔥 តំបន់គួរពិចារណា SELL!", TOPIC_ALERTS)

if __name__ == "__main__":
    main()
  
