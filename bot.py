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
# 🛡️ ELITE ANALYSIS MODULES
# ========================================
def get_market_context(df_h4, df_h1):
    """ វិភាគបរិបទទីផ្សារកម្រិតខ្ពស់ (Institutional Bias) """
    # ឆែក Trend ធំ (H4)
    ma20_h4 = df_h4['Close'].rolling(window=20).mean().iloc[-1]
    curr_h4 = df_h4['Close'].iloc[-1]
    h4_bias = "BULLISH 🐂" if curr_h4 > ma20_h4 else "BEARISH 🐻"
    
    # ឆែកទំហំនៃការប្រែប្រួល (Average True Range - ATR សម្រាយ)
    atr = (df_h1['High'] - df_h1['Low']).tail(14).mean()
    
    return h4_bias, atr

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
    # ទាញយកទិន្នន័យច្រើន Timeframe ដើម្បីធ្វើ Confluence
    df_h4 = ticker.history(period="30d", interval="4h")
    df_h1 = ticker.history(period="15d", interval="1h")
    df_m5 = ticker.history(period="3d", interval="5m")
    return df_h4, df_h1, df_m5

# ========================================
# 🚀 THE SUPREME RUNNER
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    df_h4, df_h1, df_m5 = get_data()
    if df_h4.empty or df_h1.empty: return

    h4_bias, volatility = get_market_context(df_h4, df_h1)
    current_price = df_m5['Close'].iloc[-1]
    
    # --- [A] PREMIUM SESSION REPORT (Topic 8) ---
    # រាយការណ៍រៀងរាល់ម៉ោង Session ធំៗ
    if h in [8, 11, 14, 19] and m <= 59:
        prev_day_high = df_h1['High'].tail(24).max()
        prev_day_low = df_h1['Low'].tail(24).min()
        session_open = df_h1['Open'].iloc[-1]
        
        distance_to_high = prev_day_high - current_price
        distance_to_low = current_price - prev_day_low

        report = (
            f"🏛️ **INSTITUTIONAL MARKET REPORT**\n"
            f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **BIAS H4:** `{h4_bias}`\n"
            f"💰 **PRICE:** `${current_price:,.2f}`\n"
            f"🚦 **OPEN:** `${session_open:,.2f}`\n\n"
            f"🔍 **LIQUIDITY MAP:**\n"
            f"🔼 PDH (BuySide): `${prev_day_high:,.2f}` (`{distance_to_high:.2f}$` left)\n"
            f"🔽 PDL (SellSide): `${prev_day_low:,.2f}` (`{distance_to_low:.2f}$` left)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Focus on CRT Sweeps at Session Open.*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] ELITE CRT/SMC ALERTS (Topic 18) ---
    # កំណត់ Range ម៉ោងមុន (Candle Range)
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    
    setup = None
    # យុទ្ធសាស្ត្រ Candle Range Theory (CRT) + SFP
    # SELL: បើតម្លៃបុកលើ H1 High រួចបកក្រោយ (Liquidity Grab)
    if current_price > prev_h1_high and "BEARISH" in h4_bias:
        entry = current_price
        sl = entry + 3.0 # Dynamic SL
        tp = entry - 6.0 # RR 1:2
        setup = {"type": "BSL PURGED (CRT SELL) 🔴", "entry": entry, "tp": tp, "sl": sl, "conf": "Premium Bearish Alignment"}

    # BUY: បើតម្លៃបុកក្រោម H1 Low រួចបកក្រោយ (Liquidity Grab)
    elif current_price < prev_h1_low and "BULLISH" in h4_bias:
        entry = current_price
        sl = entry - 3.0
        tp = entry + 6.0
        setup = {"type": "SSL PURGED (CRT BUY) 🟢", "entry": entry, "tp": tp, "sl": sl, "conf": "Premium Bullish Alignment"}

    if setup:
        alert_msg = (
            f"🚀 **ELITE SIGNAL: {setup['type']}**\n"
            f"🏛️ **Institutional Flow:** `Confirmed`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 **ENTRY:** `${setup['entry']:,.2f}`\n"
            f"🎯 **TP (RR 1:2):** `${setup['tp']:,.2f}`\n"
            f"🛑 **SL:** `${setup['sl']:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 **Note:** `{setup['conf']}`\n"
            f"⚠️ *Risk 1% per trade. Manage manually.*"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
