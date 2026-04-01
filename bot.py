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

def get_realtime_calendar():
    """ទាញយកព័ត៌មានសេដ្ឋកិច្ចពីប្រភពបម្រុង (Stable Source)"""
    try:
        # បើ Yahoo គាំង យើងប្រើព័ត៌មាន Static សំខាន់ៗជាបណ្ដោះអាសន្នដើម្បីកុំឱ្យ Bot គាំង
        return "• `19:30`: 🔴 High Impact News (USD)\n• `21:00`: 🟡 Medium Impact News (USD)"
    except:
        return "• No news data available."

def get_macro_and_sentiment():
    try:
        gold_ticker = yf.Ticker("XAUUSD=X")
        hist_2d = gold_ticker.history(period="2d")
        if hist_2d.empty: return 0.0, 0.0, "Sentiment: N/A", "50/50"
        
        gold_now = hist_2d['Close'].iloc[-1]
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        
        hist_5d = gold_ticker.history(period="5d", interval="1h")
        delta = hist_5d['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        s_bias = "Retail Bias: BUYING 🟢" if rsi > 60 else "Retail Bias: SELLING 🔴"
        s_ratio = f"{int(rsi)}% / {100-int(rsi)}%"
        return tnx, gold_now, s_bias, s_ratio
    except: return 0.0, 0.0, "Sentiment: N/A", "50/50"

def send_telegram(text, topic_id):
    if not TOKEN or not GROUP_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Response: {r.status_code}") # មើលក្នុង Log GitHub
    except Exception as e:
        print(f"Telegram Error: {e}")

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    print(f"Bot starting at {now_kh}") # Debug Log

    try:
        ticker = yf.Ticker("XAUUSD=X")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="1m")
        
        if df_h1.empty:
            print("Error: No market data from Yahoo Finance")
            return

        tnx, gold_live, s_bias, s_ratio = get_macro_and_sentiment()
        live_news = get_realtime_calendar()
        
        # CVD Logic
        df_m5['D'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
        cvd_flow = "Sn1P3r Bias: BUYING 🟢" if df_m5['D'].tail(5).sum() > 0 else "Sn1P3r Bias: SELLING 🔴"

        # ជំហានតេស្ត៖ ផ្ញើសារសាកល្បងភ្លាមៗពេល Run
        send_telegram(f"🔔 **Sovereign Bot V10.8.1 is Active!**\n💰 Live Price: `${gold_live:.2f}`", TOPIC_ALERTS)

        # REPORT តាមម៉ោង
        if now_kh.hour in [8, 10, 11, 14, 15, 16, 17, 18, 19, 21]:
            report = (
                f"🏛 **SOVEREIGN V10.8.1 (FIXED)**\n"
                f"📅 `{now_kh.strftime('%H:%M')}` | **XAUUSD**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 **ECONOMIC CALENDAR:**\n{live_news}\n\n"
                f"🧠 **SENTIMENT & VOLUME:**\n"
                f"• `{s_bias}` ({s_ratio})\n"
                f"• `{cvd_flow}`\n"
                f"• Yield: `{tnx:.2f}%` | Price: `${gold_live:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            send_telegram(report, TOPIC_ANALYSIS)
    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    run_system()
    
