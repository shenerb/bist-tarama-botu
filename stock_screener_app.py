import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers

st.set_page_config(page_title="BIST Gelişmiş Tarayıcı", layout="wide")
st.title("📈 Gelişmiş BIST Dip & Hacim & Teknik Analiz Tarayıcısı")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def detect_support_resistance(prices, window=20):
    support = prices.rolling(window).min()
    resistance = prices.rolling(window).max()
    return support, resistance

def plot_advanced_chart(data, ticker_name):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue", linewidth=2)
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange", linestyle="--")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green", linestyle="--")
    ax1.plot(data.index, data["Support"], label="Destek", color="gray", linestyle=":")
    ax1.plot(data.index, data["Resistance"], label="Direnç", color="black", linestyle=":")

    ax1.set_title(f"{ticker_name} - Gelişmiş Grafik")
    ax1.set_ylabel("Fiyat")
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(data.index, data["RSI"], label="RSI", color="purple", alpha=0.5)
    ax2.fill_between(data.index, 70, 30, color="purple", alpha=0.05)
    ax2.set_ylabel("RSI")

    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(("axes", 1.1))
    ax3.bar(data.index, data["Volume"], label="Hacim", color="gray", alpha=0.3)
    ax3.set_ylabel("Hacim")

    fig.tight_layout()
    st.pyplot(fig)
    plt.clf()

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        return None

    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    data["Support"], data["Resistance"] = detect_support_resistance(data["Close"])
    return data.dropna()

def generate_commentary(rsi, volume_ratio, close, ma20, ma50):
    commentary = []

    if rsi >= 70:
        commentary.append("RSI aşırı alımda. Düzeltme riski olabilir.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda. Tepki yükselişi olabilir.")
    else:
        commentary.append("RSI nötr seviyede.")

    if volume_ratio > 1.5:
        commentary.append("Hacim yüksek. İlgi artmış olabilir.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük. Sinyaller zayıf olabilir.")
    else:
        commentary.append("Hacim ortalama seviyede.")

    if close > ma20 > ma50:
        commentary.append("Trend pozitif. Alım baskısı var.")
    elif close < ma20 < ma50:
        commentary.append("Trend negatif. Dikkatli olunmalı.")
    else:
        commentary.append("Trend kararsız. Net yön yok.")

    return " ".join(commentary)

# Sidebar
st.sidebar.header("Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Eşiği (kat)", 1.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Filtresi Kullan", value=True)

if st.button("Taramayı Başlat"):
    tickers = get_all_bist_tickers()

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue

            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["AvgVolume"] = data["Volume"].rolling(20).mean()

            close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            volume = data["Volume"].iloc[-1]
            avg_volume = data["AvgVolume"].iloc[-1]
            volume_ratio = volume / avg_volume if avg_volume else 0
            rsi = calculate_rsi(data["Close"]).iloc[-1]

            passes_ma = close < ma20 * (1 + ma_tolerance) or close < ma50 * (1 + ma_tolerance) if use_ma else True
            passes_volume = volume_ratio >= volume_threshold

            if passes_ma and passes_volume:
                st.subheader(f"{ticker.replace('.IS', '')} | RSI: {rsi:.2f} | Hacim Katsayısı: {volume_ratio:.2f}")
                data_plot = prepare_data_for_plot(ticker)
                if data_plot is not None:
                    plot_advanced_chart(data_plot, ticker.replace(".IS", ""))
                    comment = generate_commentary(rsi, volume_ratio, close, ma20, ma50)
                    st.markdown(f"<i>{comment}</i>", unsafe_allow_html=True)
        except Exception:
            continue
