import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt

# Piyasa değeri formatlama
def format_market_cap(cap):
    if cap is None or cap != cap:
        return "N/A"
    if cap >= 1_000_000_000:
        return f"{cap / 1_000_000_000:.2f} Milyar $"
    elif cap >= 1_000_000:
        return f"{cap / 1_000_000:.2f} Milyon $"
    else:
        return f"{cap:.0f} $"

# Streamlit Ayarları
st.set_page_config(page_title="BIST Dip & Hacim Tarayıcı", layout="centered")
st.title("📉 Dip ve Hacim Tarama")

# RSI Hesaplama
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD Hesaplama
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
        commentary.append("RSI nötr bölgede.")
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
        commentary.append("Fiyat ortalamalara yakın.")
    return " ".join(commentary)

def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})
    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")
    ax1.set_title(f"{ticker_name} - Son 1 Yıl Kapanış ve MA")
    ax1.legend()
    ax1.grid(True)
    ax2.plot(data.index, data["RSI"], label="RSI", color="purple")
    ax2.axhline(70, color='red', linestyle='--', linewidth=1)
    ax2.axhline(30, color='green', linestyle='--', linewidth=1)
    ax2.set_ylabel("RSI")
    ax2.legend()
    ax2.grid(True)
    ax3.plot(data.index, data["MACD_Line"], label="MACD", color="blue")
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange")
    ax3.bar(data.index, data["MACD_Hist"], label="Histogram", color="gray", alpha=0.4)
    ax3.set_ylabel("MACD")
    ax3.legend()
    ax3.grid(True)
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

def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_rsi=False, rsi_threshold=30, ceiling_threshold=None):
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

            close = float(data["Close"].iloc[-1])
            prev_close = float(data["Close"].iloc[-2])
            change_pct = ((close - prev_close) / prev_close) * 100

            if ceiling_threshold is not None and change_pct < ceiling_threshold:
                continue

            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
            rsi_latest = data["RSI"].iloc[-1]
            last_date = data.index[-1].strftime("%Y-%m-%d")
            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            is_near_ma = close < min(ma20, ma50, ma200) * (1 + ma_tolerance)
            passes_ma = is_near_ma if use_ma else True
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
                    "RSI": round(rsi_latest, 2)
                })
        except Exception:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# Sidebar Ayarları
st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)
use_ceiling_filter = st.sidebar.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)

# Hisse Seçimi
all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("📌 Tarama İçin Hisse Seç (boş bırak tümü için)", options=all_tickers)

# Tarama Başlat
if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        ceiling_threshold = 9.5 if use_ceiling_filter else None

        df = scan_stocks(tickers_to_scan, ma_tolerance, volume_threshold, use_ma, use_rsi, rsi_threshold, ceiling_threshold)

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                hisse = row['Hisse']
                ticker_full = hisse + ".IS"
                info = {}
                try:
                    info = yf.Ticker(ticker_full).info
                except:
                    pass

                st.markdown(f"""
                <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0;">
                    <strong>{hisse}</strong><br>
                    <i>Tarih: {row['Tarih']}</i><br>
                    Kapanış: <b>{row['Kapanış']}</b> ({'▲' if row['Değişim'] >= 0 else '▼'} {abs(row['Değişim'])}%)<br>
                    RSI: <b>{row['RSI']}</b> | Hacim/Ort: <b>{row['Hacim Katsayısı']}</b><br>
                    MA20: {row['MA20']} | MA50: {row['MA50']}<br><br>
                    📊 <b>Finansal Oranlar</b><br>
                    F/K: <b>{info.get("trailingPE", "N/A")}</b><br>
                    PD/DD: <b>{info.get("priceToBook", "N/A")}</b><br>
                    Piyasa Değeri: <b>{format_market_cap(info.get("marketCap"))}</b>
                </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    rsi_latest = data_plot["RSI"].iloc[-1]
                    macd_comment = generate_macd_commentary(data_plot["MACD_Line"], data_plot["MACD_Signal"])
                    st.markdown(f"<b>MACD:</b> {macd_comment}", unsafe_allow_html=True)

                    commentary = generate_commentary(
                        rsi_latest,
                        row['Hacim Katsayısı'],
                        row['Kapanış'],
                        row['MA20'],
                        row['MA50']
                    )
                    st.markdown(f"<i>{commentary}</i>", unsafe_allow_html=True)
                    plot_stock_chart(data_plot, row['Hisse'])
