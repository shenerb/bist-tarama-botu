import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers  # BIST sembollerini döndüren fonksiyon

st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")
st.title("📈 Hisse Analiz")

# ---------------- Yardım Sekmesi ----------------
with st.sidebar.expander("🆘 Yardım"):
    st.markdown("""
### Uygulama Yardımı

Bu uygulama, BIST hisseleri için teknik ve temel filtreleme yapmanızı sağlar.

#### Filtreler:
- **MA Yakınlık Toleransı:** Hisse, MA20/50/200 ortalamalarına ne kadar yakınsa seçilir.
- **Hacim Artış Eşiği:** Günlük hacmin, 20 günlük ortalama hacme oranı.
- **RSI Eşiği:** RSI değeri belirtilen seviyenin altındaysa hisse seçilir.
- **Tavan Filtresi:** Son kapanış %9.5 ve üzeri artış ise.
- **PD/DD < 1:** Defter değerinin altında fiyatlanan hisseler.
""")

# ---------------- Önbelleğe Alma ----------------
@st.cache_data
def load_halaciklik_data():
    df = pd.read_excel("temelozet.xlsx")
    df["Kod"] = df["Kod"].str.strip().str.upper()
    return df.set_index("Kod")["Halka Açıklık Oranı (%)"].to_dict()

@st.cache_data
def load_lot_data():
    df = pd.read_csv("dolasim_lot.csv", sep=None, engine='python')
    df["Kod"] = df["Kod"].str.strip().str.upper()
    return df.set_index("Kod")["Dolasimdaki_Lot"].to_dict()

halka_aciklik_dict = load_halaciklik_data()
dolasim_lot_dict = load_lot_data()

# ---------------- Teknik Göstergeler ----------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def prepare_data_for_plot(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        return None
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
    ax1.set_title(f"{ticker_name} - Teknik Görünüm")
    ax1.legend()
    ax1.grid(True)
    ax2.plot(data.index, data["RSI"], label="RSI", color="purple")
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    ax2.legend()
    ax2.grid(True)
    ax3.plot(data.index, data["MACD_Line"], label="MACD", color="blue")
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange")
    ax3.bar(data.index, data["MACD_Hist"], label="Histogram", color="gray", alpha=0.4)
    ax3.legend()
    ax3.grid(True)
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# ---------------- Tarama Fonksiyonu ----------------
def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_volume, use_rsi=False, rsi_threshold=30, ceiling_threshold=None, use_pddd_filter=False):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="90d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()
            data["EMA89"] = data["Close"].ewm(span=89, adjust=False).mean()
            data["AvgVolume20"] = data["Volume"].rolling(20).mean()
            data["RSI"] = calculate_rsi(data["Close"])

            close = float(data["Close"].iloc[-1])
            prev_close = float(data["Close"].iloc[-2])
            change_pct = ((close - prev_close) / prev_close) * 100

            if ceiling_threshold and change_pct < ceiling_threshold:
                continue

            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
            ema89 = float(data["EMA89"].iloc[-1])
            rsi_latest = data["RSI"].iloc[-1]
            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            is_near_ma = close < min(ma20, ma50, ma200) * (1 + ma_tolerance)

            passes_ma = is_near_ma if use_ma else True
            passes_volume = volume_ratio >= volume_threshold if use_volume else True
            passes_rsi = rsi_latest <= rsi_threshold if use_rsi else True

            info = {}
            try:
                info = yf.Ticker(ticker).info
            except:
                pass

            pddd = info.get("priceToBook", None)
            passes_pddd = (pddd is not None and pddd < 1) if use_pddd_filter else True

            if passes_ma and passes_volume and passes_rsi and passes_pddd:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": data.index[-1].strftime("%Y-%m-%d"),
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "EMA89": round(ema89, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2),
                    "RSI": round(rsi_latest, 2),
                    "PD/DD": pddd
                })
        except:
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)

# ---------------- Filtre Paneli ----------------
with st.expander("📌 Filtre Ayarlarını Göster / Gizle", expanded=True):
    ma_tolerance = st.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
    volume_threshold = st.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
    use_ma = st.checkbox("MA Dip Filtresi Kullan", value=True)
    use_volume = st.checkbox("Hacim Filtresi Kullan", value=True)
    use_rsi = st.checkbox("RSI Dip Filtresi Kullan", value=False)
    rsi_threshold = st.slider("RSI Eşiği", 10, 50, 30)
    use_ceiling_filter = st.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)
    use_pddd_filter = st.checkbox("PD/DD < 1 olanları göster", value=False)

# ---------------- Hisse Seçimi ----------------
all_tickers = get_all_bist_tickers()
selected_tickers = st.multiselect("📍 Tarama İçin Hisse Seç (boş bırak tümü için)", options=all_tickers)

# ---------------- Tarama ----------------
if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        ceiling_threshold = 9.5 if use_ceiling_filter else None
        df = scan_stocks(tickers_to_scan, ma_tolerance, volume_threshold, use_ma, use_volume, use_rsi, rsi_threshold, ceiling_threshold, use_pddd_filter)

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            for _, row in df.iterrows():
                hisse = row['Hisse']
                ticker_full = hisse + ".IS"
                info = {}
                try:
                    info = yf.Ticker(ticker_full).info
                except:
                    pass

                market_cap_try = info.get("marketCap", None)
                usdtry = yf.Ticker("USDTRY=X").info.get("regularMarketPrice", None)
                market_cap_usd_str = "N/A"
                if market_cap_try and usdtry:
                    market_cap_usd = market_cap_try / usdtry
                    market_cap_usd_str = f"{market_cap_usd / 1e6:.2f} Milyon $" if market_cap_usd < 1e9 else f"{market_cap_usd / 1e9:.2f} Milyar $"

                lot = dolasim_lot_dict.get(hisse, "N/A")
                halka_aciklik = halka_aciklik_dict.get(hisse, "N/A")
                lot_str = f"{int(lot):,}".replace(",", ".") if lot != "N/A" else "N/A"
                halka_str = f"%{halka_aciklik:.2f}" if halka_aciklik != "N/A" else "N/A"
                color = "green" if row['Değişim'] >= 0 else "red"
                sign = "▲" if row['Değişim'] >= 0 else "▼"

                st.markdown(f"""
                <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0;">
                    <strong>{hisse}</strong><br>
                    <i>Tarih: {row['Tarih']}</i><br>
                    Kapanış: <b>{row['Kapanış']}</b> <span style='color:{color}'>{sign} {abs(row['Değişim'])}%</span><br>
                    RSI: <b>{row['RSI']}</b> | Hacim/Ort: <b>{row['Hacim Katsayısı']}</b><br>
                    MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                    EMA89: <b>{row['EMA89']}</b><br>
                    <b>PD/DD:</b> {round(row['PD/DD'], 2) if row['PD/DD'] else 'N/A'}<br>
                    <b>Dolaşımdaki Lot:</b> {lot_str}<br>
                    <b>Halka Açıklık Oranı:</b> {halka_str}<br><br>
                    📊 <b>Finansal Oranlar</b><br>
                    F/K: <b>{info.get("trailingPE", "N/A")}</b><br>
                    Piyasa Değeri: <b>{market_cap_usd_str}</b>
                </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    plot_stock_chart(data_plot, hisse)
                else:
                    st.info(f"{hisse} için yeterli veri bulunamadı.")
