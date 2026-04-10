import os, requests, pytz
from datetime import datetime
from tradingview_ta import TA_Handler, Interval, Exchange

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 8
TOPIC_ALERTS = 18

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def get_tv_analysis(symbol, interval):
    # ទាញទិន្នន័យពី TradingView ផ្ទាល់
    handler = TA_Handler(
        symbol=symbol,
        screener="forex",
        exchange="OANDA", # ឬ TVC សម្រាប់មាស
        interval=interval
    )
    return handler.get_analysis()

def run_v21_tv():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    if now.weekday() >= 5: return

    try:
        # 1. FETCH TV DATA (D1 & H1 & M5)
        # មាសលើ TV ប្រើ XAUUSD
        d1_tv = get_tv_analysis("XAUUSD", Interval.INTERVAL_1_DAY)
        h1_tv = get_tv_analysis("XAUUSD", Interval.INTERVAL_1_HOUR)
        m5_tv = get_tv_analysis("XAUUSD", Interval.INTERVAL_5_MINUTES)
        
        curr_p = m5_tv.indicators["close"]
        
        # --- STEP 1: D1 BIAS (TradingView's EMA 200) ---
        ema200_d1 = d1_tv.indicators["EMA200"]
        d1_bias = "BULLISH" if curr_p > ema200_d1 else "BEARISH"
        d1_rec = d1_tv.summary['RECOMMENDATION']

        # --- STEP 2: H1 STRUCTURE (Zones & Indicators) ---
        h1_rsi = h1_tv.indicators["RSI"]
        # រក Support/Resistance សាមញ្ញពី TV
        h1_pivot = h1_tv.indicators["Pivot.M.Classic.Middle"]

        # --- STEP 3: M5 EXECUTION (Confirmation) ---
        m5_rec = m5_tv.summary['RECOMMENDATION'] # "STRONG_BUY", "BUY", etc.
        m5_fvg = m5_tv.indicators["close"] > m5_tv.indicators["open"] # Simple Bullish Move

        # --- ALIGNMENT LOGIC ---
        signal = None
        # 🔵 BUY: Daily Bull + M5 Strong Buy on TV
        if d1_bias == "BULLISH" and "BUY" in m5_rec:
            signal = "🔵 BUY SNIPER (TV CONFIRMED)"
        
        # 🔴 SELL: Daily Bear + M5 Strong Sell on TV
        elif d1_bias == "BEARISH" and "SELL" in m5_rec:
            signal = "🔴 SELL SNIPER (TV CONFIRMED)"

        # --- TOPIC 18: ALERT ---
        if signal:
            msg = (f"🎯 **{signal}**\n"
                   f"🌍 D1 Bias: {d1_bias} ({d1_rec})\n"
                   f"🔭 H1 RSI: {h1_rsi:.2f}\n"
                   f"📊 M5 TV Signal: {m5_rec}\n"
                   f"💰 Price: `${curr_p:.2f}`\n"
                   f"🛡 SL: Below Structure | TP: 1:2 / 1:3")
            send_telegram(msg, TOPIC_ALERTS)

        # --- TOPIC 8: REPORT ---
        if 8 <= now.hour <= 22:
            report = (
                f"🏛 **E11 TV-INTELLIGENCE V21.0**\n"
                f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📈 **1. TRADINGVIEW D1 BIAS:**\n"
                f"• Recommendation: **{d1_rec}**\n"
                f"• EMA 200: `${ema200_d1:.2f}`\n\n"
                f"🔭 **2. H1 CONTEXT:**\n"
                f"• RSI: {h1_rsi:.2f}\n• Pivot: `${h1_pivot:.2f}`\n\n"
                f"📊 **3. TECHNICAL CHECKLIST:**\n"
                f"• M5 TV Signal: {m5_rec}\n"
                f"• Trend Alignment: {'✅ ALIGNED' if d1_bias in m5_rec else '❌ CONFLICT'}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Direct TV Data Link Active!*"
            )
            send_telegram(report, TOPIC_REPORT)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_v21_tv()
                     
