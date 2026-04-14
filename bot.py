import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# --- CONFIG (ទាញយកពី GitHub Secrets ទាំងអស់ដើម្បីសុវត្ថិភាព) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')

# កែសម្រួល Topic ID តាម Group ថ្មីរបស់បង
TOPIC_REPORT = 2  # https://t.me/E11Projects/2
TOPIC_ALERTS = 3  # https://t.me/E11Projects/3

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown",
        "message_thread_id": topic_id  # បាញ់ចូល Topic ជាក់លាក់
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Status: {r.status_code}, Response: {r.text}")
    except Exception as e:
        print(f"Error sending message: {e}")

def run_v31_engine():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 🛑 សម្រាកថ្ងៃចុងសប្តាហ៍ (សៅរ៍-អាទិត្យ ទីផ្សារបិទ)
    if now.weekday() >= 5:
        return

    # 1. FETCH LIVE DATA (XAUUSD)
    try:
        gold = yf.Ticker("GC=F")
        df_1h = gold.history(period="5d", interval="1h")
        if df_1h.empty: return
        
        curr_p = df_1h['Close'].iloc[-1]
        h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]

        # 2. SNIPER ALERT (Topic 3) - បាញ់ពេលតម្លៃប៉ះ OB
        if h1_ob_l <= curr_p <= h1_ob_h:
            alert_msg = (
                f"🎯 **XAUUSD SNIPER ALERT**\n"
                f"🔥 Price is in 1H Order Block!\n"
                f"💰 Price: `${curr_p:.2f}`\n"
                f"📊 Zone: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n"
                f"⚡ *Wait for M5 CHoCH to Enter!*"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)

        # 3. HOURLY REPORT (Topic 2) - បាញ់រាល់ដើមម៉ោង
        if now.minute < 10:
            report = (
                f"🏛 **E11 PROJECTS INTELLIGENCE**\n"
                f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📈 **1H MARKET STRUCTURE:**\n"
                f"• Trend: {'Bullish ↗️' if curr_p > df_1h['Close'].iloc[-24] else 'Bearish ↘️'}\n"
                f"• Range: `${df_1h['Low'].tail(24).min():.2f} - ${df_1h['High'].tail(24).max():.2f}`\n\n"
                f"💎 **ACTIVE SMC ZONES:**\n"
                f"• 1H OB: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Status: Full Monitoring Active*"
            )
            send_telegram(report, TOPIC_REPORT)

    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    run_v28_final() # កែមក run_v31_engine() ពេលបង Update
    run_v31_engine()
    
