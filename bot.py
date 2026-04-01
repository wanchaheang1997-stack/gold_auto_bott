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

# សូមផ្ទៀងផ្ទាត់លេខ Topic ID ក្នុង URL Telegram របស់បង
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

def send_telegram(text, topic_id=None):
    if not TOKEN or not GROUP_ID:
        print("❌ Missing Secrets!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Log: {r.status_code}")
    except: print("❌ Connection Failed")

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    print(f"🚀 Sniper Start: {now_kh.strftime('%H:%M:%S')}")

    try:
        # ១. ទាញទិន្នន័យ XAUUSD (Spot Gold)
        ticker = yf.Ticker("XAUUSD=X")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="1m")
        
        if df_h1.empty or df_m5.empty:
            print("❌ No Market Data")
            return

        # ២. គណនា Session High/Low (Tokyo & London)
        sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
        sess_data = {}
        for name, (s, e) in sessions.items():
            d = df_h1.between_time(s, e)
            sess_data[name] = {'H': d['High'].max() if not d.empty else 0.0, 
                               'L': d['Low'].min() if not d.empty else 0.0}

        # ៣. គណនា Sn1P3r Volume Delta (ដូចក្នុង Indicator បងប្រើ)
        df_m5['D'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
        cvd_val = df_m5['D'].tail(5).sum()
        cvd_flow = "BUYING 🟢" if cvd_val > 0 else "SELLING 🔴"

        # ៤. ផ្ញើ Report តាមម៉ោង (Topic 8)
        if now_kh.hour in [8, 11, 14, 16, 17, 19, 21]:
            report = (
                f"🏛 **SOVEREIGN SNIPER V11.0**\n"
                f"📅 `{now_kh.strftime('%H:%M')}` | **XAUUSD**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **LIVE MARKET:**\n"
                f"• Price: `${df_m5['Close'].iloc[-1]:.2f}`\n"
                f"• Sn1P3r Delta: `{cvd_flow}`\n\n"
                f"🗺 **SESSION ZONES:**\n"
                f"• Tokyo: `${sess_data['Tokyo']['H']:.2f}` - `${sess_data['Tokyo']['L']:.2f}`\n"
                f"• London: `${sess_data['London']['H']:.2f}` - `${sess_data['London']['L']:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *Ready for BTrader CHoCH Confirmation*"
            )
            send_telegram(report, TOPIC_ANALYSIS)

        # ៥. REAL-TIME SFP ALERTS (Topic 18)
        curr_h, curr_l, curr_c = df_m5['High'].iloc[-1], df_m5['Low'].iloc[-1], df_m5['Close'].iloc[-1]
        
        for s_name, prices in sess_data.items():
            if prices['H'] == 0: continue
            # Check Sweep High
            if curr_h > prices['H'] and curr_c < prices['H']:
                msg = f"🚨 **SFP ALERT: {s_name.upper()} HIGH SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`"
                send_telegram(msg, TOPIC_ALERTS)
            # Check Sweep Low
            elif curr_l < prices['L'] and curr_c > prices['L']:
                msg = f"🚨 **SFP ALERT: {s_name.upper()} LOW SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`"
                send_telegram(msg, TOPIC_ALERTS)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_system()
                              
