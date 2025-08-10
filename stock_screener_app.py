import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers  # BIST hisselerini getiriyor varsayıyorum

st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")
st.title("📈 Hisse Analiz")

# ---------------------- Veri yükleme ----------------------
@st.cache_data
def load_halaciklik_data():
    df_ozet = pd.read_excel("temelozet.xlsx")
    df_ozet["Kod"] = df_ozet["Kod"].str.strip().str.upper()
    return df_ozet.set_index("Kod")["Halka Açıklık Oranı (%)"].to_dict()

halka_aciklik_dict = load_halaciklik_data()

@st.cache_data
def load_lot_data():
    df_lot = pd.read_csv("dolasim_lot.csv", sep=None, engine='python')
    df_lot["Kod"] = df_lot["Kod"].str.strip().str.upper()
    return df_lot.set_index("Kod")["Dolasimdaki_Lot"].to_dict()

dolasim_lot_dict = load_lot_data()

# ---------------------- Teknik hesaplamalar ----------------------

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

def calculate_trin(tickers):
    """
    TRIN = (Advancing Issues / Declining Issues) / (Advancing Volume / Declining Volume)
    Hesaplamak için:
    - Hangi hisseler kapanış fiyatlarını bir önceki güne göre yükseltti (advancers)
    - Hangi hisseler düştü (decliners)
    - Bu hisselerin toplam hacimleri
    """
    adv_count = 0
    dec_count = 0
    adv_volume = 0
    dec_volume = 0

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="2d", interval="1d", progress=False)
            if len(data) < 2:
                continue
            close_today = data["Close"].iloc[-1]
            close_yesterday = data["Close"].iloc[-2]
            volume_today = data["Volume"].iloc[-1]

            if close_today > close_yesterday:
                adv_count += 1
                adv_volume += volume_today
            elif close_today < close_yesterday:
                dec_count += 1
                dec_volume += volume_today
        except:
            continue
        time.sleep(0.05)

    # Sıfıra bölme hatalarını engelle
    if dec_count == 0 or dec_volume == 0:
        return np.nan

    trin = (adv_count / dec_count) / (adv_volume / dec_volume)
    return trin

# ---------------------- Grafik hazırlama ----------------------

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        return None
    data.dropna(inplace=True)
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["EMA89"] = data["Close"].ewm(span=89, adjust=False).mean()
    data["RSI"] = calculate_rsi(data["Close"])
    macd_line, signal_line, histogram = calculate_macd(data["Close"])
    data["MACD_Line"] = macd_line
    data["MACD_Signal"] = signal_line
    data["MACD_Hist"] = histogram
    return data

def plot_stock_chart(data, ticker_name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True,
                                       gridspec_kw={'height_ratios': [2, 1, 1]})

    ax1.plot(data.index, data["Close"], label="Kapanış", color="blue")
    ax1.plot(data.index, data["MA20"], label="MA20", color="orange")
    ax1.plot(data.index, data["MA50"], label="MA50", color="green")
    ax1.plot(data.index, data["MA200"], label="MA200", color="red")
    ax1.plot(data.index, data["EMA89"], label="EMA89", color="magenta", linestyle="--")
    ax1.set_title(f"{ticker_name} - Son 1 Yıl Teknik Görünüm")
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

    fig.text(0.5, 0.5, 'Bay-P',
             fontsize=50, color='gray', alpha=0.15,
             ha='center', va='center',
             weight='bold', style='italic', rotation=20)

    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# ---------------------- Tarama fonksiyonu ----------------------

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
            passes_volume = volume_ratio >= volume_threshold if use_volume else True
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

# ---------------------- Sidebar ----------------------

st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_volume = st.sidebar.checkbox("Hacim Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)
use_ceiling_filter = st.sidebar.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)
use_trin_filter = st.sidebar.checkbox("TRIN Filtresi Kullan", value=False)

all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("📌 Tarama İçin Hisse Seç (boş bırak tümü için)", options=all_tickers)

# ---------------------- Ana içerik ----------------------

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        ceiling_threshold = 9.5 if use_ceiling_filter else None

        if use_trin_filter:
            trin_value = calculate_trin(tickers_to_scan)
            st.write(f"### TRIN Değeri: {trin_value:.2f}" if not np.isnan(trin_value) else "TRIN hesaplanamadı")

        df = scan_stocks(tickers_to_scan, ma_tolerance, volume_threshold, use_ma, use_volume, use_rsi, rsi_threshold, ceiling_threshold)

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

                market_cap_try = info.get("marketCap", None)
                usdtry = None
                try:
                    usdtry = yf.Ticker("USDTRY=X").info.get("regularMarketPrice", None)
                except:
                    pass

                market_cap_usd_str = "N/A"
                if market_cap_try and usdtry:
                    market_cap_usd = market_cap_try / usdtry
                    if market_cap_usd >= 1e9:
                        market_cap_usd_str = f"{market_cap_usd / 1e9:.2f} Milyar $"
                    elif market_cap_usd >= 1e6:
                        market_cap_usd_str = f"{market_cap_usd / 1e6:.2f} Milyon $"

                lot = dolasim_lot_dict.get(hisse, "N/A")
                if lot != "N/A":
                    try:
                        lot = f"{int(lot):,}".replace(",", ".")
                    except:
                        pass

                halka_aciklik = halka_aciklik_dict.get(hisse, "N/A")
                if halka_aciklik != "N/A":
                    halka_aciklik = f"%{halka_aciklik:.2f}"

                color = "green" if row['Değişim'] >= 0 else "red"
                sign = "▲" if row['Değişim'] >= 0 else "▼"

                st.markdown(f"""
                <div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin:15px 0; font-family:Arial, sans-serif;">

                    <div style="display:flex; gap:20px; font-size:14px; margin-bottom:8px; flex-wrap: wrap;">
                        <div><b>RSI:</b> {row['RSI']}</div>
                        <div><b>Hacim/Ort:</b> {row['Hacim Katsayısı']}</div>
                        <div><b>MA20:</b> {row['MA20']}</div>
                        <div><b>MA50:</b> {row['MA50']}</div>
                    </div>

                    <div style="font-size:14px; margin-bottom:10px;">
                        <b>Dolaşımdaki Lot:</b> {lot} &nbsp;&nbsp; | &nbsp;&nbsp; 
                        <b>Halka Açıklık Oranı:</b> {halka_aciklik}
                    </div>

                    <div style="
                        border-top:1px solid #ddd; 
                        padding-top:10px; 
                        font-size:14px; 
                        color:#555;
                        display: flex;
                        gap: 20px;
                        flex-wrap: wrap;
                    ">
                        <div><b>F/K:</b> {info.get("trailingPE", "N/A")}</div>
                        <div><b>PD/DD:</b> {info.get("priceToBook", "N/A")}</div>
                        <div><b>Piyasa Değeri:</b> {market_cap_usd_str}</div>
                    </div>

                    <div style="margin-top:8px; font-size:16px; font-weight:bold; color:{color};">
                        Kapanış: {row['Kapanış']} &nbsp;&nbsp; 
                        <span style="color:{color};">{sign} {abs(row['Değişim'])}%</span>
                    </div>

                    <div style="margin-top:8px; font-size:12px; color:#888;">
                        Tarih: {row['Tarih']}
                    </div>

                </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    plot_stock_chart(data_plot, hisse)
                else:
                    st.info(f"{hisse} için yeterli veri bulunamadı.")
