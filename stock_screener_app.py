def scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma):
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

            close = float(data["Close"].iloc[-1])
            prev_close = float(data["Close"].iloc[-2])
            change_pct = ((close - prev_close) / prev_close) * 100

            ma20 = float(data["MA20"].iloc[-1])
            ma50 = float(data["MA50"].iloc[-1])
            ma200 = float(data["MA200"].iloc[-1])
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

            if passes_ma and passes_volume:
                results.append({
                    "Hisse": ticker.replace(".IS", ""),
                    "Tarih": last_date,
                    "Kapanış": round(close, 2),
                    "Değişim": round(change_pct, 2),
                    "MA20": round(ma20, 2),
                    "MA50": round(ma50, 2),
                    "Hacim Katsayısı": round(volume_ratio, 2)
                })
        except Exception as e:
            st.write(f"Hata oluştu: {e} - Ticker: {ticker}")
            continue
        time.sleep(0.1)
    return pd.DataFrame(results)


# Arayüzde buton kısmı

if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Tüm BIST hisseleri taranıyor..."):
        tickers = get_all_bist_tickers()
        st.write("Tarama yapılacak tickers:", tickers)  # Ticker listesini yazdır

        df = scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma)

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")
            for _, row in df.iterrows():
                icon = "▲" if row['Değişim'] >= 0 else "▼"
                color = "green" if row['Değişim'] >= 0 else "red"

                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0; font-size:15px;">
                        <strong>{row['Hisse']}</strong><br>
                        <i>Veri tarihi: {row['Tarih']}</i><br>
                        Kapanış: <span style="color:{color}; font-weight:bold;">
                            {row['Kapanış']} ({icon} {abs(row['Değişim'])}%)
                        </span><br>
                        MA20: {row['MA20']} | MA50: {row['MA50']}<br>
                        Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b><br>
                """, unsafe_allow_html=True)

                ticker_full = row['Hisse'] + ".IS"
                data_plot = prepare_data_for_plot(ticker_full)
                if data_plot is not None:
                    rsi_latest = data_plot["RSI"].iloc[-1]
                    st.markdown(f"<b>RSI:</b> {rsi_latest:.2f}", unsafe_allow_html=True)

                    commentary = generate_commentary(
                        rsi_latest,
                        row['Hacim Katsayısı'],
                        row['Kapanış'],
                        row['MA20'],
                        row['MA50']
                    )
                    st.markdown(f"<b>Yorum:</b> {commentary} <br><i>Yatırım tavsiyesi değildir.</i>", unsafe_allow_html=True)

                    plot_stock_chart(data_plot, row['Hisse'])
                else:
                    st.info(f"{row['Hisse']} için grafik verisi yok.")

                st.markdown("</div>", unsafe_allow_html=True)
