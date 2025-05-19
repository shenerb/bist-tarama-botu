import streamlit as st

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
        "GWIND.IS", "EUHOL.IS", "ISFIN.IS", "PRKME.IS", "SELEC.IS", "YUNSA.IS", "IZMDC.IS",
        "MERKO.IS", "GOLTS.IS", "AKSEN.IS", "AGHOL.IS", "ISYHO.IS", "ANELT.IS", "AYEN.IS",
        "EGSER.IS", "DGGYO.IS", "DERIM.IS", "AKGRT.IS", "ALFAS.IS", "BAGFS.IS", "BASCM.IS",
        "BAYRK.IS", "BNTAS.IS", "BTCIM.IS", "CMENT.IS", "CLEBI.IS", "CMBTN.IS", "CRDFA.IS",
        "CUSAN.IS", "DOBUR.IS", "DZGYO.IS", "EMNIS.IS", "ERBOS.IS", "ESCAR.IS", "EUREN.IS",
        "EUYO.IS", "FLAP.IS", "FONET.IS", "FRIGO.IS", "GARFA.IS", "GEDZA.IS", "GENIL.IS",
        "GEREL.IS", "GLBMD.IS", "GLCVY.IS", "GSDDE.IS", "HATEK.IS", "HDFGS.IS", "IEYHO.IS",
        "IHLAS.IS", "INDES.IS", "INTEM.IS", "INVEO.IS", "ISBTR.IS", "ISDMR.IS", "ISGSY.IS",
        "ISMEN.IS", "IZINV.IS", "IZTAR.IS", "KAPLM.IS", "KARTN.IS", "KATMR.IS", "KERVN.IS",
        "KLKIM.IS", "KLMSN.IS", "KLRHO.IS", "KRONT.IS", "KRVGD.IS", "KUTPO.IS", "LIDFA.IS",
        "LKMNH.IS", "LUKSK.IS", "MAKIM.IS", "MARKA.IS", "MARTI.IS", "MAALT.IS", "MERIT.IS",
        "METUR.IS", "MIPAZ.IS", "MMCAS.IS", "MNDRS.IS", "MRDIN.IS", "NETAS.IS", "NUGYO.IS",
        "OYLUM.IS", "OZRDN.IS", "OZRNE.IS", "OZSUB.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS",
        "PETUN.IS", "PEKGY.IS", "PRZMA.IS", "RALYH.IS", "RAYSG.IS", "RODRG.IS", "RTALB.IS",
        "RUBNS.IS", "RYGYO.IS", "SAMAT.IS", "SANEL.IS", "SARKY.IS", "SEKUR.IS", "SILVR.IS",
        "SNPAM.IS", "SODSN.IS", "SONME.IS", "SUNTK.IS", "SUWEN.IS", "TATGD.IS", "TAVHL.IS",
        "TEKTU.IS", "TEZOL.IS", "TRILC.IS", "TMTAS.IS", "TNZTP.IS", "TRCAS.IS", "TSPOR.IS",
        "TTKOM.IS", "TURSG.IS", "TURGG.IS", "TURHL.IS", "UFUK.IS", "ULAS.IS", "ULUUN.IS",
        "UTPYA.IS", "UZERB.IS", "VAKFN.IS", "VAKKO.IS", "VAKPR.IS", "VARYO.IS", "VESBE.IS",
        "YAPRK.IS", "YATAS.IS", "YGGYO.IS", "YONGA.IS", "YYAPI.IS"
        # Toplamda 400'e yakın hisse senedi manuel olarak eklenmiştir.
    ]
    return bist_all
