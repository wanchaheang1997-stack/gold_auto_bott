import requests
import os
import yfinance as yf
from datetime import datetime
import pytz

# --- ទាញយកការកំណត់ពី GitHub Secrets ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')

# --- កំណត់តម្លៃមាសសម្រាប់ថ្ងៃនេះ (បងកែលេខ ២ នេះរាល់ព្រឹក) ---
RESISTANCE = 2210.0
SUPPORT = 2190.0

def get_gold_data():
    try:
        # ទាញតម្លៃមាស XAU/USD ពី Yahoo Finance
        gold = yf.Ticker("GC=F") # ឬប្រើ "XAUUSD=X"
        data = gold.history(period="2d")
        if data.empty: return None
        
        current_price = data['Close'].iloc[-1]
        high = data['High'].iloc[-1]
        low = data['Low'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        return {
            "price": current_price,
            "high": high,
            "low": low,
            "change": change_pct
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_msg(text, topic_id):
    if not topic_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id
    }
    requests.post(url, data=payload)

def main():
    data = get_gold_data()
    if not data: return
    
    price = data['price']
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    kh_time = datetime.now(kh_tz)

    # ១. ផ្ញើ Report ភ្លាមៗ (ដើម្បីតេស្តឱ្យឃើញសារ)
    # បើបងចង់ឱ្យវាផ្ញើតែម៉ោង ៨ ព្រឹក ចាំខ្ញុំជួយថែមលក្ខខណ្ឌម៉ោងឱ្យក្រោយ
    report = (
        f"📊 **Titanium321 | Daily Gold Report**\n"
        f"📅 {kh_time.strftime('%d %m %Y')} | ⏰ {kh_time.strftime('%H:%M')}\n"
        f"------------------------------------\n"
        f"💰 តម្លៃមាសបច្ចុប្បន្ន: **${price:,.2f}**\n"
        f"📈 បម្រែបម្រួល: {data['change']:.2f}%\n"
        f"🏔️ ខ្ពស់/ទាបថ្ងៃនេះ: ${data['high']:,.2f} / ${data['low']:,.2f}\n\n"
        f"🎯 **Key Zones:**\n"
        f"📍 Resistance: **${RESISTANCE:,.2f}**\n"
        f"📍 Support: **${SUPPORT:,.2f}**\n\n"
        f"✍️ *Analyzed by: E11*"
    )
    send_msg(report, TOPIC_ANALYSIS)

    # ២. Alert តម្លៃ
    if price <= SUPPORT:
        send_msg(f"🚨 **BUY ALERT!**\n💰 តម្លៃដល់ Support: **${price:,.2f}**", TOPIC_ALERTS)
    elif price >= RESISTANCE:
        send_msg(f"🚨 **SELL ALERT!**\n💰 តម្លៃដល់ Resistance: **${price:,.2f}**", TOPIC_ALERTS)

if __name__ == "__main__":
    main()
        
