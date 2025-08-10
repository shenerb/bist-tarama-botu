import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers  # Bu modülün mevcut olduğunu varsayıyorum

st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")

st.title("📈 Hisse Analiz")

st.markdown("""
## Kullanım

1. **Filtre Ayarları** panelinden teknik filtrelerin parametrelerini seçin:  
   - MA yakınlık toleransı  
   - Hacim artış eşiği  
   - RSI dip seviyesi (isteğe bağlı)  
   - Bugün tavan yapan hisseleri filtreleme

2. Tarama yapmak istediğiniz hisseleri seçin veya boş bırakarak tüm hisseleri tarayın.

3. **Taramayı Başlat** butonuna tıklayın.

4. Filtreleme sonuçları listelenecek, her hisse için detaylı bilgiler ve teknik grafikler gösterilecektir.
""")

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

def calculate_trin(tickers):
    data = yf.download(tickers, period="2d", interval="1d", progress=False)
    if data.empty:
        return None, "Veri bulunamadı."

    if isinstance(data.columns, pd.MultiIndex):
        close = data['Close'].iloc[-2]
        prev_close = data['Close'].iloc[-3] if len(data) > 2 else None
        volume = data['Volume'].iloc[-2]
    else:
        close = pd.Series({tickers: data['Close'][-2]})
        prev_close = None
        volume = pd.Series({tickers: data['Volume'][-2]})

    # TRIN için bugünkü ve dünün kapanışları karşılaştırılır:
    if prev_close is None:
        # Tek gün veri varsa TRIN hesaplanamaz
        return None, "Yetersiz veri (tek gün)"

    advancing_issues = 0
    declining_issues = 0
    advancing_volume = 0
    declining_volume = 0

    for ticker in tickers:
        try:
            d = yf.download(ticker, period="2d", interval="1d", progress=False)
            if d.empty or len(d) < 2:
                continue
            close_today = d['Close'].iloc[-1]
            close_yesterday = d['Close'].iloc[-2]
            volume_today = d['Volume'].iloc[-1]

            if close_today > close_yesterday:
                advancing_issues += 1
                advancing_volume += volume_today
            elif close_today < close_yesterday:
                declining_issues += 1
                declining_volume += volume_today
        except:
            continue

    if declining_issues == 0 or declining_volume == 0:
        return None, "Yetersiz veri (sıfıra bölme)."

    trin = (advancing_issues / declining_issues) / (advancing_volume / declining_volume)

    return trin, None

# Sidebar filtreler
st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_volume = st.sidebar.checkbox("Hacim Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)
use_ceiling_filter = st.sidebar.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)

all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("📌 Tarama İçin Hisse Seç (boş bırak tümü için)", options=all_tickers)

scan_type = st.sidebar.selectbox("Tarama Türü", ["Normal Tarama", "TRIN Taraması"])

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        ceiling_threshold = 9.5 if use_ceiling_filter else None

        if scan_type == "Normal Tarama":
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
                        lot = f"{int(lot):,}".replace(",", ".")

                    halka_aciklik = halka_aciklik_dict.get(hisse, "N/A")

                    st.markdown(f"---\n### {hisse}  {row['Tarih']}")
                    st.write(f"Kapanış: {row['Kapanış']} ₺  |  Değişim: {row['Değişim']}%  |  MA20: {row['MA20']}  |  MA50: {row['MA50']}  |  Hacim Katsayısı: {row['Hacim Katsayısı']}  |  RSI: {row['RSI']}")
                    st.write(f"Piyasa Değeri (TRY): {market_cap_try if market_cap_try else 'N/A'}")
                    st.write(f"Piyasa Değeri (USD): {market_cap_usd_str}")
                    st.write(f"Dolaşımdaki Lot: {lot}")
                    st.write(f"Halka Açıklık Oranı: {halka_aciklik}")

                    data = prepare_data_for_plot(ticker_full)
                    if data is not None:
                        plot_stock_chart(data, hisse)
                    else:
                        st.info("Grafik için yeterli veri yok.")
        else:
            trin, error = calculate_trin(tickers_to_scan)
            if error:
                st.error(f"TRIN Hesaplanamadı: {error}")
            else:
                color = "green" if trin < 1 else "red"
                yorum = "Olumlu piyasa sinyali" if trin < 1 else "Olumsuz piyasa sinyali"
                st.markdown(f"""
                <div style="border:2px solid {color}; padding: 15px; border-radius: 10px; background-color: #f0f0f0;">
                    <h3 style="color:{color};">TRIN Değeri: {trin:.2f}</h3>
                    <p style="color:{color}; font-weight:bold;">{yorum}</p>
                </div>
                """, unsafe_allow_html=True)
