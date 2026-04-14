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

def run_v32_logic():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    if now.weekday() >= 5: return

    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="5d", interval="1h")
        if df.empty: return
        
        curr_p = df['Close'].iloc[-1]
        prev_p = df['Close'].iloc[-2]
        h1_ob_l, h1_ob_h = df['Low'].iloc[-2], df['High'].iloc[-2]

        # --- LOGIC ANALYSIS ---
        trend = "BULLISH 🚀" if curr_p > df['Close'].iloc[-24] else "BEARISH 📉"
        
        # Logic Buy/Sell Advice
        if curr_p >= h1_ob_h:
            logic_move = "⚠️ WAIT FOR REJECTION (SELL SETUP)"
            psy_tip = "កុំដេញ Buy តាមតម្លៃខ្ពស់! Sniper រង់ចាំឱ្យគោលដៅចុះខ្សោយសិន ទើបបាញ់បញ្ច្រាស។"
        elif curr_p <= h1_ob_l:
            logic_move = "✅ LOOK FOR CONFIRMATION (BUY SETUP)"
            psy_tip = "តម្លៃមកដល់តំបន់ទិញហើយ! តែត្រូវរង់ចាំឱ្យមានកម្លាំងទិញត្រឡប់មកវិញ (CHoCH) សិន សឹមចូល។"
        else:
            logic_move = "👀 NO-TRADE ZONE (PATIENCE)"
            psy_tip = "ទីផ្សារកំពុងស្ថិតក្នុងភាពមិនច្បាស់លាស់។ ការមិនចូលជួញដូរ ក៏ជាការចំណេញដូចគ្នា (Protect Capital)។"

        # 1. ALERT LOGIC (Topic 3)
        if h1_ob_l <= curr_p <= h1_ob_h:
            alert_msg = (
                f"🎯 **XAUUSD SNIPER ALERT**\n"
                f"🔥 Price in 1H Zone: `${curr_p:.2f}`\n"
                f"📍 Logic: {logic_move}\n"
                f"💡 Mindset: {psy_tip}"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)

        # 2. ENHANCED REPORT (Topic 2)
        if now.minute < 10:
            report = (
                f"🏛 **E11 GLOBAL INTELLIGENCE V32**\n"
                f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **MARKET ANALYSIS:**\n"
                f"• Trend: {trend}\n"
                f"• OB Zone: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n\n"
                f"🧠 **STRATEGY & PSYCHOLOGY:**\n"
                f"👉 **Action:** {logic_move}\n"
                f"🧘 **Mindset:** _{psy_tip}_\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Wait for the perfect setup!*"
            )
            send_telegram(report, TOPIC_REPORT)

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_v32_logic()
    
