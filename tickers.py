# tickers.py

@st.cache_data(ttl=86400)
def get_all_bist_tickers():
    bist_all = [
        "AKBNK.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS", "BRSAN.IS", "CIMSA.IS",
        "DOHOL.IS", "ECILC.IS", "EGEEN.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS",
        "GARAN.IS", "GUBRF.IS", "HALKB.IS", "HEKTS.IS", "ISCTR.IS", "ISGYO.IS", "KARSN.IS",
        "KCHOL.IS", "KRDMD.IS", "KOZAA.IS", "KOZAL.IS", "LOGO.IS", "MGROS.IS", "ODAS.IS",
        "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "SKBNK.IS", "TCELL.IS",
        "THYAO.IS", "TKFEN.IS", "TOASO.IS", "TRGYO.IS", "TSKB.IS", "TTRAK.IS", "TUPRS.IS",
        "VAKBN.IS", "VESTL.IS", "YKBNK.IS", "ZOREN.IS", "QUAGR.IS", "SNGYO.IS", "AYDEM.IS",
        "ESEN.IS", "ULKER.IS", "BIOEN.IS", "GESAN.IS", "CANTE.IS", "NTHOL.IS", "KMPUR.IS",
        "OZKGY.IS", "KORDS.IS", "GSDHO.IS", "MAVI.IS", "TMSN.IS", "VERUS.IS", "TMPOL.IS",
        # Listeyi ihtiyacınıza göre genişletebilirsiniz
    ]
    return bist_all
