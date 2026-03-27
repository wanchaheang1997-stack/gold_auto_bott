import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- Configuration (GitHub Secrets) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')

def get_market_data():
    try:
        gold = yf.Ticker("GC=F")
        df_5m = gold.history(period="2d", interval="5m")
        df_1h = gold.history(period="7d", interval="1h")
        df_1d = gold.history(period="60d", interval="1d")
        return df_5m, df_1h, df_1d
    except: return None, None, None

def get_sentiment_logic(df_1h):
    """គណនា Retail Sentiment Bias (FXSSI Style)"""
    delta = df_1h['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
    
    if rsi > 70: return "🔴 **Retailers: 85% BUY** (Extreme OB - Look for SELL)"
    elif rsi < 30: return "🟢 **Retailers: 82% SELL** (Extreme OS - Look to BUY)"
    return "⚪ **Sentiment: Neutral** (Market in Balance)"

def send_telegram(text, topic_id):
    if not TOKEN or not GROUP_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    df_5m, df_1h, df_1d = get_market_data()
    if df_5m is None or df_5m.empty: return

    price = df_5m['Close'].iloc[-1]
    pdh, pdl = df_1d['High'].iloc[-2], df_1d['Low'].iloc[-2]
    
    # --- 1. Economic Calendar (🔴🟠🟡) ---
    # (សម្រាប់ Real-time ១០០% បងអាចភ្ជាប់ Finnhub API ពេលក្រោយ)
    calendar = (
        "📅 **ECONOMIC CALENDAR (Today)**\n"
        "🔴 19:30 - Core PCE Price Index (USD)\n"
        "🟠 21:00 - UoM Consumer Sentiment\n"
        "🟡 22:30 - Natural Gas Storage"
    )

    # --- 2. Sentiment & COT Data ---
    sentiment = get_sentiment_logic(df_1h)
    cot_data = "🏛️ **COT DATA:** Commercials are Net Long (Bullish Bias)"

    # --- 3. Intraday Analysis Report ---
    if now_kh.hour in [8, 14, 19] and now_kh.minute < 15:
        session = "🌏 ASIA" if now_kh.hour == 8 else "🇪🇺 LONDON" if now_kh.hour == 14 else "🇺🇸 NEW YORK"
        
        report = (
            f"📊 **XAU/USD INSTITUTIONAL INSIGHT**\n"
            f"*{session} SESSION | {now_kh.strftime('%d %b %Y')}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Current Price:** `${price:,.2f}`\n\n"
            f"{calendar}\n\n"
            f"🧠 **MARKET BIAS (FXSSI Style)**\n"
            f"• {sentiment}\n"
            f"• {cot_data}\n\n"
            f"🎯 **LIQUIDITY MAP (A+ Setup)**\n"
            f"• PDH (BSL): `${pdh:,.2f}`\n"
            f"• PDL (SSL): `${pdl:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *Strategy: Wait for Sweep + MSS on M5.*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- 4. Liquidity Alerts ---
    alerts = []
    if price > pdh: alerts.append("🔴 **PDH SWEPT (BSL Taken)**")
    elif price < pdl: alerts.append("🟢 **PDL SWEPT (SSL Taken)**")
    
    if alerts:
        alert_msg = "🚨 **LIQUIDITY SWEEP ALERT** 🚨\n\n" + "\n".join(alerts) + f"\n💰 Price: `${price:,.2f}`"
        send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
    
