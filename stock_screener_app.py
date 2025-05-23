# stock_screener_app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from tickers import get_all_bist_tickers

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

def calculate_macd(close, slow=26, fast=12, signal=9):
    exp1 = close.ewm(span=fast, adjust=False).mean()
    exp2 = close.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def find_support_resistance(data, window=20):
    if "Low" not in data.columns or "High" not in data.columns:
        return None, None

    support = []
    resistance = []
    for i in range(window, len(data)):
        low_range = data["Low"].iloc[i - window:i]
        high_range = data["High"].iloc[i - window:i]
        if data["Low"].iloc[i] == low_range.min():
            support.append((data.index[i], data["Low"].iloc[i]))
        if data["High"].iloc[i] == high_range.max():
            resistance.append((data.index[i], data["High"].iloc[i]))
    return support, resistance

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
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Kapanış"
    ))

    fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], mode='lines', name='MA20', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], mode='lines', name='MA50', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=data.index, y=data["MA200"], mode='lines', name='MA200', line=dict(color='red')))

    support, resistance = find_support_resistance(data)
    if support:
        for s in support[-5:]:
            fig.add_hline(y=s[1], line_dash="dot", line_color="blue", opacity=0.3)
    if resistance:
        for r in resistance[-5:]:
            fig.add_hline(y=r[1], line_dash="dot", line_color="red", opacity=0.3)

    fig.update_layout(title=f"{ticker_name} - Teknik Görünüm", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # MACD Plot
    macd_line, signal_line = calculate_macd(data["Close"])
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data.index, y=macd_line, name='MACD', line=dict(color='purple')))
    fig_macd.add_trace(go.Scatter(x=data.index, y=signal_line, name='Sinyal', line=dict(color='gray')))
    fig_macd.update_layout(title="MACD Göstergesi")
    st.plotly_chart(fig_macd, use_container_width=True)

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=False)
    if data.empty or len(data) < 50:
        return None

    required_columns = {"Close", "Low", "High", "Open"}
    if not required_columns.issubset(data.columns):
        return None

    data.dropna(inplace=True)
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    return data

def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False, auto_adjust=False)
            if data.empty or len(data) < 30:
                continue

            data.dropna(inplace=True)
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()

            close = float(data["Close"].iloc[-1])
            prev_close = float(data["Close"].iloc[-2])
            change_pct = ((close - prev_close) / prev_close) * 100

            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
            last_date = data.index[-1].strftime("%Y-%m-%d")
            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            is_near_ma20 = close < ma20 * (1 + ma_tolerance)
            is_near_ma50 = close < ma50 * (1 + ma_tolerance)
            is_near_ma200 = close < ma200 * (1 + ma_tolerance)
            near_any_ma = is_near_ma20 or is_near_ma50 or is_near_ma200

            passes_ma = near_any_ma if use_ma else True
            passes_volume = volume_ratio >= volume_threshold

            if passes_ma and passes_volume:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": last_date,
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2)
                })
        except Exception as e:
            print(f"{ticker} hatası: {e}")
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
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: <span style="color:{color}; font-weight:bold;">
                            {row['Kapanış']} ({icon} {abs(row['Değişim'])}%)
                        </span><br>
                        MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                        Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b><br>
                """, unsafe_allow_html=True)

                ticker_full = row['Hisse'] + ".IS"
                data_plot = prepare_data_for_plot(ticker_full)
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
                    st.markdown(f"<b>Yorum:</b> {commentary} <br><i>Yatırım tavsiyesi değildir.</i>", unsafe_allow_html=True)

                    plot_stock_chart(data_plot, row['Hisse'])
                else:
                    st.info(f"{row['Hisse']} için grafik verisi yok.")
                st.markdown("</div>", unsafe_allow_html=True)
