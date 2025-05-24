import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers  # Senin tickers modülün

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

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_supertrend(df, period=10, multiplier=3):
    df = df.copy()
    df['TR'] = df[['High', 'Low', 'Close']].apply(
        lambda x: max(x['High'] - x['Low'], abs(x['High'] - x['Close']), abs(x['Low'] - x['Close'])),
        axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()

    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])

    supertrend = [True] * len(df)  # True = uptrend, False = downtrend

    for i in range(period, len(df)):
        curr_close = df['Close'].iloc[i]
        prev_upper = df['UpperBand'].iloc[i - 1]
        prev_lower = df['LowerBand'].iloc[i - 1]
        prev_supertrend = supertrend[i - 1]

        if prev_supertrend:
            if curr_close <= prev_upper:
                supertrend[i] = False
            else:
                supertrend[i] = True
                if df['LowerBand'].iloc[i] > prev_lower:
                    df.at[df.index[i], 'LowerBand'] = prev_lower
        else:
            if curr_close >= prev_lower:
                supertrend[i] = True
            else:
                supertrend[i] = False
                if df['UpperBand'].iloc[i] < prev_upper:
                    df.at[df.index[i], 'UpperBand'] = prev_upper

    df['Supertrend'] = supertrend
    return df

def generate_commentary(rsi, volume_ratio, close, ma20, ma50, supertrend, macd_line, signal_line):
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

    if supertrend:
        commentary.append("Supertrend AL sinyali veriyor.")
    else:
        commentary.append("Supertrend SAT sinyali veriyor.")

    if macd_line > signal_line:
        commentary.append("MACD pozitif ve sinyal hattının üzerinde. AL sinyali.")
    else:
        commentary.append("MACD negatif ve sinyal hattının altında. SAT sinyali.")

    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data["Close"], label="Kapanış", color="blue")
    plt.plot(data.index, data["MA20"], label="MA20", color="orange")
    plt.plot(data.index, data["MA50"], label="MA50", color="green")
    plt.plot(data.index, data["MA200"], label="MA200", color="red")

    plt.plot(data.index, data["LowerBand"], label="Supertrend Alt Bant", linestyle="--", color="green", alpha=0.5)
    plt.plot(data.index, data["UpperBand"], label="Supertrend Üst Bant", linestyle="--", color="red", alpha=0.5)

    plt.legend()
    plt.title(f"{ticker_name} - Son 1 Yıl Kapanış, MA ve Supertrend")
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()

    plt.figure(figsize=(10, 3))
    plt.plot(data.index, data["MACD_Line"], label="MACD", color="purple")
    plt.plot(data.index, data["Signal_Line"], label="Sinyal Hattı", color="orange")
    plt.bar(data.index, data["MACD_Histogram"], label="Histogram", color="gray", alpha=0.5)
    plt.legend()
    plt.title(f"{ticker_name} - MACD")
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
    data = calculate_supertrend(data)
    macd_line, signal_line, histogram = calculate_macd(data["Close"])
    data["MACD_Line"] = macd_line
    data["Signal_Line"] = signal_line
    data["MACD_Histogram"] = histogram
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
            st.dataframe(df)

            selected_ticker = st.selectbox("Grafiğini görmek istediğiniz hisseyi seçin:", df["Hisse"].tolist())

            if selected_ticker:
                full_ticker = selected_ticker + ".IS"
                data = prepare_data_for_plot(full_ticker)
                if data is not None:
                    plot_stock_chart(data, selected_ticker)

                    last
