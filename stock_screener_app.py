import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="BIST Dip & Hacim Taraması", layout="centered")
st.title("📉 BIST Dip & Hacim Taraması")

def scan_stocks(tickers, ma_tolerance, use_ma):
    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="60d", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                st.write(f"{ticker}: Veri yetersiz veya mevcut değil.")
                continue

            data.dropna(inplace=True)
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA200"] = data["Close"].rolling(200).mean()

            close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            ma200 = data["MA200"].iloc[-1]
            last_date = data.index[-1].strftime("%Y-%m-%d")
            volume = data["Volume"].iloc[-1]

            st.write(f"{ticker} - Son veri: {last_date} - Hacim: {volume}")

            is_near_ma20 = close < ma20 * (1 + ma_tolerance)
            is_near_ma50 = close < ma50 * (1 + ma_tolerance)
            is_near_ma200 = close < ma200 * (1 + ma_tolerance)
            near_any_ma = is_near_ma20 or is_near_ma50 or is_near_ma200

            if use_ma and not near_any_ma:
                continue

            results.append({
                "Hisse": ticker.replace(".IS", ""),
                "Tarih": last_date,
                "Kapanış": round(close, 2),
                "MA20": round(ma20, 2),
                "MA50": round(ma50, 2),
                "MA200": round(ma200, 2)
            })
        except Exception as e:
            st.write(f"{ticker} hata: {e}")
            continue
        time.sleep(0.2)
    return pd.DataFrame(results)

# Arayüz
st.sidebar.header("🔧 Filtre Ayarları")
ma_tolerance = st.sidebar.slider("MA Yakınlık Toleransı (%)", 1, 10, 5) / 100
use_ma = st.sidebar.checkbox("MA Dip Filtresi Kullan", value=True)

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Hisseler taranıyor..."):
        # Test için örnek hisseler
        test_tickers = ["AKBNK.IS", "THYAO.IS", "SISE.IS"]
        df = scan_stocks(test_tickers, ma_tolerance, use_ma)
        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: {row['Kapanış']}<br>
                        MA20: {row['MA20']} | MA50: {row['MA50']} | MA200: {row['MA200']}
                    </div>
                """, unsafe_allow_html=True)
