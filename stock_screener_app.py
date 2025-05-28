import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt

st.set_page_config(page_title="BIST Dip & Hacim Tarayıcı", layout="centered")
st.title("📉 BIST Dip & Hacim Taraması")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def generate_macd_commentary(macd_line, signal_line):
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        return "MACD Al sinyali verdi."
    elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        return "MACD Sat sinyali verdi."
    else:
        return "MACD nötr durumda."

def generate_commentary(rsi, volume_ratio, close, ma20, ma50):
    commentary = []

    if rsi >= 70:
        commentary.append("RSI aşırı alım bölgesinde. Düzeltme riski olabilir.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda. Teknik olarak dipten dönüş ihtimali var.")
    else:
        commentary.append("RSI nötr bölgede. Belirsiz yön.")

    if volume_ratio > 1.5:
        commentary.append("Hacim ortalamanın oldukça üzerinde. İlgi artmış olabilir.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük. Sinyaller teyitsiz olabilir.")
    else:
        commentary.append("Hacim ortalama seviyede.")

    if close > ma20 > ma50:
        commentary.append("Fiyat kısa ve orta vadeli ortalamaların üzerinde. Trend pozitif.")
    elif close < ma20 < ma50:
        commentary.append("Fiyat kısa ve orta vadeli ortalamaların altında. Trend zayıf.")
    else:
        commentary.append("Fiyat ortalamalara yakın. Yön arayışı olabilir.")

    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    plt.figure(figsize=(10, 4))
    plt.plot(data.index, data["Close"], label="Kapanış", color="blue")
    plt.plot(data.index, data["MA20"], label="MA20", color="orange")
    plt.plot(data.index, data["MA50"], label="MA50", color="green")
    plt.plot(data.index, data["MA200"], label="MA200", color="red")
    plt.title(f"{ticker_name} - Son 1 Yıl Kapanış ve MA")
    plt.legend()
    plt.text(0.5, 0.5, "Bay-P", fontsize=40, color="gray", alpha=0.15,
             ha="center", va="center", transform=plt.gca().transAxes, weight="bold")
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        return None
    data.dropna(inplace=True)
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    macd_line, signal_line, histogram = calculate_macd(data["Close"])
    data["MACD_Line"] = macd_line
    data["MACD_Signal"] = signal_line
    data["MACD_Hist"] = histogram
    return data

# --- Yeni Özellik: Hisse manuel inceleme ---
st.subheader("📌 Hisse İncele")
manual_input = st.text_input("İncelemek istediğiniz hisse kodunu girin (örnek: ASELS):")

if st.button("🔍 İncele"):
    if manual_input:
        ticker_manual = manual_input.strip().upper() + ".IS"
        data_plot = prepare_data_for_plot(ticker_manual)
        if data_plot is None:
            st.error(f"{manual_input} için veri alınamadı. Hisse kodunu kontrol edin.")
        else:
            rsi_latest = data_plot["RSI"].iloc[-1]
            volume = data_plot["Volume"].iloc[-1]
            avg_volume = data_plot["Volume"].rolling(20).mean().iloc[-1]
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            ma20 = data_plot["MA20"].iloc[-1]
            ma50 = data_plot["MA50"].iloc[-1]
            close = data_plot["Close"].iloc[-1]

            macd_comment = generate_macd_commentary(data_plot["MACD_Line"], data_plot["MACD_Signal"])
            commentary = generate_commentary(rsi_latest, volume_ratio, close, ma20, ma50)

            st.markdown(f"**Kapanış:** {close:.2f} | **RSI:** {rsi_latest:.2f}")
            st.markdown(f"**Hacim/Ort:** {volume_ratio:.2f}")
            st.markdown(f"**MACD:** {macd_comment}")
            st.markdown(f"**Yorum:** _{commentary}_")

            plot_stock_chart(data_plot, manual_input)
    else:
        st.info("Lütfen bir hisse kodu girin.")
