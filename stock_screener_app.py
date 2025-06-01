import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt

st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")
st.title("📈 Hisse Analiz")

# RSI hesaplama
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD hesaplama
def calculate_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# MACD yorum
def generate_macd_commentary(macd_line, signal_line):
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        return "MACD Al sinyali verdi."
    elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        return "MACD Sat sinyali verdi."
    else:
        return "MACD nötr durumda."

# RSI + MA + hacim yorum
def generate_commentary(rsi, volume_ratio, close, ma20, ma50):
    commentary = []
    if rsi >= 70:
        commentary.append("RSI aşırı alım bölgesinde.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda.")
    else:
        commentary.append("RSI nötr bölgede.")
    if volume_ratio > 1.5:
        commentary.append("Hacim ortalamanın üzerinde.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük.")
    else:
        commentary.append("Hacim ortalama seviyede.")
    if close > ma20 > ma50:
        commentary.append("Trend pozitif.")
    elif close < ma20 < ma50:
        commentary.append("Trend zayıf.")
    else:
        commentary.append("Fiyat ortalamalara yakın.")
    commentary.append("⚠️ Yatırım tavsiyesi değildir.")
    return " ".join(commentary)

# Grafik çiz
def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})
    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")
    ax1.plot(data.index, data["EMA89"], label="EMA89", color="magenta", linestyle="--")
    ax1.set_title(f"{ticker_name} - Son 1 Yıl")
    ax1.legend(); ax1.grid(True)
    ax2.plot(data.index, data["RSI"], label="RSI", color="purple")
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    ax2.legend(); ax2.grid(True)
    ax3.plot(data.index, data["MACD_Line"], label="MACD", color="blue")
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange")
    ax3.bar(data.index, data["MACD_Hist"], color="gray", alpha=0.4)
    ax3.legend(); ax3.grid(True)
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# Detaylı veri hazırlanması
def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        return None
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["EMA89"] = data["Close"].ewm(span=89, adjust=False).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    macd_line, signal_line, histogram = calculate_macd(data["Close"])
    data["MACD_Line"] = macd_line
    data["MACD_Signal"] = signal_line
    data["MACD_Hist"] = histogram
    return data

# Hisse tarama fonksiyonu
def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_volume):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()
            data["RSI"] = calculate_rsi(data["Close"])
            close = float(data["Close"].iloc[-1])
            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            is_near_ma = close < min(ma20, ma50, ma200) * (1 + ma_tolerance)
            passes_ma = is_near_ma if use_ma else True
            passes_volume = volume_ratio >= volume_threshold if use_volume else True
            if passes_ma and passes_volume:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Kapanış": round(close, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "RSI": round(data["RSI"].iloc[-1], 2),
                    "Hacim Katsayısı": round(volume_ratio, 2)
                })
        except:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# Sidebar filtreler
st.sidebar.header("🔧 Filtreler")
ma_tolerance = st.sidebar.slider("MA Yakınlık (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Eşiği", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Filtresi", True)
use_volume = st.sidebar.checkbox("Hacim Filtresi", True)
all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("Hisseler", options=all_tickers)

# USDTRY kurunu al
try:
    usdtry = yf.Ticker("USDTRY=X").info.get("regularMarketPrice", None)
except:
    usdtry = None

# Taramayı başlat
if st.button("🔍 Tara"):
    with st.spinner("Tarama yapılıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        df = scan_stocks(tickers_to_scan, ma_tolerance, volume_threshold, use_ma, use_volume)
        if df.empty:
            st.warning("Kriterlere uygun hisse bulunamadı.")
        else:
            for _, row in df.iterrows():
                hisse = row['Hisse']
                ticker_full = hisse + ".IS"
                info = {}
                try:
                    info = yf.Ticker(ticker_full).info
                except:
                    pass

                market_cap = info.get("marketCap", None)
                market_cap_usd = market_cap / usdtry if (market_cap and usdtry) else None
                mcap_str = f"{market_cap_usd / 1e9:.2f} Milyar $" if market_cap_usd else "N/A"
                target_price = info.get("targetMeanPrice", None)
                recommendation = info.get("recommendationKey", None)
                analyst_count = info.get("numberOfAnalystOpinions", None)

                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin:10px 0;">
                    <b>{hisse}</b><br>
                    Kapanış: {row['Kapanış']} ₺<br>
                    RSI: {row['RSI']} | Hacim Katsayısı: {row['Hacim Katsayısı']}<br>
                    MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                    Piyasa Değeri: <b>{mcap_str}</b><br>
                    Hedef Fiyat: <b>{target_price:.2f} ₺</b> | Analist Görüşü: <b>{recommendation.capitalize() if recommendation else 'N/A'}</b> ({analyst_count} analist)
                </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    macd_comment = generate_macd_commentary(data_plot["MACD_Line"], data_plot["MACD_Signal"])
                    st.markdown(f"📉 <b>MACD:</b> {macd_comment}", unsafe_allow_html=True)
                    st.markdown(f"<i>{generate_commentary(row['RSI'], row['Hacim Katsayısı'], row['Kapanış'], row['MA20'], row['MA50'])}</i>", unsafe_allow_html=True)
                    plot_stock_chart(data_plot, hisse)
