import requests
import os
from datetime import datetime
import pytz

# ទាញយក Token ពី GitHub Secret
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = "-1003709011282"
TOPIC_ANALYSIS = "8"
TOPIC_ALERTS = "18"

# --- កំណត់ Key Zones សម្រាប់ថ្ងៃនេះ (បងអាចឱ្យខ្ញុំកែលេខនេះរាល់ព្រឹក) ---
RESISTANCE = 4510.0
SUPPORT = 4380.0

def get_oanda_data():
    try:
        api_url = "https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token=csqi9p1r01qs8636p630csqi9p1r01qs8636p63g"
        res = requests.get(api_url).json()
        return {"price": float(res['c']), "high": float(res['h']), "low": float(res['l']), "change": float(res['dp'])}
    except: return None

def send_msg(text, topic_id):
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

    # ១. របាយការណ៍វិភាគ (រត់នៅម៉ោង ៨:០០ ព្រឹក)
    if kh_time.hour == 8 and kh_time.minute < 20:
        report = (
            f"📊 **Titanium321 | របាយការណ៍វិភាគមាស**\n"
            f"📅 ថ្ងៃទី {kh_time.strftime('%d %m %Y')}\n"
            f"------------------------------------\n"
            f"💰 **Current Price:** ${price:,.2f} (OANDA)\n"
            f"📈 **Daily Change:** {data['change']:.2f}%\n"
            f"🏔️ **High/Low:** ${data['high']:,.2f} / ${data['low']:,.2f}\n\n"
            f"🎯 **Key Zones Today:**\n"
            f"📍 Resistance: **${RESISTANCE:,.2f}**\n"
            f"📍 Support: **${SUPPORT:,.2f}**\n\n"
            f"⚠️ **Risk Management:**\n"
            f"ប្រើប្រាស់ Stop Loss ជានិច្ចដើម្បីការពារដើមទុន។\n"
            f"------------------------------------\n"
            f"✍️ **Analyzed by: E11**\n"
            f"🚀 *Power by Gemini AI Assistant*"
        )
        send_msg(report, TOPIC_ANALYSIS)

    # ២. Alert តម្លៃ (រត់រាល់ ១៥ នាទីម្តង បើតម្លៃដល់ Zone)
    if price <= SUPPORT:
        send_msg(f"🚨 **Titanium321 | BUY ALERT!**\n💰 តម្លៃដល់ Support: **${price:,.2f}**\n👉 ពិនិត្យមើល Price Action មុនចូល!", TOPIC_ALERTS)
    elif price >= RESISTANCE:
        send_msg(f"🚨 **Titanium321 | SELL ALERT!**\n💰 តម្លៃដល់ Resistance: **${price:,.2f}**\n👉 ពិនិត្យមើល Price Action មុនចូល!", TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
