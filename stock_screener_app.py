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

def calculate_macd(series, short=12, long=26, signal=9):
    exp1 = series.ewm(span=short, adjust=False).mean()
    exp2 = series.ewm(span=long, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def generate_commentary(rsi, volume_ratio, close, ma20, ma50, macd, macd_signal, close_val, upper_band, lower_band):
    commentary = []

    # RSI Yorumları
    if rsi >= 70:
        commentary.append("RSI aşırı alım bölgesinde. Düzeltme riski olabilir.")
    elif rsi <= 30:
        commentary.append("RSI aşırı satımda. Teknik olarak dipten dönüş ihtimali var.")
    else:
        commentary.append("RSI nötr bölgede. Belirsiz yön.")

    # Hacim Yorumu
    if volume_ratio > 1.5:
        commentary.append("Hacim ortalamanın oldukça üzerinde. İlgi artmış olabilir.")
    elif volume_ratio < 0.8:
        commentary.append("Hacim düşük. Sinyaller teyitsiz olabilir.")
    else:
        commentary.append("Hacim ortalama seviyede.")

    # Trend Yorumu
    if close > ma20 > ma50:
        commentary.append("Fiyat kısa ve orta vadeli ortalamaların üzerinde. Trend pozitif.")
    elif close < ma20 < ma50:
        commentary.append("Fiyat kısa ve orta vadeli ortalamaların altında. Trend zayıf.")
    else:
        commentary.append("Fiyat ortalamalara yakın. Yön arayışı olabilir.")

    # MACD Yorumu
    if macd > macd_signal:
        commentary.append("MACD sinyal çizgisinin üzerinde, pozitif momentum var.")
    else:
        commentary.append("MACD sinyal çizgisinin altında, momentum negatif.")

    # Bollinger Bandı Yorumu
    if close_val > upper_band:
        commentary.append("Fiyat üst Bollinger Bandının üzerinde, aşırı alım olabilir.")
    elif close_val < lower_band:
        commentary.append("Fiyat alt Bollinger Bandının altında, aşırı satım olabilir.")
    else:
        commentary.append("Fiyat Bollinger Bandı içinde, normal aralıkta.")

    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    plt.figure(figsize=(10, 4))
    plt.plot(data.index, data["Close"], label="Kapanış", color="blue")
    plt.plot(data.index, data["MA20"], label="MA20", color="orange")
    plt.plot(data.index, data["MA50"], label="MA50", color="green")
    plt.plot(data.index, data["MA200"], label="MA200", color="red")
    plt.plot(data.index, data["UpperBB"], label="Bollinger Üst Bant", color="purple", linestyle="--")
    plt.plot(data.index, data["LowerBB"], label="Bollinger Alt Bant", color="purple", linestyle="--")
    plt.title(f"{ticker_name} - Son 1 Yıl Kapanış ve MA + Bollinger Band")
    plt.legend()

    plt.text(
        0.5, 0.5, "Bay-P",
        fontsize=40,
        color="gray",
        alpha=0.15,
        ha="center",
        va="center",
        transform=plt.gca().transAxes,
        weight="bold"
    )

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

    ma20 = data["Close"].rolling(20).mean()
    std20 = data["Close"].rolling(20).std()
    data["UpperBB"] = ma20 + (std20 * 2)
    data["LowerBB"] = ma20 - (std20 * 2)

    macd, macd_signal, macd_hist = calculate_macd(data["Close"])
    data["MACD"] = macd
    data["MACD_Signal"] = macd_signal
    data["MACD_Hist"] = macd_hist

    return data

def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma):
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
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: <span style="color:{color}; font-weight:bold;">
                            {row['Kapanış']} ({icon} {abs(row['Değişim'])}%)
                        </span><br>
                        MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                        Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b><br>
               
