import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt

# EMA hesaplama
def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

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
        commentary.append("RSI aşırı satım bölgesinde.")
    else:
        commentary.append("RSI nötr.")

    if volume_ratio > 1.5:
        commentary.append("Hacim yüksek.")
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

# Grafik çizimi
def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})
    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")
    ax1.plot(data.index, data["EMA89"], label="EMA89", color="purple")
    ax1.legend()
    ax1.grid(True)
    ax1.set_title(f"{ticker_name} - Fiyat ve Ortalamalar")

    ax2.plot(data.index, data["RSI"], label="RSI", color="darkviolet")
    ax2.axhline(70, linestyle="--", color="red")
    ax2.axhline(30, linestyle="--", color="green")
    ax2.legend()
    ax2.grid(True)

    ax3.plot(data.index, data["MACD_Line"], label="MACD", color="blue")
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange")
    ax3.bar(data.index, data["MACD_Hist"], label="Histogram", color="gray", alpha=0.4)
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# Tarama fonksiyonu
def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_volume, use_rsi=False, rsi_threshold=30, ceiling_threshold=None):
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
            data["EMA89"] = calculate_ema(data["Close"], 89)
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()
            data["RSI"] = calculate_rsi(data["Close"])

            close = data["Close"].iloc[-1]
            prev_close = data["Close"].iloc[-2]
            change_pct = ((close - prev_close) / prev_close) * 100
            if ceiling_threshold is not None and change_pct < ceiling_threshold:
                continue

            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            rsi_latest = data["RSI"].iloc[-1]
            volume = data["Volume"].iloc[-1]
            avg_volume = data["AvgVolume20"].iloc[-1]
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            date = data.index[-1].strftime("%Y-%m-%d")

            is_near_ma = close < min(ma20, ma50) * (1 + ma_tolerance)
            passes = True
            if use_ma and not is_near_ma:
                passes = False
            if use_volume and volume_ratio < volume_threshold:
                passes = False
            if use_rsi and rsi_latest > rsi_threshold:
                passes = False

            if passes:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": date,
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "RSI": round(rsi_latest, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2)
                })

        except Exception:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# Tek tek detaylı veri
def prepare_detailed_data(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 200:
        return None
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["EMA89"] = calculate_ema(data["Close"], 89)
    data["RSI"] = calculate_rsi(data["Close"])
    macd_line, signal_line, hist = calculate_macd(data["Close"])
    data["MACD_Line"] = macd_line
    data["MACD_Signal"] = signal_line
    data["MACD_Hist"] = hist
    return data

# Streamlit Arayüzü
st.set_page_config(page_title="BIST Tarama ve Analiz", layout="wide")
st.title("📊 BIST Hisse Tarama ve Teknik Analiz")

tickers = st.text_area("📥 İncelenecek Hisseler (.IS uzantılı, virgülle ayır)", "THYAO.IS,ASELS.IS,SASA.IS").split(",")
tickers = [t.strip() for t in tickers if t.strip()]

col1, col2, col3 = st.columns(3)
with col1:
    ma_tol = st.slider("MA Toleransı (%)", 1, 10, 5) / 100
    use_ma = st.checkbox("MA Filtresi", value=True)
with col2:
    volume_threshold = st.slider("Min Hacim Katı", 0.0, 5.0, 1.5)
    use_volume = st.checkbox("Hacim Filtresi", value=True)
with col3:
    rsi_check = st.checkbox("RSI Filtresi", value=False)
    rsi_threshold = st.slider("RSI Eşiği", 10, 70, 30)
    ceiling_check = st.checkbox("Tavan Filtresi (%9+)", value=False)

if st.button("🔍 Tarama Yap"):
    with st.spinner("Hisseler taranıyor..."):
        ceiling = 9.5 if ceiling_check else None
        df = scan_stocks(
            tickers,
            ma_tolerance=ma_tol,
            volume_threshold=volume_threshold,
            use_ma=use_ma,
            use_volume=use_volume,
            use_rsi=rsi_check,
            rsi_threshold=rsi_threshold,
            ceiling_threshold=ceiling
        )

        if df.empty:
            st.warning("Uygun hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                st.markdown(f"### {row['Hisse']} ({row['Tarih']})")
                st.write(f"Kapanış: {row['Kapanış']} | Değişim: {row['Değişim']}% | RSI: {row['RSI']} | Hacim Katsayısı: {row['Hacim Katsayısı']}")
                st.write(f"MA20: {row['MA20']} | MA50: {row['MA50']}")
                
                data = prepare_detailed_data(row["Hisse"] + ".IS")
                if data is not None:
                    support = data["Low"].rolling(20).min().iloc[-1]
                    resistance = data["High"].rolling(20).max().iloc[-1]
                    macd_comment = generate_macd_commentary(data["MACD_Line"], data["MACD_Signal"])
                    comment = generate_commentary(row["RSI"], row["Hacim Katsayısı"], row["Kapanış"], row["MA20"], row["MA50"])
                    st.markdown(f"**Destek:** {support:.2f} | **Direnç:** {resistance:.2f}")
                    st.markdown(f"**MACD Yorumu:** {macd_comment}")
                    st.markdown(f"*{comment}*")
                    plot_stock_chart(data, row["Hisse"])
