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
        # 1. Fundamental (Yields & Ratios)
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        gold = yf.Ticker("GC=F").history(period="2d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="2d")['Close'].iloc[-1]
        gs_ratio = gold / silver
        
        # 2. Sentimental Approximation (ប្រើកម្លាំង RSI ធ្វើជាតំណាង Retail Sentiment)
        # បើ RSI ខ្ពស់ Retail ចូលចិត្តលក់ (Contrarian)
        g_ticker = yf.Ticker("GC=F")
        hist = g_ticker.history(period="5d", interval="1h")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        sentiment_val = rsi.iloc[-1]
        # Logic Sentiment: RSI > 60 = Retail Buying, RSI < 40 = Retail Selling
        if sentiment_val > 60:
            s_text = "Retail Bias: BUYING 🟢"
            s_detail = f"{int(sentiment_val)}% / {100-int(sentiment_val)}%"
        else:
            s_text = "Retail Bias: SELLING 🔴"
            s_detail = f"{100-int(sentiment_val)}% / {int(sentiment_val)}%"
            
        return tnx, gs_ratio, s_text, s_detail
    except:
        return 0.0, 0.0, "Sentiment: N/A", "50% / 50%"

def get_cvd_bias(df_m5):
    df_m5 = df_m5.copy()
    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd = df_m5['Delta'].tail(12).sum()
    bias = "Aggressive Buying 🟢" if cvd > 0 else "Aggressive Selling 🔴"
    return cvd, bias

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

# ========================================
# 🚀 THE COMPLETE RUNNER (V10.3)
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="5d", interval="1h")
    df_m5 = gold.history(period="2d", interval="5m")
    
    if df_h1.empty or df_m5.empty: return

    yield_10y, gs_ratio, s_bias, s_ratio = get_macro_and_sentiment()
    cvd_val, cvd_flow = get_cvd_bias(df_m5)
    
    tokyo_h = df_h1.between_time('00:00', '07:00')['High'].max()
    tokyo_l = df_h1.between_time('00:00', '07:00')['Low'].min()
    current_price = df_m5['Close'].iloc[-1]

    # --- [A] INSTITUTIONAL REPORT (Topic 8) ---
    if now_kh.hour in [8, 11, 14, 15, 19, 21]:
        report = (
            f"🏛 **SOVEREIGN COMPLETE REPORT**\n"
            f"📅 `{now_kh.strftime('%d %b | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **FUNDAMENTALS:**\n"
            f"• US 10Y Yield: `{yield_10y:.2f}%`\n"
            f"• Gold/Silver: `{gs_ratio:.2f}`\n\n"
            f"🧠 **SENTIMENT (RETAIL):**\n"
            f"• `{s_bias}`\n"
            f"• Ratio: `{s_ratio}`\n\n"
            f"🔥 **ORDER FLOW (CVD):**\n"
            f"• Bias: `{cvd_flow}`\n"
            f"• Strength: `{abs(cvd_val):,.0f}`\n\n"
            f"🗺 **INTRADAY ZONES:**\n"
            f"• Tokyo High: `${tokyo_h:,.1f}`\n"
            f"• Tokyo Low: `${tokyo_l:,.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Full Data Active*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] ALERTS (Topic 18) ---
    last_m5 = df_m5.iloc[-1]
    if last_m5['High'] > tokyo_h and last_m5['Close'] < tokyo_h:
        msg = f"🚨 **SFP: TOKYO HIGH SWEEP**\n💰 Price: `${current_price:,.2f}`\n📊 CVD: `{cvd_flow}`\n🧠 {s_bias}"
        send_telegram(msg, TOPIC_ALERTS)
    elif last_m5['Low'] < tokyo_l and last_m5['Close'] > tokyo_l:
        msg = f"🚨 **SFP: TOKYO LOW SWEEP**\n💰 Price: `${current_price:,.2f}`\n📊 CVD: `{cvd_flow}`\n🧠 {s_bias}"
        send_telegram(msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
        
