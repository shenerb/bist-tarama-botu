if st.button("🔍 Taramayı Başlat"):
    with st.spinner("Tüm BIST hisseleri taranıyor..."):
        tickers = get_all_bist_tickers()
        df = scan_stocks(tickers, ma_tolerance, volume_threshold, use_ma, use_rsi, rsi_threshold)

        if df.empty:
            st.warning("Kriterlere uyan hisse bulunamadı.")
        else:
            st.success(f"{len(df)} hisse bulundu.")

            # ✅ Autocomplete arama kutusu
            hisse_listesi = df["Hisse"].tolist()
            selected_hisse = st.selectbox("🔎 Hisse ara (autocomplete):", ["Tümünü Göster"] + hisse_listesi)

            # Eğer belirli bir hisse seçilmişse, sadece onu filtrele
            if selected_hisse != "Tümünü Göster":
                df = df[df["Hisse"] == selected_hisse]

            if df.empty:
                st.warning("Aramaya uyan hisse bulunamadı.")
            else:
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
                            RSI: <b>{row['RSI']}</b><br>
                            Hacim/Ort.: <b>{row['Hacim Katsayısı']}</b><br>
                    """, unsafe_allow_html=True)

                    ticker_full = row['Hisse'] + ".IS"
                    data_plot = prepare_data_for_plot(ticker_full)
                    if data_plot is not None:
                        rsi_latest = data_plot["RSI"].iloc[-1]
                        macd_comment = generate_macd_commentary(data_plot["MACD_Line"], data_plot["MACD_Signal"])

                        st.markdown(f"<b>RSI:</b> {rsi_latest:.2f}", unsafe_allow_html=True)
                        st.markdown(f"<b>MACD:</b> {macd_comment}", unsafe_allow_html=True)

                        commentary = generate_commentary(
                            rsi_latest,
                            row['Hacim Katsayısı'],
                            row['Kapanış'],
                            row['MA20'],
                            row['MA50']
                        )
                        st.markdown(f"<i>{commentary}</i>", unsafe_allow_html=True)

                        plot_stock_chart(data_plot, row['Hisse'])

                    st.markdown("</div>", unsafe_allow_html=True)
