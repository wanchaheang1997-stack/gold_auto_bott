import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime

# ========================================
# ⚙️ CONFIGURATION
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID') 
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"📡 Status: {r.status_code}")
    except: pass

def get_yahoo_data():
    # ១. ព្យាយាមទាញទិន្នន័យមាស (ការពារកុំឱ្យជួប Error 404)
    gold_symbols = ["GC=F", "XAUUSD=X", "XAU-USD"]
    df_gold = pd.DataFrame()
    for sym in gold_symbols:
        try:
            df_gold = yf.Ticker(sym).history(period="2d", interval="1h")
            if not df_gold.empty: break
        except: continue

    # ២. ទាញទិន្នន័យ Macro (Yield & Silver)
    try:
        yield_10y = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
        gs_ratio = df_gold['Close'].iloc[-1] / silver if not df_gold.empty else 0
    except:
        yield_10y, gs_ratio = 0.0, 0.0

    return df_gold, yield_10y, gs_ratio

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    df_gold, yld, gsr = get_yahoo_data()
    if df_gold.empty: 
        print("❌ មិនអាចទាញទិន្នន័យពី Yahoo បានឡើយ")
        return

    price = df_gold['Close'].iloc[-1]
    
    # --- ១. សារតេស្ត (បាញ់ភ្លាមៗពេល Run) ---
    test_msg = f"🚀 **Yahoo Engine Online!**\n💰 Gold: `${price:.2f}` | 📈 Yield: `{yld:.2f}%`"
    send_telegram(test_msg, TOPIC_ANALYSIS)

    # --- ២. REPORT (តាមទម្រង់ដែលបងចង់បាន) ---
    target_hours = [8, 10, 14, 16, 19, 21, 22]
    if now_kh.hour in target_hours:
        report = (
            f"🏛 **SOVEREIGN SESSION REPORT**\n"
            f"📅 `{now_kh.strftime('%H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **MACRO & SENTIMENT:**\n"
            f"• Price: `${price:.2f}`\n"
            f"• Yield: `{yld:.2f}%` | Gold/Silver: `{gsr:.1f}`\n"
            f"• Sentiment: `Monitoring Liquidity...`\n\n"
            f"🗺 **SESSION MONITORING:**\n"
            f"• 🇯🇵 Tokyo | 🇬🇧 London | 🇺🇸 N.York\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Check SFP & Sweep on TradingView!*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

if __name__ == "__main__":
    run_system()
    
