import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- ទាញយកតម្លៃពី GitHub Secrets ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_ID")

# --- កំណត់ Topic IDs (Thread IDs) ---
TOPIC_ANALYSIS = 8   # សម្រាប់ Daily Report
TOPIC_ALERTS = 18    # សម្រាប់ SMC Smart Alerts

SYMBOL = "GC=F" # XAU/USD Gold Futures (YFinance)

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "message_thread_id": topic_id
    }
    try:
        r = requests.post(url, json=payload)
        return r.json()
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

class SMCLogic:
    @staticmethod
    def fetch_data(interval):
        return yf.download(SYMBOL, period="2d", interval=interval, progress=False)

    @staticmethod
    def detect_sfp(df):
        """ស្វែងរក Liquidity Sweep (SFP) នៅលើ M15"""
        if len(df) < 20: return None
        last = df.iloc[-1]
        lookback = df.iloc[-25:-2] 
        p_high, p_low = lookback['High'].max(), lookback['Low'].min()

        # Bearish SFP (Sweep High)
        if last['High'] > p_high and last['Close'] < p_high:
            return {"type": "SFP (BSL Swept)", "level": p_high, "bias": "SELL"}
        # Bullish SFP (Sweep Low)
        if last['Low'] < p_low and last['Close'] > p_low:
            return {"type": "SFP (SSL Swept)", "level": p_low, "bias": "BUY"}
        return None

    @staticmethod
    def get_market_bias(df):
        """រកមើលតំបន់ Premium/Discount"""
        high = df['High'].iloc[-40:].max()
        low = df['Low'].iloc[-40:].min()
        mid = (high + low) / 2
        current = df['Close'].iloc[-1]
        return "Premium (Sell Zone)" if current > mid else "Discount (Buy Zone)"

def run_bot():
    smc = SMCLogic()
    
    # 1. ទាញទិន្នន័យ (H1 សម្រាប់ Structure, M15 សម្រាប់ Sweep)
    df_h1 = smc.fetch_data("1h")
    df_m15 = smc.fetch_data("15m")
    
    if df_h1.empty or df_m15.empty:
        print("❌ No data fetched")
        return

    current_price = df_h1['Close'].iloc[-1]
    market_bias = smc.get_market_bias(df_h1)

    # --- ផ្នែកទី ១: ផ្ញើ REPORT ទៅ Topic 8 ---
    report_text = (
        f"📊 *XAUUSD INSTITUTIONAL ANALYSIS*\n"
        f"————————————————\n"
        f"🇰🇭 *របាយការណ៍ទីផ្សារមាស (Session Update)*\n"
        f"• តម្លៃបច្ចុប្បន្ន: `${current_price:.2f}`\n"
        f"• Market Bias: *{market_bias}*\n"
        f"• Session Time: {datetime.now().strftime('%H:%M')} (GMT+7)\n\n"
        f"💡 *SMC Note:* តម្លៃកំពុងស្ថិតក្នុងតំបន់ {market_bias}។ "
        f"រង់ចាំការធ្វើ Liquidity Sweep មុននឹងសម្រេចចិត្តចូល Order។"
    )
    send_telegram(report_text, TOPIC_ANALYSIS)

    # --- ផ្នែកទី ២: ឆែករក ALERT ទៅ Topic 18 ---
    setup = smc.detect_sfp(df_m15)
    if setup:
        # បញ្ជាក់បន្ថែមជាមួយ Market Bias (Sell តែនៅ Premium, Buy តែនៅ Discount)
        if (setup['bias'] == "SELL" and "Premium" in market_bias) or \
           (setup['bias'] == "BUY" and "Discount" in market_bias):
            alert_text = (
                f"🚨 *XAUUSD SMART ALERT*\n\n"
                f"*Type:* {setup['type']}\n"
                f"*Bias:* {setup['bias']} 🔴\n"
                f"*Key Level:* ${setup['level']:.2f}\n\n"
                f"💬 *Institutional Comment:* តម្លៃបានធ្វើការ Sweep Liquidity រួចរាល់ក្នុងតំបន់ {market_bias}។ "
                f"សូមរង់ចាំមើល M5 CHoCH ឬ Rejection candle មុននឹងចូល Entry។"
            )
            send_telegram(alert_text, TOPIC_ALERTS)

if __name__ == "__main__":
    run_bot()
    
