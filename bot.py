import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 2
TOPIC_ALERTS = 3

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def get_market_insight():
    # ក្នុងឆ្នាំ ២០២៦ មាសកំពុងរងឥទ្ធិពលពីភូមិសាស្ត្រនយោបាយ និងអត្រាការប្រាក់ Fed
    gold = yf.download('GC=F', period='5d', interval='1h')
    curr_p = gold['Close'].iloc[-1]
    pdh, pdl = gold['High'].iloc[-2], gold['Low'].iloc[-2]
    
    # វិភាគដោយប្រើ Logic ជំនួយ
    bias = "BULLISH ↗️" if curr_p > pdh else "BEARISH ↘️" if curr_p < pdl else "NEUTRAL ↔️"
    
    # Fundamental & Sentiment (Simulated Insight based on 2026 Context)
    insight = (
        "• *Sentiment:* កម្លាំងទិញនៅតែខ្លាំងក្នុងតំបន់ $4,800.\n"
        "• *Fundamental:* ការរំពឹងទុកលើការបញ្ចុះអត្រាការប្រាក់ Fed (33% Odds).\n"
        "• *World News:* បញ្ហាសន្តិភាព US-Iran កំពុងធ្វើឱ្យមាសមានចលនាខ្លាំង."
    )
    return curr_p, pdh, pdl, bias, insight

def run_v37_intelligence():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    if now.weekday() >= 5: return

    try:
        price, pdh, pdl, bias, insight = get_market_insight()

        # 1. TOPIC REPORT (Insight & Levels)
        if now.minute < 10:
            report = (
                f"🏛 **E11 GLOBAL INTELLIGENCE V37**\n"
                f"⏰ `{now.strftime('%H:%M')} | Price: ${price:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 **MARKET INSIGHT:**\n{insight}\n\n"
                f"📊 **ANALYSIS:**\n"
                f"• Bias: {bias}\n"
                f"• PDH (Resistance): `${pdh:.2f}`\n"
                f"• PDL (Support): `${pdl:.2f}`\n\n"
                f"📅 **CALENDAR:**\n- USD High Impact News (Check 19:30)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Plan your trade, trade your plan!*"
            )
            send_telegram(report, TOPIC_REPORT)

        # 2. SNIPER ALERT (Topic 3)
        # បន្ថែម Logic ប៉ះ PDH/PDL ឱ្យ Alert ខ្លាំងៗ
        if price >= pdh or price <= pdl:
            alert = f"🎯 **SNIPER ALERT: KEY LEVEL HIT!**\n💰 Price: `${price:.2f}`\n📍 Level: {'PDH (Breakout?)' if price >= pdh else 'PDL (Bounce?)'}"
            send_telegram(alert, TOPIC_ALERTS)

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_v37_intelligence()
    
