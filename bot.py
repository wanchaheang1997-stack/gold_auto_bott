import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- Configuration (Hardcoded IDs) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    

def get_session_info(hour):
    """កំណត់ Session តាមម៉ោងដែលបងផ្ដល់ឱ្យ"""
    if 8 <= hour < 14: return "🇯🇵 Asia Session Open", "Focus: Tokyo/Sydney Liquidity"
    if 14 <= hour < 19: return "🇬🇧 London Session Open", "Focus: London Breakout / Judas Swing"
    if 19 <= hour < 23: return "🇺🇸 New York Session Open", "Focus: High Volatility / News Drivers"
    return "🌑 Pre-Market / Off-Hours", "Focus: Consolidation"

def send_telegram(text, topic_id):
    if not TOKEN or not GROUP_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def main():
    # កំណត់ម៉ោងនៅកម្ពុជា
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    day_of_week = now_kh.weekday() # 0=Monday, 5=Saturday, 6=Sunday
    current_hour = now_kh.hour

    # --- លក្ខខណ្ឌសម្រាកថ្ងៃចុងសប្តាហ៍ (សៅរ៍-អាទិត្យ) ---
    if day_of_week >= 5:
        print("Weekend: Bank Closed. Bot is resting...")
        return

    # ទាញយកទិន្នន័យមាស
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="10d", interval="1h")
    if df_h1.empty: return
    
    price = df_h1['Close'].iloc[-1]
    pdh, pdl = df_h1['High'].iloc[-24:].max(), df_h1['Low'].iloc[-24:].min()
    session_name, focus = get_session_info(current_hour)

    # --- ១. របាយការណ៍វិភាគតាម Session (Topic ID: 8) ---
    # បោះ Report តែនៅម៉ោងដើម Session (8:00, 14:00, 19:00) ឬតាមការចុច Manual
    is_session_start = current_hour in [8, 14, 19]
    is_manual = os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch'

    if is_session_start or is_manual:
        report = (
            f"🏦 **BANK SESSION UPDATE**\n"
            f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 **Current Session:** `{session_name}`\n"
            f"🎯 **Market Focus:** _{focus}_\n\n"
            f"💰 **Live Gold Price:** `${price:,.2f}`\n\n"
            f"🏗️ **SMC LEVELS (H1 Framework)**\n"
            f"• **BSL (Liquidity High):** `${pdh:,.2f}`\n"
            f"• **SSL (Liquidity Low):** `${pdl:,.2f}`\n\n"
            f"⚡ **STRATEGY FOR THIS SESSION**\n"
            f"1. រង់ចាំតម្លៃ Sweep កម្រិត High/Low នៃ Session មុន។\n"
            f"2. ប្រសិនបើមាន **M5 MSS** ក្រោយពេល Sweep គឺជា High Prob Setup។\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Bot នឹង Update ជូននៅដើម Session បន្ទាប់។*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- ២. ផ្នែក Alert ស្កែនរាល់ម៉ោង (Topic ID: 18) ---
    if price >= pdh:
        send_telegram(f"🚨 **LIQUIDITY ALERT!**\n🔥 Price swept PDH: `${price:,.2f}`\n🌐 Session: {session_name}", TOPIC_ALERTS)
    elif price <= pdl:
        send_telegram(f"🚨 **LIQUIDITY ALERT!**\n🔥 Price swept PDL: `${price:,.2f}`\n🌐 Session: {session_name}", TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
