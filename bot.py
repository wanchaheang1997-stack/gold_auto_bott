import requests
import os
from datetime import datetime
import pytz

# --- Configuration (ប្រើ ID ដែលបងរកឃើញ) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS') # លេខ 8
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')     # លេខ 18

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    requests.post(url, data=payload)

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)

    # --- ព័ត៌មានទីផ្សារពិតប្រាកដ (Current Market Data) ---
    live_price = 4432.90
    pdh = 4475.20  # Previous Day High (26 Mar)
    pdl = 4375.80  # Previous Day Low (26 Mar)
    
    # ១. ផ្ញើរបាយការណ៍ទៅ Topic Analysis (ID: 8)
    report = (
        f"📊 **XAU/USD SMC MASTER ANALYSIS**\n"
        f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Live Price:** `${live_price:,.2f}`\n\n"
        f"🏗️ **HTF STRUCTURE (H1):** `Bearish 📉`\n"
        f"💡 **Bias:** ទីផ្សារកំពុងស្ថិតក្នុងដំណាក់កាល Correction បន្ទាប់ពីធ្លាក់ពី $5,500។\n\n"
        f"🎯 **KEY LIQUIDITY LEVELS**\n"
        f"• **BSL (PDH):** `${pdh:,.2f}`\n"
        f"• **SSL (PDL):** `${pdl:,.2f}`\n\n"
        f"🌍 **MACRO FOCUS (NY SESSION)**\n"
        f"🔴 21:00 - Michigan Consumer Sentiment (Final)\n"
        f"⚠️ *Note: តម្លៃកំពុងទាក់ទាញមករក PDL ($4,375) ដើម្បីយក SSL មុននឹងងើបឡើងវិញ។*"
        f"\n━━━━━━━━━━━━━━━━━━━━"
    )
    send_telegram(report, TOPIC_ANALYSIS)

    # ២. ផ្ញើសារតេស្តទៅ Topic Alerts (ID: 18)
    alert_test = (
        f"🚨 **SMC ALERT SYSTEM: ONLINE**\n"
        f"🔥 ស្ថានភាព៖ កំពុងស្កែនរកការទម្លុះ PDH/PDL...\n"
        f"📈 PDH Target: `${pdh:,.2f}`\n"
        f"📉 PDL Target: `${pdl:,.2f}`\n"
        f"✅ បើបងឃើញសារនេះ មានន័យថា ID 18 ដើរត្រឹមត្រូវហើយ!"
    )
    send_telegram(alert_test, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
