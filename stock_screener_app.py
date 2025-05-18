import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="BIST MA & Hacim Tarama", layout="wide")
st.title("BIST Dip & Hacim Artışı Taraması (MA20/50/200 + RSI)")

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

def scan_stocks(tickers, volume_threshold):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="60d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue
            data.dropna(inplace=True)

            # Hareketli ortalamalar
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()

            # RSI
            data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()

            # Hacim analizi
            avg_volume = data["Volume"].iloc[-6:-1].mean()
            today_volume = data["Volume"].iloc[-1]
            volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0

            close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            ma200 = data["MA200"].iloc[-1]

            is_below_ma20 = close < ma20 * 1.01
            is_below_ma50 = close < ma50 * 1.01
            is_below_ma200 = close < ma200 * 1.01
            near_bottom = is_below_ma20 or is_below_ma50 or is_below_ma200

            if volume_ratio >= volume_threshold and near_bottom:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Kapanış": round(close, 2),
                    "Hacim Oranı": f"{volume_ratio:.2f}x",
                    "RSI": round(data["RSI"].iloc[-1], 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "MA200": round(ma200, 2)
                })
        except:
            continue
        time.sleep(0.2)
    return pd.DataFrame(results)

# Arayüz: kullanıcıdan eşik değeri al
volume_threshold = st.slider("Minimum Hacim Artış Oranı (örneğin 1.5x)", 1.0, 5.0, 1.5, 0.1)

if st.button("Taramayı Başlat"):
    with st.spinner("BIST hisseleri taranıyor..."):
        bist_tickers = get_bist_tickers()
        df = scan_stocks(bist_tickers, volume_threshold)
        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            st.dataframe(df)
            st.download_button("Excel Olarak İndir", df.to_csv(index=False), file_name="bist_ma_tarama.csv")
