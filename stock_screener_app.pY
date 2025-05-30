import streamlit as st
import hashlib
import uuid
import os
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt

# -----------------------------
# Cihaz Kimliği Oluşturma
# -----------------------------
def get_device_id():
    system_id = str(uuid.getnode())  # Sadece MAC adresi kullan (sabit kalsın)
    hashed = hashlib.sha256(system_id.encode()).hexdigest()
    return hashed[:20]

# -----------------------------
# Cihaz Yetkili Mi Kontrol Et
# -----------------------------
def is_device_authorized(device_id):
    if not os.path.exists("authorized_devices.txt"):
        return False
    with open("authorized_devices.txt", "r") as f:
        allowed_ids = f.read().splitlines()
    return device_id in allowed_ids

# -----------------------------
# Cihaz Kontrolü
# -----------------------------
device_id = get_device_id()
if not is_device_authorized(device_id):
    st.error("❌ Bu cihaz yetkili değil.")
    st.warning("Lütfen aşağıdaki cihaz kodunu geliştiriciye gönderin:")
    st.code(device_id)
    st.stop()

# -----------------------------
# Uygulamanın Asıl İçeriği Başlıyor
# -----------------------------

st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")
st.title("📈 Hisse Analiz")

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
        commentary.append("RSI aşırı alım bölgesinde.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda.")
    else:
        commentary.append("RSI nötr.")
    if volume_ratio > 1.5:
        commentary.append("Hacim yüksek.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük.")
    else:
        commentary.append("Hacim normal.")
    if close > ma20 > ma50:
        commentary.append("Trend yukarı.")
    elif close < ma20 < ma50:
        commentary.append("Trend aşağı.")
    else:
        commentary.append("Trend kararsız.")
    commentary.append("⚠️ Yatırım tavsiyesi değildir.")
    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")
    ax1.set_title(f"{ticker_name} - Kapanış ve Ortalamalar")
    ax1.legend()
    ax2.plot(data.index, data["RSI"], label="RSI", color="purple")
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    ax2.legend()
    ax3.plot(data.index, data["MACD_Line"], label="MACD", color="blue")
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange")
    ax3.bar(data.index, data["MACD_Hist"], label="Histogram", color="gray")
    ax3.legend()
    plt.tight_layout()
    st.pyplot(fig)
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

# Sidebar
st.sidebar.header("Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Eşiği", 0.1, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Filtresi", value=True)
use_volume = st.sidebar.checkbox("Hacim Filtresi", value=True)
use_rsi = st.sidebar.checkbox("RSI Filtresi", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)

all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("Hisseler", options=all_tickers)

def scan_stocks(tickers):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="3mo", interval="1d", progress=False)
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
            rsi_latest = float(data["RSI"].iloc[-1])
            volume = float(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            is_near_ma = close < min(ma20, ma50, ma200) * (1 + ma_tolerance)
            passes_ma = is_near_ma if use_ma else True
            passes_volume = volume_ratio >= volume_threshold if use_volume else True
            passes_rsi = rsi_latest <= rsi_threshold if use_rsi else True
            if passes_ma and passes_volume and passes_rsi:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Kapanış": close,
                    "MA20": ma20,
                    "MA50": ma50,
                    "RSI": rsi_latest,
                    "Hacim Katsayısı": volume_ratio
                })
        except:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

if st.button("Taramayı Başlat"):
    st.info("Taranıyor...")
    tickers = [t + ".IS" for t in selected_tickers] if selected_tickers else [t + ".IS" for t in all_tickers]
    df = scan_stocks(tickers)
    if df.empty:
        st.warning("Uygun hisse bulunamadı.")
    else:
        for _, row in df.iterrows():
            st.subheader(row["Hisse"])
            st.write(f"Kapanış: {row['Kapanış']:.2f} TL")
            st.write(f"RSI: {row['RSI']:.1f}")
            st.write(f"Hacim Katsayısı: {row['Hacim Katsayısı']:.2f}")
            commentary = generate_commentary(
                float(row['RSI']),
                float(row['Hacim Katsayısı']),
                float(row['Kapanış']),
                float(row['MA20']),
                float(row['MA50'])
            )
            st.info(commentary)
            data = prepare_data_for_plot(row["Hisse"] + ".IS")
            if data is not None:
                plot_stock_chart(data, row["Hisse"])
