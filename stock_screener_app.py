import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="BIST Tarama Botu", layout="centered")
st.title("BIST Dip & Hacim Taraması")

@st.cache_data(ttl=3600)
def get_bist_tickers():
    url = "https://tr.investing.com/equities/turkey"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    tickers = []
    rows = soup.select("table.genTbl.closedTbl.elpTbl.elp20 tbody tr")
    for row in rows:
        try:
            code = row.select_one("td.left.bold.elp.plusIconTd a").text.strip()
            tickers.append(code + ".IS")
        except:
            continue
    return list(set(tickers))

def scan_stocks(tickers, volume_threshold, ma_tolerance, use_volume, use_ma):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="60d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue
            data.dropna(inplace=True)

            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()

            avg_volume = data["Volume"].iloc[-6:-1].mean()
            today_volume = data["Volume"].iloc[-1]
            volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0

            close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            ma200 = data["MA200"].iloc[-1]

            is_near_ma20 = close < ma20 * (1 + ma_tolerance)
            is_near_ma50 = close < ma50 * (1 + ma_tolerance)
            is_near_ma200 = close < ma200 * (1 + ma_tolerance)
            near_any_ma = is_near_ma20 or is_near_ma50 or is_near_ma200

            passes_volume = volume_ratio >= volume_threshold
            passes_ma = near_any_ma
            last_date = data.index[-1].strftime("%Y-%m-%d")

            if (
                (use_volume and use_ma and passes_volume and passes_ma)
                or (use_volume and not use_ma and passes_volume)
                or (not use_volume and use_ma and passes_ma)
            ):
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": last_date,
                    "Kapanış": round(close, 2),
                    "Hacim Oranı": f"{volume_ratio:.2f}x",
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "MA200": round(ma200, 2)
                })
        except:
            continue
        time.sleep(0.2)
    return pd.DataFrame(results)

# Arayüz
st.sidebar.header("Filtre Ayarları")
volume_threshold = st.sidebar.slider("Minimum Hacim Artış (x)", 1.0, 5.0, 1.2, 0.1)
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
use_volume = st.sidebar.checkbox("Hacim Filtresi Kullan", value=True)
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)

if st.button("Taramayı Başlat"):
    with st.spinner("BIST hisseleri taranıyor..."):
        bist_tickers = get_bist_tickers()
        df = scan_stocks(bist_tickers, volume_threshold, ma_tolerance, use_volume, use_ma)
        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı. Borsa kapalı olabilir veya filtreler çok sıkı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for i, row in df.iterrows():
                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: {row['Kapanış']}<br>
                        Hacim Oranı: {row['Hacim Oranı']}<br>
                        MA20: {row['MA20']} | MA50: {row['MA50']} | MA200: {row['MA200']}
                    </div>
                """, unsafe_allow_html=True)

            st.download_button("Excel Olarak İndir", df.to_csv(index=False), file_name="bist_tarama_sonuclar.csv")
