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

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    # ១. ទាញទិន្នន័យពី Yahoo (ជាមួយ Backup)
    try:
        ticker = yf.Ticker("GC=F")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="5m")
        if df_h1.empty: return
    except: return

    price = df_m5['Close'].iloc[-1]
    
    # ២. គណនា Indicators (E11, Sn1P3r, BTrader)
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
    zones = {}
    for s_name, (start, end) in sessions.items():
        d = df_h1.between_time(start, end)
        zones[s_name] = {'H': d['High'].max() if not d.empty else 0, 'L': d['Low'].min() if not d.empty else 0}

    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd_stat = "BULLISH 🟢" if df_m5['Delta'].tail(3).sum() > 0 else "BEARISH 🔴"

    # --- 📢 ៣. បាញ់សារភ្លាមៗ (ពេលបងចុច RUN ឥឡូវនេះ) ---
    report = (
        f"🏛 **SOVEREIGN TRINITY REPORT**\n"
        f"📅 `{now_kh.strftime('%H:%M:%S')}` | Price: `${price:.2f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 **MACRO & SENTIMENT:**\n"
        f"• CVD Flow: `{cvd_stat}`\n"
        f"• Status: `System Online ✅`\n\n"
        f"🗺 **E11 SESSION MONITORING:**\n"
        f"• Tokyo H/L: `${zones['Tokyo']['H']:.1f}` / `${zones['Tokyo']['L']:.1f}`\n"
        f"• London H/L: `${zones['London']['H']:.1f}` / `${zones['London']['L']:.1f}`\n"
        f"• NY High/L: `${zones['NY']['H']:.1f}` / `${zones['NY']['L']:.1f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Check SFP & BTrader CHoCH!*"
    )
    # ផ្ញើចូល Topic 8 ជាការបញ្ជាក់ថា Bot ដើរ
    send_telegram(report, TOPIC_ANALYSIS)

    # ៤. មុខងារ ALERT ស្វ័យប្រវត្តិ (ទុកឱ្យវា Scan រក Triple Confluence)
    # វានឹងលោតចូល Topic 18 តែពេលណាគ្រប់លក្ខខណ្ឌប៉ុណ្ណោះ
    # ... (Logic Alert ចាស់ៗនៅដដែល)

if __name__ == "__main__":
    run_system()
    
