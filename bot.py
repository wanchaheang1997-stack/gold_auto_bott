import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- Configuration ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    

def get_session_name(hour):
    """កំណត់ឈ្មោះ Session តាមម៉ោងនៅកម្ពុជា"""
    if 14 <= hour < 19: return "🇬🇧 London Session"
    if 19 <= hour < 23: return "🇺🇸 New York Session (Overlap)"
    if 23 <= hour or hour < 3: return "🇺🇸 New York Session (Late)"
    if 7 <= hour < 14: return "🇯🇵 Asian Session"
    return "🌑 Pre-Market / Consolidation"

def send_telegram(text, topic_id):
    if not TOKEN or not GROUP_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    current_hour = now_kh.hour
    session = get_session_name(current_hour)
    
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="15d", interval="1h")
    
    if df_h1.empty: return
    
    price = df_h1['Close'].iloc[-1]
    pdh, pdl = df_h1['High'].iloc[-24:].max(), df_h1['Low'].iloc[-24:].min()
    
    # --- របាយការណ៍វិភាគលម្អិត (ផ្ញើរាល់ម៉ោងនៅពេលទៀន H1 បិទ) ---
    report = (
        f"🔔 **SMC HOURLY UPDATE**\n"
        f"📅 `{now_kh.strftime('%H:%M')} | {now_kh.strftime('%d %b')}`\n"
        f"🌐 **Session:** `{session}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Live Price:** `${price:,.2f}`\n\n"
        
        f"🏗️ **HTF KEY LEVELS (H1)**\n"
        f"• **PDH (Liquidity High):** `${pdh:,.2f}`\n"
        f"• **PDL (Liquidity Low):** `${pdl:,.2f}`\n\n"
        
        f"⚡ **SESSION STRATEGY**\n"
        f"• **Status:** Wait for Session High/Low Sweep.\n"
        f"• **Action:** ប្រសិនបើតម្លៃទម្លុះ PDH/PDL ក្នុង Session នេះ រង់ចាំ M5 MSS ដើម្បីចូល Order។\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Bot នឹងបន្ត Update រាល់ ១ ម៉ោងម្តងនៅពេលបិទទៀន។*"
    )
    send_telegram(report, TOPIC_ANALYSIS)

    # --- ផ្នែក Alert (Alert ភ្លាមៗបើប៉ះកម្រិតសំខាន់) ---
    if price >= pdh:
        send_telegram(f"🚨 **BSL SWEPT!** (In {session})\n💰 Price: `${price:,.2f}`", TOPIC_ALERTS)
    elif price <= pdl:
        send_telegram(f"🚨 **SSL SWEPT!** (In {session})\n💰 Price: `${price:,.2f}`", TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
