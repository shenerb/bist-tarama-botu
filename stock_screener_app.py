# stock_screener_app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt
import numpy as np

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

def calculate_macd(data):
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def find_support_resistance(data, window=20):
    supports = []
    resistances = []
    for i in range(window, len(data)):
        window_data = data["Close"].iloc[i - window:i]
        if data["Close"].iloc[i] == window_data.min():
            supports.append((data.index[i], data["Close"].iloc[i]))
        elif data["Close"].iloc[i] == window_data.max():
            resistances.append((data.index[i], data["Close"].iloc[i]))
    return supports, resistances

def generate_commentary(rsi, volume_ratio, close, ma20, ma50):
    commentary = []

    if rsi >= 70:
        commentary.append("RSI aşırı alımda.")
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
        commentary.append("Trend pozitif.")
    elif close < ma20 < ma50:
        commentary.append("Trend negatif.")
    else:
        commentary.append("Yönsüz seyir.")

    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), gridspec_kw={"height_ratios": [2, 1]})

    # Fiyat grafiği
    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")

    supports, resistances = find_support_resistance(data)
    for s in supports[-3:]:
        ax1.hlines(s[1], xmin=data.index[0], xmax=data.index[-1], colors='cyan', linestyles='dashed', alpha=0.5)
    for r in resistances[-3:]:
        ax1.hlines(r[1], xmin=data.index[0], xmax=data.index[-1], colors='magenta', linestyles='dashed', alpha=0.5)

    ax1.set_title(f"{ticker_name} - Fiyat ve Ortalamalar")
    ax1.legend()

    # MACD
    macd, signal = calculate_macd(data)
    ax2.plot(data.index, macd, label="MACD", color="purple")
    ax2.plot(data.index, signal, label="Signal", color="gray")
    ax2.bar(data.index, macd - signal, color=np.where(macd - signal > 0, 'lime', 'salmon'), alpha=0.5)
    ax2.set_title("MACD Göstergesi")
    ax2.legend()

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 50 or "Close" not in data.columns:
        return None
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    return data

def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False)
            if data.empty or len(data) < 30 or "Close" not in data.columns or "Volume" not in data.columns:
                continue

            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()

            close = data["Close"].iloc[-1]
            prev_close = data["Close"].iloc[-2]
            change_pct = ((close - prev_close) / prev_close) * 100

            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            ma200 = data["MA200"].iloc[-1]
            last_date = data.index[-1].strftime("%Y-%m-%d")
            volume = data["Volume"].iloc[-1]
            avg_volume = data["AvgVolume20"].iloc[-1]
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            is_near_ma = (
                close < ma20 * (1 + ma_tolerance)
                or close < ma50 * (1 + ma_tolerance)
                or close < ma200 * (1 + ma_tolerance)
            )

            if (not use_ma or is_near_ma) and (volume_ratio >= volume_threshold):
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": last_date,
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2)
                })
        except Exception:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# Arayüz
st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 1.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Tüm BIST hisseleri taranıyor..."):
        tickers = get_all_bist_tickers()
        df = scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma)

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                icon = "▲" if row['Değişim'] >= 0 else "▼"
                color = "green" if row['Değişim'] >= 0 else "red"

                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>{row['Tarih']}</i><br>
                        Kapanış: <span style="color:{color}; font-weight:bold;">{row['Kapanış']} ({icon} {abs(row['Değişim'])}%)</span><br>
                        MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                        Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b>
                    </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(row['Hisse'] + ".IS")
                if data_plot is not None:
                    rsi_latest = data_plot["RSI"].iloc[-1]
                    st.markdown(f"<b>RSI:</b> {rsi_latest:.2f}", unsafe_allow_html=True)

                    commentary = generate_commentary(
                        rsi_latest,
                        row['Hacim Katsayısı'],
                        row['Kapanış'],
                        row['MA20'],
                        row['MA50']
                    )
                    st.markdown(f"<b>Yorum:</b> {commentary}<br><i>Yatırım tavsiyesi değildir.</i>", unsafe_allow_html=True)
                    plot_stock_chart(data_plot, row['Hisse'])
                else:
                    st.info(f"{row['Hisse']} için grafik verisi yok.")
