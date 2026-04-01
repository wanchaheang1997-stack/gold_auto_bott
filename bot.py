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

def get_macro_and_sentiment():
    try:
        # 1. Fundamental
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        gold = yf.Ticker("GC=F").history(period="2d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="2d")['Close'].iloc[-1]
        gs_ratio = gold / silver
        
        # 2. Sentimental (RSI Based)
        hist = yf.Ticker("GC=F").history(period="5d", interval="1h")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        s_bias = "Retail Bias: BUYING 🟢" if rsi > 60 else "Retail Bias: SELLING 🔴"
        s_ratio = f"{int(rsi)}% / {100-int(rsi)}%" if rsi > 60 else f"{100-int(rsi)}% / {int(rsi)}%"
        return tnx, gs_ratio, s_bias, s_ratio
    except: return 0.0, 0.0, "Sentiment: N/A", "50/50"

def get_session_data(df_h1):
    # កំណត់ម៉ោងតាម Session (UTC+7)
    sessions = {
        'Tokyo': ('08:00', '10:00'),
        'London': ('14:00', '16:00'),
        'New York': ('19:00', '22:00')
    }
    results = {}
    for name, (start, end) in sessions.items():
        data = df_h1.between_time(start, end)
        if not data.empty:
            results[name] = {'H': data['High'].max(), 'L': data['Low'].min()}
        else:
            results[name] = {'H': 0.0, 'L': 0.0}
    return results

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    ticker = yf.Ticker("GC=F")
    df_h1 = ticker.history(period="5d", interval="1h")
    df_m5 = ticker.history(period="2d", interval="5m")
    if df_h1.empty or df_m5.empty: return

    # ទាញទិន្នន័យ
    tnx, gs, s_bias, s_ratio = get_macro_and_sentiment()
    sess = get_session_data(df_h1)
    
    # CVD Logic
    df_m5['D'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd_val = df_m5['D'].tail(12).sum()
    cvd_flow = "Aggressive Buying 🟢" if cvd_val > 0 else "Aggressive Selling 🔴"

    # --- [A] REPORT (Topic 8) ---
    if now_kh.hour in [8, 11, 14, 15, 19, 21]:
        report = (
            f"🏛 **SOVEREIGN SESSION REPORT**\n"
            f"📅 `{now_kh.strftime('%H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **MACRO & SENTIMENT:**\n"
            f"• Yield: `{tnx:.2f}%` | Gold/Silver: `{gs:.1f}`\n"
            f"• `{s_bias}` ({s_ratio})\n"
            f"• CVD: `{cvd_flow}`\n\n"
            f"🗺 **SESSION ZONES (UTC+7):**\n"
            f"• 🇯🇵 Tokyo: `${sess['Tokyo']['H']:.1f}` - `${sess['Tokyo']['L']:.1f}`\n"
            f"• 🇬🇧 London: `${sess['London']['H']:.1f}` - `${sess['London']['L']:.1f}`\n"
            f"• 🇺🇸 N.York: `${sess['New York']['H']:.1f}` - `${sess['New York']['L']:.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Check SFP at these Levels!*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] ALERTS (Topic 18) ---
    curr = df_m5['Close'].iloc[-1]
    # Check Sweep រាល់ Session ទាំងអស់
    for s_name, prices in sess.items():
        if prices['H'] == 0: continue
        # Sweep High
        if df_m5['High'].iloc[-1] > prices['H'] and curr < prices['H']:
            msg = f"🚨 **SFP: {s_name.upper()} HIGH SWEEP**\n💰 Price: `${curr:,.2f}`\n📊 CVD: `{cvd_flow}`\n🧠 {s_bias}"
            send_telegram(msg, TOPIC_ALERTS)
        # Sweep Low
        elif df_m5['Low'].iloc[-1] < prices['L'] and curr > prices['L']:
            msg = f"🚨 **SFP: {s_name.upper()} LOW SWEEP**\n💰 Price: `${curr:,.2f}`\n📊 CVD: `{cvd_flow}`\n🧠 {s_bias}"
            send_telegram(msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
        
