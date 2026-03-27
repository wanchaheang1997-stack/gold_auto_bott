import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- Configuration ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')
HEADER_IMAGE_LINK = "ដាក់_LINK_រូបភាព_របស់_BRO_ទីនេះ"

def get_market_data():
    try:
        gold = yf.Ticker("GC=F")
        df_5m = gold.history(period="3d", interval="5m")
        df_1h = gold.history(period="7d", interval="1h")
        df_1d = gold.history(period="60d", interval="1d")
        if df_5m.empty or df_1h.empty or df_1d.empty: return None, None, None
        return df_5m, df_1h, df_1d
    except: return None, None, None

def send_telegram(text, topic_id, photo=None):
    if not TOKEN or not GROUP_ID: return
    if photo:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {"chat_id": GROUP_ID, "photo": photo, "caption": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    df_5m, df_1h, df_1d = get_market_data()
    if df_5m is None: return

    price = df_5m['Close'].iloc[-1]
    pdh, pdl = df_1d['High'].iloc[-2], df_1d['Low'].iloc[-2]
    pwh, pwl = df_1d['High'].iloc[-10:-1].max(), df_1d['Low'].iloc[-10:-1].min()
    asia = df_5m.between_time('00:00', '07:00')
    asia_h = asia['High'].max() if not asia.empty else None
    asia_l = asia['Low'].min() if not asia.empty else None

    # --- ផ្នែក REPORT (កែសម្រួល Syntax ឱ្យត្រឹមត្រូវ) ---
    if now_kh.hour in [8, 14, 19] and now_kh.minute < 15:
        if now_kh.hour == 8: session = "🌏 ASIA"
        elif now_kh.hour == 14: session = "🇪🇺 LONDON"
        else: session = "🇺🇸 NEW YORK"
        
        report = (
            f"📊 **XAU/USD A+ SETUP ROADMAP**\n"
            f"*{session} SESSION | {now_kh.strftime('%d %b %Y')}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Price:** `${price:,.2f}`\n\n"
            f"🎯 **EXTERNAL LIQUIDITY**\n"
            f"• **PWH (BSL):** `${pwh:,.2f}`\n"
            f"• **PWL (SSL):** `${pwl:,.2f}`\n"
            f"• **PDH:** `${pdh:,.2f}`\n"
            f"• **PDL:** `${pdl:,.2f}`\n\n"
            f"🏗️ **SMC STRUCTURE**\n"
            f"• Supply: `${df_1h['High'].iloc[-48:-1].max():,.2f}`\n"
            f"• Demand: `${df_1h['Low'].iloc[-48:-1].min():,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS, photo=HEADER_IMAGE_LINK)

    # --- ផ្នែក ALERTS ---
    alerts = []
    if price > pdh: alerts.append("🔴 **PDH SWEPT**")
    elif price < pdl: alerts.append("🟢 **PDL SWEPT**")
    if now_kh.hour >= 14 and asia_h and price > asia_h: alerts.append("🇪🇺 **LONDON SWEEP ASIA HIGH**")
    elif now_kh.hour >= 14 and asia_l and price < asia_l: alerts.append("🇪🇺 **LONDON SWEEP ASIA LOW**")

    if alerts:
        alert_msg = "🚨 **ICT/SMC ALERT** 🚨\n\n" + "\n".join(alerts) + f"\n\n💰 Price: `${price:,.2f}`"
        send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
