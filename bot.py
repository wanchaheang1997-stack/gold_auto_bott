import requests
import os
from datetime import datetime
import pytz

# --- ទាញយកការកំណត់ពី GitHub Secrets & Variables ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
FINNHUB_KEY = os.getenv('FINNHUB_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')

# --- តំបន់កំណត់តម្លៃមាស (បងកែលេខ ២ នេះរាល់ព្រឹក) ---
RESISTANCE = 4510.0
SUPPORT = 4380.0

def get_oanda_data():
    try:
        # ទាញតម្លៃមាសពី Finnhub (OANDA Symbol)
        api_url = f"https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token={FINNHUB_KEY}"
        res = requests.get(api_url).json()
        return {
            "price": float(res['c']), 
            "high": float(res['h']), 
            "low": float(res['l']), 
            "change": float(res['dp'])
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def send_msg(text, topic_id):
    if not topic_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id,
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

def main():
    data = get_oanda_data()
    if not data: return
    
    price = data['price']
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    kh_time = datetime.now(kh_tz)

    # --- ១. ផ្ញើ Daily Report (ចន្លោះម៉ោង ៨:០០ - ៨:១៥ ព្រឹក) ---
    if kh_time.hour == 8 and kh_time.minute < 15:
        report = (
            f"📊 **Titanium321 | Daily Analysis**\n"
            f"📅 {kh_time.strftime('%d %m %Y')} | ⏰ {kh_time.strftime('%H:%M')}\n"
            f"------------------------------------\n"
            f"💰 តម្លៃបច្ចុប្បន្ន: **${price:,.2f}**\n"
            f"📈 បម្រែបម្រួល: {data['change']:.2f}%\n"
            f"🏔️ ខ្ពស់/ទាបថ្ងៃនេះ: ${data['high']:,.2f} / ${data['low']:,.2f}\n\n"
            f"🎯 **Key Zones Today:**\n"
            f"📍 Resistance: **${RESISTANCE:,.2f}**\n"
            f"📍 Support: **${SUPPORT:,.2f}**\n\n"
            f"✍️ *Analyzed by: E11*"
        )
        send_msg(report, TOPIC_ANALYSIS)

    # --- ២. ប្រព័ន្ធ Alert តម្លៃ (រត់រាល់ ១៥ នាទី) ---
    if price <= SUPPORT:
        alert_buy = (
            f"🚨 **Titanium321 | BUY ALERT!**\n"
            f"💰 តម្លៃចុះដល់ Support: **${price:,.2f}**\n"
            f"⚡ ពិនិត្យមើលសញ្ញាត្រឡប់ក្បាលឡើង!"
        )
        send_msg(alert_buy, TOPIC_ALERTS)
        
    elif price >= RESISTANCE:
        alert_sell = (
            f"🚨 **Titanium321 | SELL ALERT!**\n"
            f"💰 តម្លៃឡើងដល់ Resistance: **${price:,.2f}**\n"
            f"⚡ ពិនិត្យមើលសញ្ញាត្រឡប់ក្បាលចុះ!"
        )
        send_msg(alert_sell, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
        
