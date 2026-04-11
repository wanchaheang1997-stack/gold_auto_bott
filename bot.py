import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 8
TOPIC_ALERTS = 18

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_v30_weekend_safe():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 🛑 WEEKEND KILL-SWITCH: ថ្ងៃសៅរ៍ (5) និងអាទិត្យ (6)
    if now.weekday() >= 5:
        return # Bot បញ្ឈប់ការងារភ្លាមៗ

    # FETCH DATA
    gold = yf.Ticker("GC=F")
    df_1h = gold.history(period="5d", interval="1h")
    df_5m = gold.history(period="2d", interval="5m")
    if df_1h.empty: return
    
    curr_p = df_5m['Close'].iloc[-1]
    h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]

    # 1. ALERT LOGIC (Topic 18)
    if h1_ob_l <= curr_p <= h1_ob_h:
        alert_msg = f"🚨 **SNIPER ALERT: Price in 1H OB**\n💰 Price: `${curr_p:.2f}`\n🔥 *Check M5 for setup!*"
        send_telegram(alert_msg, TOPIC_ALERTS)

    # 2. HOURLY REPORT (Topic 8)
    if now.minute < 5: 
        report = (
            f"🏛 **E11 INTELLIGENCE V30.0**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: `${curr_p:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 **STATUS:** Market is LIVE.\n"
            f"💎 **KEY ZONES:** 1H OB `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n✅ *Full Monitoring is Active!*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_v30_weekend_safe()
    
