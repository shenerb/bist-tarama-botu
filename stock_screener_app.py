import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt

st.set_page_config(page_title="BIST Dip & Hacim Tarayıcı", layout="centered")
st.title("📉 BIST Dip & Hacim Taraması")

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

# AL/SAT sinyali üretimi (MACD kesişim kontrolü ile düzeltildi)
def generate_trade_signal(rsi, macd_line, signal_line, close, ema):
    macd_cross_up = (macd_line.iloc[-2] <= signal_line.iloc[-2]) and (macd_line.iloc[-1] > signal_line.iloc[-1])
    macd_cross_down = (macd_line.iloc[-2] >= signal_line.iloc[-2]) and (macd_line.iloc[-1] < signal_line.iloc[-1])
    
    if rsi < 30 and macd_cross_up and close > ema:
        return "AL"
    elif rsi > 70 and macd_cross_down and close < ema:
        return "SAT"
    else:
        return "NÖTR"

# Grafik çizimi
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

# Grafik için veri hazırlama
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

# MACD yorumu
def generate_macd_commentary(macd_line, signal_line):
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        return "MACD Al sinyali verdi."
    elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        return "MACD Sat sinyali verdi."
    else:
        return "MACD nötr durumda."

# Yorumlama
def generate_commentary(rsi, volume_ratio, close, ma20, ma50):
    commentary = []
    if rsi >= 70:
        commentary.append("RSI aşırı alım bölgesinde. Düzeltme riski olabilir.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda. Teknik olarak dipten dönüş ihtimali var.")
    else:
        commentary.append("RSI nötr bölgede.")
    if volume_ratio > 1.5:
        commentary.append("Hacim ortalamanın oldukça üzerinde.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük. Sinyaller teyitsiz olabilir.")
    else:
        commentary.append("Hacim ortalama seviyede.")
    if close > ma20 > ma50:
        commentary.append("Trend pozitif.")
    elif close < ma20 < ma50:
        commentary.append("Trend zayıf.")
    else:
        commentary.append("Yön arayışı olabilir.")
    return " ".join(commentary)

# Hisse tarama
def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_rsi=False, rsi_threshold=30):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue
            data.dropna(inplace=True)
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()
            data["RSI"] = calculate_rsi(data["Close"])
            
            macd_line, signal_line, _ = calculate_macd(data["Close"])
            ema20 = data["Close"].ewm(span=20, adjust=False).mean()

            close = float(data["Close"].iloc[-1])
            prev_close = float(data["Close"].iloc[-2])
            change_pct = ((close - prev_close) / prev_close) * 100

            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
            rsi_latest = data["RSI"].iloc[-1]
            ema_latest = ema20.iloc[-1]

            trade_signal = generate_trade_signal(rsi_latest, macd_line, signal_line, close, ema_latest)

            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            last_date = data.index[-1].strftime("%Y-%m-%d")

            is_near_ma20 = close < ma20 * (1 + ma_tolerance)
            is_near_ma50 = close < ma50 * (1 + ma_tolerance)
            is_near_ma200 = close < ma200 * (1 + ma_tolerance)
            near_any_ma = is_near_ma20 or is_near_ma50 or is_near_ma200

            passes_ma = near_any_ma if use_ma else True
            passes_volume = volume_ratio >= volume_threshold
            passes_rsi = rsi_latest <= rsi_threshold if use_rsi else True

            if passes_ma and passes_volume and passes_rsi:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": last_date,
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2),
                    "RSI": round(rsi_latest, 2),
                    "İşlem Sinyali": trade_signal
                })
        except Exception:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# --- Arayüz ---

st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 1.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)

st.sidebar.header("📊 Sinyal Filtresi")
signal_filter = st.sidebar.selectbox("İşlem Sinyali Filtresi", ["Tümü", "Sadece AL", "Sadece SAT", "Sadece NÖTR"])

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Tüm BIST hisseleri taranıyor..."):
        tickers = get_all_bist_tickers()
        df = scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_rsi, rsi_threshold)

        # İşlem sinyali filtresi
        if signal_filter == "Sadece AL":
            df = df[df["İşlem Sinyali"] == "AL"]
        elif signal_filter == "Sadece SAT":
            df = df[df["İşlem Sinyali"] == "SAT"]
        elif signal_filter == "Sadece NÖTR":
            df = df[df["İşlem Sinyali"] == "NÖTR"]

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                icon = "▲" if row['Değişim'] >= 0 else "▼"
                color = "green" if row['Değişim'] >= 0 else "red"
                sinyal_rengi = {
                    "AL": "green",
                    "SAT": "red",
                    "NÖTR": "gray"
                }[row["İşlem Sinyali"]]

                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: <span style="color:{color}; font-weight:bold;">
                            {row['Kapanış']} ({icon} {abs(row['Değişim'])}%)
                        </span><br>
                        MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                        RSI: <b>{row['RSI']}</b> | Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b><br>
                        <b>İşlem Sinyali:</b> <span style="color:{sinyal_rengi}; font-weight:bold;">{row['İşlem Sinyali']}</span>
                    </div>
                """, unsafe_allow_html=True)

                ticker_full = row['Hisse'] + ".IS"
                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    rsi_latest = data_plot["RSI"].iloc[-1]
                    macd_comment = generate_macd_commentary(data_plot["MACD_Line"], data_plot["MACD_Signal"])
                    commentary = generate_commentary(
                        rsi_latest,
                        row['Hacim Katsayısı'],
                        row['Kapanış'],
                        row['MA20'],
                        row['MA50']
                    )
                    st.markdown(f"<i>{macd_comment}</i>", unsafe_allow_html=True)
                    st.markdown(f"<i>{commentary}</i>", unsafe_allow_html=True)
                    plot_stock_chart(data_plot, row['Hisse'])
