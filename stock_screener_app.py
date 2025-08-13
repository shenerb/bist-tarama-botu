import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt
from tickers import get_all_bist_tickers  # Bu modülün mevcut olduğunu varsayıyorum

# ======================= Uygulama Ayarları =======================
st.set_page_config(page_title="BIST Hisse Analiz", layout="centered")
st.title("📈 Hisse Analiz")

# ======================= Kullanım =======================
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

5. Piyasa geneli TRIN analizi için sol menüden **📊 Piyasa TRIN Analizi** butonuna tıklayın (otomatik çalışmaz).
""")

# ======================= Veri Yükleme =======================
@st.cache_data
def load_halaciklik_data():
    df_ozet = pd.read_excel("temelozet.xlsx")
    df_ozet["Kod"] = df_ozet["Kod"].str.strip().str.upper()
    return df_ozet.set_index("Kod")["Halka Açıklık Oranı (%)"].to_dict()

@st.cache_data
def load_lot_data():
    df_lot = pd.read_csv("dolasim_lot.csv", sep=None, engine='python')
    df_lot["Kod"] = df_lot["Kod"].str.strip().str.upper()
    return df_lot.set_index("Kod")["Dolasimdaki_Lot"].to_dict()

halka_aciklik_dict = load_halaciklik_data()
dolasim_lot_dict = load_lot_data()

# ======================= Teknik Hesaplamalar =======================
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

# ======================= Grafik Hazırlama =======================
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

    # İmza
    fig.text(0.5, 0.5, 'Bay-P', fontsize=50, color='gray', alpha=0.15,
             ha='center', va='center', weight='bold', style='italic', rotation=20)

    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# ======================= Tarama =======================
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
            rsi_latest = float(data["RSI"].iloc[-1])
            last_date = data.index[-1].strftime("%Y-%m-%d")
            volume = int(data["Volume"].iloc[-1])
            avg_volume = float(data["AvgVolume20"].iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            passes_ma = (close < min(ma20, ma50, ma200) * (1 + ma_tolerance)) if use_ma else True
            passes_volume = (volume_ratio >= volume_threshold) if use_volume else True
            passes_rsi = (rsi_latest <= rsi_threshold) if use_rsi else True

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

# ======================= TRIN =======================
def _safe_row_values(df: pd.DataFrame, date) -> tuple | None:
    """
    Verilen tarihteki satırı güvenle tek satıra indirip (Series),
    Close, Prev_Close, Volume değerlerini skalar olarak döndürür.
    Değer yoksa veya NaN ise None döner.
    """
    try:
        entry = df.loc[date]
    except KeyError:
        return None

    # entry Series ya da DataFrame olabilir (duplicate indeks durumunda)
    if isinstance(entry, pd.DataFrame):
        entry = entry.iloc[0]

    try:
        prev_close = entry["Prev_Close"]
        close = entry["Close"]
        vol = entry["Volume"]
    except KeyError:
        return None

    if pd.isna(prev_close) or pd.isna(close) or pd.isna(vol):
        return None

    try:
        return float(close), float(prev_close), float(vol)
    except Exception:
        return None

def calculate_trin_for_market(tickers, start="2024-01-01", end=None):
    # Hisse verilerini topla
    all_data = {}
    for t in tickers:
        df = yf.download(t, start=start, end=end, interval="1d", progress=False)
        if df.empty or len(df) < 2:
            continue
        df = df[['Close', 'Volume']].copy()
        df['Prev_Close'] = df['Close'].shift(1)
        all_data[t] = df

    if not all_data:
        return pd.DataFrame(columns=["TRIN"])

    # Tüm tarihler
    all_dates = sorted(set().union(*[df.index for df in all_data.values()]))

    records = []
    for date in all_dates:
        adv_issues = dec_issues = 0
        adv_vol = dec_vol = 0.0

        for df in all_data.values():
            vals = _safe_row_values(df, date)
            if vals is None:
                continue
            close_val, prev_close_val, vol_val = vals

            if close_val > prev_close_val:
                adv_issues += 1
                adv_vol += vol_val
            elif close_val < prev_close_val:
                dec_issues += 1
                dec_vol += vol_val
            # eşitlik halinde nötr sayıyoruz (ne adv ne dec)

        if adv_issues > 0 and dec_issues > 0 and adv_vol > 0 and dec_vol > 0:
            trin = (adv_issues / dec_issues) / (adv_vol / dec_vol)
            records.append({"Date": date, "TRIN": trin})

    df_trin = pd.DataFrame(records).set_index("Date")
    if df_trin.empty:
        return df_trin

    df_trin["TRIN_RSI"] = calculate_rsi(df_trin["TRIN"], 14)
    return df_trin

# ======================= Sidebar =======================
st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
volume_threshold = st.sidebar.slider("Hacim Artış Eşiği (kat)", 0.0, 5.0, 1.5)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)
use_volume = st.sidebar.checkbox("Hacim Filtresi Kullan", value=True)
use_rsi = st.sidebar.checkbox("RSI Dip Filtresi Kullan", value=False)
rsi_threshold = st.sidebar.slider("RSI Eşiği", 10, 50, 30)
use_ceiling_filter = st.sidebar.checkbox("Bugün Tavan Yapanları Tara (≥ %9)", value=False)

# Hisse Seçimi
all_tickers = get_all_bist_tickers()
selected_tickers = st.sidebar.multiselect("📌 Tarama İçin Hisse Seç (boş bırak tümü için)", options=all_tickers)

# ======================= Tarama Çalıştır =======================
if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        tickers_to_scan = selected_tickers if selected_tickers else all_tickers
        ceiling_threshold = 9.5 if use_ceiling_filter else None

        df = scan_stocks(
            tickers_to_scan, ma_tolerance, volume_threshold,
            use_ma, use_volume, use_rsi, rsi_threshold, ceiling_threshold
        )

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                hisse = row['Hisse']
                ticker_full = hisse + ".IS"

                # Temel bilgiler
                try:
                    info = yf.Ticker(ticker_full).info
                except Exception:
                    info = {}

                # USD cinsi piyasa değeri
                try:
                    usdtry = yf.Ticker("USDTRY=X").info.get("regularMarketPrice", None)
                except Exception:
                    usdtry = None

                market_cap_try = info.get("marketCap", None)
                if market_cap_try and usdtry:
                    mcap_usd = market_cap_try / usdtry
                    if mcap_usd >= 1e9:
                        market_cap_usd_str = f"{mcap_usd / 1e9:.2f} Milyar $"
                    elif mcap_usd >= 1e6:
                        market_cap_usd_str = f"{mcap_usd / 1e6:.2f} Milyon $"
                    else:
                        market_cap_usd_str = f"{mcap_usd:.0f} $"
                else:
                    market_cap_usd_str = "N/A"

                lot = dolasim_lot_dict.get(hisse, "N/A")
                if lot != "N/A":
                    lot = f"{int(lot):,}".replace(",", ".")

                halka_aciklik = halka_aciklik_dict.get(hisse, "N/A")
                if halka_aciklik != "N/A":
                    halka_aciklik = f"%{halka_aciklik:.2f}"

                color = "green" if row['Değişim'] >= 0 else "red"
                sign = "▲" if row['Değişim'] >= 0 else "▼"

                st.markdown(f"""
                <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0;">
                    <strong>{hisse}</strong><br>
                    <i>Tarih: {row['Tarih']}</i><br>
                    Kapanış: <b>{row['Kapanış']}</b> <span style='color:{color}'>{sign} {abs(row['Değişim'])}%</span><br>
                    RSI: <b>{row['RSI']}</b> | Hacim/Ort: <b>{row['Hacim Katsayısı']}</b><br>
                    MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                    <b>Dolaşımdaki Lot:</b> {lot}<br>
                    <b>Halka Açıklık Oranı:</b> {halka_aciklik}<br><br>
                    📊 <b>Finansal Oranlar</b><br>
                    F/K: <b>{info.get("trailingPE", "N/A")}</b><br>
                    PD/DD: <b>{info.get("priceToBook", "N/A")}</b><br>
                    Piyasa Değeri: <b>{market_cap_usd_str}</b>
                </div>
                """, unsafe_allow_html=True)

                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    plot_stock_chart(data_plot, hisse)
                else:
                    st.info(f"{hisse} için yeterli veri bulunamadı.")

# ======================= TRIN Butonu (isteğe bağlı çalışır) =======================
if st.sidebar.button("📊 Piyasa TRIN Analizi"):
    with st.spinner("Piyasa TRIN hesaplanıyor..."):
        trin_df = calculate_trin_for_market(all_tickers, start="2024-01-01")

    if trin_df.empty:
        st.warning("TRIN hesaplanacak yeterli veri oluşturulamadı.")
    else:
        trin_df = trin_df.copy()
        st.subheader("📊 Piyasa TRIN ve TRIN RSI(14)")
        st.dataframe(trin_df.round(3))

        fig, ax1 = plt.subplots(figsize=(12, 5))
        ax1.plot(trin_df.index, trin_df["TRIN"], label="TRIN", color="blue")
        ax1.axhline(1, color="gray", linestyle="--", linewidth=1)
        ax1.set_ylabel("TRIN", color="blue")
        ax1.tick_params(axis='y', labelcolor="blue")

        ax2 = ax1.twinx()
        ax2.plot(trin_df.index, trin_df["TRIN_RSI"], label="TRIN RSI (14)", color="orange")
        ax2.axhline(70, color="red", linestyle="--", linewidth=1)
        ax2.axhline(30, color="green", linestyle="--", linewidth=1)
        ax2.set_ylabel("TRIN RSI", color="orange")
        ax2.tick_params(axis='y', labelcolor="orange")

        fig.tight_layout()
        st.pyplot(fig)
