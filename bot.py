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

# ========================================
# 🌍 FUNDAMENTAL & SENTIMENT ENGINE
# ========================================
def get_economic_calendar():
    """ ត្រួតពិនិត្យព័ត៌មានសេដ្ឋកិច្ចសំខាន់ៗ (Simulated for Gold) """
    # ក្នុងនាមជា Bot យើងផ្ដោតលើ USD News
    events = [
        {"time": "19:30", "event": "Core PCE Price Index", "impact": "HIGH 🔴"},
        {"time": "21:00", "event": "Fed Chair Powell Speaks", "impact": "CRITICAL 🔥"}
    ]
    return events

def get_market_sentiment(df_h1):
    """ គណនា Retail Sentiment តាមរយៈ RSI & Price Action """
    # ប្រើ RSI ដើម្បីស្មានពី Sentiment (Overbought = Sell Sentiment, Oversold = Buy Sentiment)
    delta = df_h1['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1+rs))
    curr_rsi = rsi.iloc[-1]
    
    if curr_rsi > 70: return "EXTREME BULLISH (Retail Buying) 🐂"
    if curr_rsi < 30: return "EXTREME BEARISH (Retail Selling) 🐻"
    return "NEUTRAL (Waiting for Breakout) ⚖️"

# ========================================
# 🤖 TELEGRAM ACTIONS
# ========================================
def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

# ========================================
# 📊 DATA ENGINE
# ========================================
def get_data():
    ticker = yf.Ticker("GC=F")
    df_h4 = ticker.history(period="30d", interval="4h")
    df_h1 = ticker.history(period="15d", interval="1h")
    df_m5 = ticker.history(period="3d", interval="5m")
    return df_h4, df_h1, df_m5

# ========================================
# 🚀 THE SUPREME RUNNER V5
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    df_h4, df_h1, df_m5 = get_data()
    if df_h4.empty or df_h1.empty: return

    current_price = df_m5['Close'].iloc[-1]
    sentiment = get_market_sentiment(df_h1)
    news_events = get_economic_calendar()
    
    # គណនា Trend H4
    ma20_h4 = df_h4['Close'].rolling(window=20).mean().iloc[-1]
    h4_bias = "BULLISH 🐂" if current_price > ma20_h4 else "BEARISH 🐻"

    # --- [A] ELITE PREMIUM REPORT (Topic 8) ---
    if h in [8, 11, 14, 17, 19, 21] and m <= 59:
        pdh = df_h1['High'].tail(24).max()
        pdl = df_h1['Low'].tail(24).min()
        session_open = df_h1['Open'].iloc[-1]
        
        # ផ្នែក Fundamental News
        news_text = ""
        for ev in news_events:
            news_text += f"• `{ev['time']}`: {ev['event']} ({ev['impact']})\n"

        report = (
            f"🏆 **GOLD SUPREME INTELLIGENCE**\n"
            f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **FUNDAMENTAL & NEWS**\n"
            f"{news_text}"
            f"📊 **SENTIMENT:** `{sentiment}`\n\n"
            f"🏛️ **INSTITUTIONAL CONTEXT**\n"
            f"• **H4 Trend:** `{h4_bias}`\n"
            f"• **Session Open:** `${session_open:,.2f}`\n"
            f"• **Current Price:** `${current_price:,.2f}`\n\n"
            f"🔍 **LIQUIDITY MAP (CRT)**\n"
            f"🔼 PDH (BuySide): `${pdh:,.2f}`\n"
            f"🔽 PDL (SellSide): `${pdl:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Advice: Trade only during Killzones.*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] CRT ALERTS (Topic 18) ---
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    
    setup = None
    # SELL Logic: Sweep High + Bearish Bias
    if current_price > prev_h1_high and "BEARISH" in h4_bias:
        setup = {"type": "BSL SWEEP (CRT SELL) 🔴", "entry": current_price, "sl": current_price + 3.0, "tp": current_price - 6.0}
    # BUY Logic: Sweep Low + Bullish Bias
    elif current_price < prev_h1_low and "BULLISH" in h4_bias:
        setup = {"type": "SSL SWEEP (CRT BUY) 🟢", "entry": current_price, "sl": current_price - 3.0, "tp": current_price + 6.0}

    if setup:
        alert_msg = (
            f"🚨 **ELITE SIGNAL: {setup['type']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 **ENTRY:** `${setup['entry']:,.2f}`\n"
            f"🎯 **TP:** `${setup['tp']:,.2f}`\n"
            f"🛑 **SL:** `${setup['sl']:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Risk 1% - Wait for M5 CHoCH*"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
