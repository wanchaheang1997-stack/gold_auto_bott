import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 2
TOPIC_ALERTS = 3

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_v36_no_key_engine():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    if now.weekday() >= 5: return

    try:
        # 1. វិភាគដង្ហើមទីផ្សារ (Volatility)
        gold = yf.Ticker("GC=F")
        df_1h = gold.history(period="2d", interval="1h")
        curr_p = df_1h['Close'].iloc[-1]
        
        # គណនាការប្រែប្រួលក្នុង ១ ម៉ោងចុងក្រោយ
        price_change = abs(curr_p - df_1h['Open'].iloc[-1])
        volatility_status = "⚠️ HIGH VOLATILITY" if price_change > 5 else "✅ NORMAL"

        # 2. REPORT (Topic 2)
        if now.minute < 10:
            report = (
                f"🏛 **E11 INTELLIGENCE V36**\n"
                f"⏰ `{now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ **MARKET PULSE:**\n"
                f"• Status: {volatility_status}\n"
                f"• PDH/PDL: In Range\n\n"
                f"🧠 **PSYCHOLOGY:**\n"
                f"_{'ទីផ្សារបក់ខ្លាំង! រង់ចាំឱ្យតម្លៃស្ងប់សិនទើបចូលបាញ់។' if price_change > 5 else 'ទីផ្សារដើរស្រួល។ រក្សាវិន័យតាម Plan!'}_"
            )
            send_telegram(report, TOPIC_REPORT)

        # 3. ALERT (Topic 3) - បាញ់តែពេលមាសបុក Zone
        h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]
        if h1_ob_l <= curr_p <= h1_ob_h:
            send_telegram(f"🎯 **SNIPER ALERT**\nPrice in OB Zone: `${curr_p:.2f}`", TOPIC_ALERTS)

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_v36_no_key_engine()
    
