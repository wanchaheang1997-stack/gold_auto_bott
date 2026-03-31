import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime

# ========================================
# ⚙️ SUPREME CONFIGURATION
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

# ========================================
# 🛡️ THE TRIPLE-THREAT & MACRO ENGINE
# ========================================

def get_volume_profile_poc(df_h1):
    """ រក POC - តំបន់មេដែកទាញតម្លៃ (ពី V6) """
    bins = 30
    df_h1['bin'] = pd.cut(df_h1['Close'], bins=bins)
    poc_bin = df_h1.groupby('bin')['Volume'].sum().idxmax()
    return (poc_bin.left + poc_bin.right) / 2

def analyze_correlations():
    """ វិភាគ DXY, Silver និង SMT Trap (ពី V7) """
    dxy = yf.Ticker("DX-Y.NYB").history(period="2d", interval="1h")
    silver = yf.Ticker("SI=F").history(period="2d", interval="1h")
    if dxy.empty or silver.empty: return None
    
    # DXY Trend
    dxy_now = dxy['Close'].iloc[-1]
    dxy_prev = dxy['Open'].iloc[-1]
    dxy_trend = "UP 📈 (Pressure on Gold)" if dxy_now > dxy_prev else "DOWN 📉 (Support for Gold)"
    
    return {"dxy": dxy_now, "dxy_trend": dxy_trend, "silver": silver['Close'].iloc[-1]}

def detect_sfp(df_m5, prev_h1_high, prev_h1_low):
    """ ស្កែនរក SFP - ការបោកបញ្ឆោត Liquidity (ពី V6) """
    last_candle = df_m5.iloc[-1]
    if last_candle['High'] > prev_h1_high and last_candle['Close'] < prev_h1_high:
        return "SFP BEARISH (Liquidity Grab) 🔴"
    if last_candle['Low'] < prev_h1_low and last_candle['Close'] > prev_h1_low:
        return "SFP BULLISH (Liquidity Grab) 🟢"
    return None

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

# ========================================
# 🚀 THE SUPREME RUNNER (MIX V6 + V7)
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    # 1. ទាញយកទិន្នន័យ (Gold, DXY, Silver)
    gold_h1 = yf.Ticker("GC=F").history(period="15d", interval="1h")
    gold_m5 = yf.Ticker("GC=F").history(period="5d", interval="5m")
    gold_h4 = yf.Ticker("GC=F").history(period="30d", interval="4h")
    
    if gold_h1.empty: return

    # 2. គណនា Logic សំខាន់ៗ
    current_price = gold_m5['Close'].iloc[-1]
    poc_price = get_volume_profile_poc(gold_h1)
    macro = analyze_correlations()
    
    # វិភាគ Trend ធំ H4
    ma20_h4 = gold_h4['Close'].rolling(20).mean().iloc[-1]
    h4_bias = "BULLISH 🐂" if current_price > ma20_h4 else "BEARISH 🐻"

    # --- [A] SUPREME INTELLIGENCE REPORT (Topic 8) ---
    if h in [8, 11, 14, 19, 21] and m <= 59:
        pdh, pdl = gold_h1['High'].tail(24).max(), gold_h1['Low'].tail(24).min()
        
        # Fundamental News Context (March 31, 2026)
        news_context = "Middle East Tension vs High Fed Rates"
        
        report = (
            f"👑 **HIGHEST SUPREME INTELLIGENCE**\n"
            f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏛️ **MACRO CONTEXT:**\n"
            f"• **DXY Index:** `{macro['dxy']:.2f}` ({macro['dxy_trend']})\n"
            f"• **Silver:** `${macro['silver']:.2f}`\n"
            f"• **News:** `{news_context}`\n\n"
            f"📊 **TECHNICALS (V6+V7):**\n"
            f"• **POC Magnet:** `${poc_price:,.2f}`\n"
            f"• **H4 Bias:** `{h4_bias}`\n"
            f"• **Current Price:** `${current_price:,.2f}`\n\n"
            f"🔍 **LIQUIDITY ZONES:**\n"
            f"🔼 PDH (BuySide): `${pdh:,.2f}`\n"
            f"🔽 PDL (SellSide): `${pdl:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Wait for SFP + SMT Divergence confirmation.*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] HIGHEST SUPREME ALERTS (Topic 18) ---
    prev_h1_high, prev_h1_low = gold_h1['High'].iloc[-2], gold_h1['Low'].iloc[-2]
    sfp_signal = detect_sfp(gold_m5, prev_h1_high, prev_h1_low)

    if sfp_signal:
        # បញ្ជាក់សញ្ញាជាមួយ Macro (Confluence)
        is_valid = False
        if "BEARISH" in sfp_signal and macro['dxy_trend'].startswith("UP"): is_valid = True
        if "BULLISH" in sfp_signal and macro['dxy_trend'].startswith("DOWN"): is_valid = True
        
        if is_valid:
            alert_msg = (
                f"🚨 **SUPREME SFP ALERT: {sfp_signal}**\n"
                f"🏛️ **Macro Confluence:** `DXY Aligned`\n"
                f"📊 **POC Rejection:** `${poc_price:,.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 **ENTRY:** `${current_price:,.2f}`\n"
                f"🛡️ **SL:** `Above/Below SFP Wick`\n"
                f"🎯 **TP:** `${poc_price:,.2f}` (Target POC)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Confirmation: Look for M1 MSS/CHoCH.*"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
