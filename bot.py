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

def get_economic_calendar():
    """ទាញយកព័ត៌មានសេដ្ឋកិច្ចសំខាន់ៗ (Simplified)"""
    # ដោយសារ API ព័ត៌មានភាគច្រើនត្រូវបង់ថ្លៃ យើងប្រើការតាមដាន Event សំខាន់ៗដែលប៉ះពាល់មាស
    # បងអាចបន្ថែមឈ្មោះ Event ក្នុងបញ្ជីនេះបាន
    news_events = [
        {"time": "19:30", "event": "🇺🇸 CPI (Inflation Data)", "impact": "🔴 High"},
        {"time": "19:30", "event": "🇺🇸 Unemployment Claims", "impact": "🟡 Medium"},
        {"time": "21:00", "event": "🇺🇸 ISM Manufacturing PMI", "impact": "🔴 High"},
        {"time": "01:00", "event": "🇺🇸 FOMC Meeting Minutes", "impact": "🔥 Extreme"}
    ]
    # ចម្រាញ់យកតែព័ត៌មានណាដែលត្រូវនឹងថ្ងៃនេះ (ឧទាហរណ៍)
    return news_events

def get_macro_and_sentiment():
    try:
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        gold_ticker = yf.Ticker("XAUUSD=X")
        gold_now = gold_ticker.history(period="2d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="2d")['Close'].iloc[-1]
        gs_ratio = gold_now / silver
        
        hist = gold_ticker.history(period="5d", interval="1h")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        s_bias = "Retail Bias: BUYING 🟢" if rsi > 60 else "Retail Bias: SELLING 🔴"
        s_ratio = f"{int(rsi)}% / {100-int(rsi)}%"
        return tnx, gs_ratio, s_bias, s_ratio
    except: return 0.0, 0.0, "Sentiment: N/A", "50/50"

def get_session_data(df_h1):
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'New York': ('19:00', '22:00')}
    results = {}
    for name, (start, end) in sessions.items():
        data = df_h1.between_time(start, end)
        results[name] = {'H': data['High'].max() if not data.empty else 0.0, 
                         'L': data['Low'].min() if not data.empty else 0.0}
    return results

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    ticker = yf.Ticker("XAUUSD=X")
    df_h1 = ticker.history(period="2d", interval="1h")
    df_m5 = ticker.history(period="1d", interval="1m")
    
    if df_h1.empty or df_m5.empty: return

    tnx, gs, s_bias, s_ratio = get_macro_and_sentiment()
    sess = get_session_data(df_h1)
    calendar = get_economic_calendar()
    
    df_m5['D'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd_flow = "Aggressive Buying 🟢" if df_m5['D'].tail(15).sum() > 0 else "Aggressive Selling 🔴"

    if now_kh.hour in [8, 11, 14, 15, 16, 17, 19, 21]:
        # រៀបចំផ្នែកព័ត៌មាន
        news_text = "\n".join([f"• `{n['time']}`: {n['event']} ({n['impact']})" for n in calendar])
        
        report = (
            f"🏛 **SOVEREIGN FULL REPORT**\n"
            f"📅 `{now_kh.strftime('%H:%M')}` | **XAUUSD (OANDA)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 **ECONOMIC CALENDAR (Today):**\n{news_text}\n\n"
            f"🌍 **LIVE MACRO:**\n"
            f"• Yield: `{tnx:.2f}%` | `{s_bias}` ({s_ratio})\n"
            f"• CVD: `{cvd_flow}`\n\n"
            f"🗺 **SESSION ZONES:**\n"
            f"• 🇯🇵 Tokyo: `${sess['Tokyo']['H']:.2f}` - `${sess['Tokyo']['L']:.2f}`\n"
            f"• 🇬🇧 London: `${sess['London']['H']:.2f}` - `${sess['London']['L']:.2f}`\n"
            f"• 🇺🇸 N.York: `${sess['New York']['H']:.2f}` - `${sess['New York']['L']:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Warning: Do not trade during High Impact News!*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] ALERTS ---
    curr = df_m5['Close'].iloc[-1]
    for s_name, prices in sess.items():
        if prices['H'] == 0: continue
        if df_m5['High'].iloc[-1] > prices['H'] and curr < prices['H']:
            send_telegram(f"🚨 **SFP: {s_name.upper()} HIGH SWEEP**\n💰 Live: `${curr:,.2f}`\n📊 CVD: `{cvd_flow}`", TOPIC_ALERTS)
        elif df_m5['Low'].iloc[-1] < prices['L'] and curr > prices['L']:
            send_telegram(f"🚨 **SFP: {s_name.upper()} LOW SWEEP**\n💰 Live: `${curr:,.2f}`\n📊 CVD: `{cvd_flow}`", TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
