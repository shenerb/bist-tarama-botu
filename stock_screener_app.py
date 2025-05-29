import streamlit as st
import yfinance as yf
import pandas as pd
import time
from tickers import get_all_bist_tickers
import matplotlib.pyplot as plt
import requests

# Finnhub API fonksiyonu
def get_finnhub_fundamentals(symbol, api_key):
    try:
        url = f"https://finnhub.io/api/v1/stock/metric"
        params = {
            "symbol": symbol,
            "metric": "all",
            "token": api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("metric", {})
    except Exception as e:
        print(f"Finnhub API hatası: {e}")
    return {}

st.set_page_config(page_title="BIST Dip & Hacim Tarayıcı", layout="centered")
st.title("📉 Dip ve Hacim Tarama")

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
                    "RSI": round(rsi_latest, 2)
                })
        except Exception:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# Sidebar
st.sidebar.header("🔧 Filtre Ayarları")
api_key = st.sidebar.text_input("🔑 Finnhub API Anahtarınız", type="password")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)
use_ceiling_filter = st.sidebar.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)

# Hisse seçimi
all_tickers = get_all_bist_tickers()
selected_tickers = st.multiselect("Hisseler", options=all_tickers, default=all_tickers[:20])

if st.button("📊 Tara"):
    if not selected_tickers:
        st.warning("Lütfen en az bir hisse seçin.")
    else:
        ceiling_threshold = 9 if use_ceiling_filter else None
        with st.spinner("Tarama yapılıyor, lütfen bekleyin..."):
            df_results = scan_stocks(
                selected_tickers,
                ma_tolerance,
                volume_threshold,
                use_ma,
                use_rsi,
                rsi_threshold,
                ceiling_threshold
            )
        if df_results.empty:
            st.info("Belirtilen kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df_results)} hisse bulundu.")
            st.dataframe(df_results)

            # Detay gösterimi
            ticker_detail = st.selectbox("Detayını görmek istediğiniz hisseyi seçin:", df_results["Hisse"].unique())
            if ticker_detail:
                ticker_full = ticker_detail + ".IS"
                data = prepare_data_for_plot(ticker_full)
                if data is not None:
                    plot_stock_chart(data, ticker_detail)

                    # Finnhub verileri
                    if api_key:
                        finnhub_data = get_finnhub_fundamentals(ticker_full, api_key)
                        if finnhub_data:
                            st.subheader("📈 Finnhub Temel Veriler")
                            # Örnek: P/E, P/B, ROE gibi temel verileri gösterelim
                            pe = finnhub_data.get("peNormalizedAnnual")
                            pb = finnhub_data.get("pbAnnual")
                            roe = finnhub_data.get("roeRoqAnnual")
                            st.markdown(f"- **Fiyat/Kazanç (P/E):** {pe if pe else 'Veri yok'}")
                            st.markdown(f"- **Fiyat/Defter Değeri (P/B):** {pb if pb else 'Veri yok'}")
                            st.markdown(f"- **Özsermaye Getirisi (ROE):** {roe if roe else 'Veri yok'}")
                        else:
                            st.warning("Finnhub'dan veri alınamadı veya API key yanlış.")
                    else:
                        st.info("Finnhub API anahtarı girilmedi, temel veriler gösterilemiyor.")

                else:
                    st.warning("Yeterli veri bulunamadı, grafik çizilemiyor.")
