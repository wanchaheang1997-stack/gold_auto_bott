import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')

# Topic IDs តាម Group ថ្មីរបស់បង
TOPIC_REPORT = 2
TOPIC_ALERTS = 3

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown",
        "message_thread_id": topic_id
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Sent to Topic {topic_id}: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def run_v31_engine():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 🛑 សម្រាកថ្ងៃចុងសប្តាហ៍
    if now.weekday() >= 5:
        return

    try:
        gold = yf.Ticker("GC=F")
        df_1h = gold.history(period="5d", interval="1h")
        if df_1h.empty: return
        
        curr_p = df_1h['Close'].iloc[-1]
        h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]

        # 1. ALERT LOGIC (Topic 3)
        # បន្ថែម Resistance $4,800 ជា Key Level
        if h1_ob_l <= curr_p <= h1_ob_h or curr_p >= 4800:
            alert_msg = (
                f"🎯 **XAUUSD SNIPER ALERT**\n"
                f"⚠️ {'Price hit Resistance $4800!' if curr_p >= 4800 else 'Price in 1H OB'}\n"
                f"💰 Price: `${curr_p:.2f}`\n"
                f"🔥 Zone: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)

        # 2. HOURLY REPORT (Topic 2)
        if now.minute < 10:
            report = (
                f"🏛 **E11 PROJECTS INTELLIGENCE**\n"
                f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **MARKET UPDATE (14-APR-2026):**\n"
                f"• Trend: Bullish Momentum ↗️\n"
                f"• Target: $4,800 - $4,833\n"
                f"• Support: $4,753, $4,731\n\n"
                f"💎 **ACTIVE SMC ZONES:**\n"
                f"• 1H OB: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Status: Full Monitoring Active*"
            )
            send_telegram(report, TOPIC_REPORT)

    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    run_v31_engine()
    
