import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
import time

# Sayfa ayarları
st.set_page_config(page_title="BIST Tarama Botu", layout="wide")

# Başlık
st.title("BIST Hacim & Dip Taraması")

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

def scan_stocks(tickers):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="15d", interval="1d", progress=False)
            if data.empty:
                continue
            data.dropna(inplace=True)
            data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()

            avg_volume = data["Volume"].iloc[-6:-1].mean()
            today_volume = data["Volume"].iloc[-1]
            volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0

            rsi_now = data["RSI"].iloc[-1]
            lowest_10d = data["Close"].iloc[-10:].min()
            close_now = data["Close"].iloc[-1]
            is_near_bottom = close_now <= lowest_10d * 1.05

            if volume_ratio > 1.5 and (rsi_now < 30 or is_near_bottom):
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Hacim Artışı": f"{volume_ratio:.2f}x",
                    "RSI": round(rsi_now, 2),
                    "Kapanış": round(close_now, 2)
                })
        except:
            continue
        time.sleep(0.2)
    return pd.DataFrame(results)

# Arayüz: taramayı başlat
if st.button("Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        bist_tickers = get_bist_tickers()
        df = scan_stocks(bist_tickers)
        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            st.dataframe(df)

            # CSV olarak indir
            st.download_button("Excel Olarak İndir", df.to_csv(index=False), file_name="bist_tarama.csv")
