import streamlit as st

@st.cache_data(ttl=86400)
def get_all_bist_tickers():
    bist_all = [
        # Bankacılık endeksi hisseleri çıkarıldı
        # Halka Arz Endeksi hisseleri ve ek hisseler dahil edildi
        "A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "ADGYO.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGYO.IS",
        "AHGAZ.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS",
        "AKYHO.IS", "ALARK.IS", "ALBRK.IS", "ALCAR.IS", "ALCTL.IS", "ALGYO.IS", "ALKIM.IS", "ALMAD.IS", "ALYAG.IS", "ANACM.IS",
        "ANHYT.IS", "ANSGR.IS", "ARASE.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ARTI.IS", "ASELS.IS", "ASGYO.IS",
        "ASUZU.IS", "ATAGY.IS", "ATATP.IS", "ATLAS.IS", "ATYAT.IS", "AVHOL.IS", "AVGYO.IS", "AVOD.IS", "AVTUR.IS", "AYCES.IS",
        "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASCM.IS",
        "BAYRK.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIMAS.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BNTAS.IS",
        "BOBET.IS", "BOSSA.IS", "BRISA.IS", "BRKSN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS",
        "BRSAN.IS",  # Eklenen hisse
        "CANTE.IS", "CARSU.IS", "CASA.IS", "CATS.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CIMSA.IS", "CMENT.IS",
        "CLEBI.IS", "CLYHO.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DARDL.IS",
        "DENGE.IS", "DERHL.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGNMO.IS", "DGGYO.IS", "DIRIT.IS", "DITAS.IS",
        "DNISI.IS", "DOAS.IS", "DOBUR.IS", "DOGUB.IS", "DOHOL.IS", "DOMINO.IS", "DURDO.IS", "DYOBY.IS", "ECILC.IS", "ECZYT.IS",
        "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGGUB.IS", "EGPRO.IS", "EIS.IS", "EKGYO.IS", "EKIZ.IS", "ELITE.IS", "EMKEL.IS",
        "ENKAI.IS", "ENSRI.IS", "EPLAS.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCAR.IS", "ESEN.IS", "ETILR.IS", "EUHOL.IS",
        "EUREN.IS", "EUYO.IS", "FADE.IS", "FENER.IS", "FONET.IS", "FORMT.IS", "FROTO.IS", "GARFA.IS", "GEDIK.IS",
        "GEDZA.IS", "GENTS.IS", "GENIL.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GOLTS.IS", "GOZDE.IS",
        "GRNYO.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "HATEK.IS", "HEKTS.IS", "HDFGS.IS", "HKTM.IS", "HLGYO.IS",
        "HUBVC.IS", "ICBCT.IS", "IDEAS.IS", "IEYHO.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS",
        "INGRM.IS", "INTEM.IS", "INVEO.IS", "ISDMR.IS", "ISFIN.IS", "ISGYO.IS", "ISGSY.IS",
        "ISMEN.IS", "ISSEN.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "IZTAR.IS", "JANTS.IS", "KARSN.IS", "KARYE.IS", "KATMR.IS",
        "KCHOL.IS", "KERVT.IS", "KFEIN.IS", "KLGYO.IS", "KLKIM.IS", "KLSER.IS", "KLMSN.IS", "KMPUR.IS", "KNFRT.IS", "KONYA.IS",
        "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRSTL.IS", "KRVGD.IS", "KUTPO.IS", "LIDFA.IS",
        "LKMNH.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEGAP.IS", "MERCN.IS",
        "MERKO.IS", "MIPAZ.IS", "MMCAS.IS", "MNDRS.IS", "MNDTR.IS", "MRDIN.IS", "MRGYO.IS", "MSCLE.IS", "MSGYO.IS", "NETAS.IS",
        "NIBAS.IS", "NTHOL.IS", "NTTUR.IS", "NUGYO.IS", "ODAS.IS", "OLMIP.IS", "ORCAY.IS", "ORGE.IS", "OTKAR.IS", "OYLUM.IS",
        "OZKGY.IS", "PAPIL.IS", "PARSN.IS", "PENTA.IS", "PETKM.IS", "PGSUS.IS", "PKART.IS", "POLHO.IS", "PRKAB.IS", "PRKME.IS",
        "PSDTC.IS", "QUAGR.IS", "QNBFB.IS", "RAYSG.IS", "RALYH.IS", "RHEAG.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS",
        "RYGYO.IS",  # Eklenen hisse
        "RYSAS.IS", "SANEL.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SELEC.IS", "SILVR.IS", "SKBNK.IS", "SKTAS.IS", "SNPAM.IS",
        "SNKRN.IS", "SODA.IS", "SOKM.IS", "SOMTA.IS", "SONME.IS", "SRVGY.IS", "SUNTK.IS", "SUWEN.IS", "TABGD.IS",  # Eklenen hisse
        "TATGD.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TMCOM.IS", "TMSN.IS", "TOASO.IS", "TOLAS.IS",
        "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TTRAK.IS", "TUKAS.IS", "TURSG.IS", "TURSH.IS", "TURPS.IS", "TSPOR.IS", "TTRAK.IS",
        "ULKER.IS", "ULUUN.IS", "ULUSE.IS", "UZERB.IS", "VAKFN.IS", "VBTYZ.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKING.IS",
        "YAPRK.IS", "YATAS.IS", "YGGYO.IS", "YGYO.IS", "YUNSA.IS", "ZOREN.IS", "ZRGYO.IS",
        # Halka Arz Endeksi hisseleri
        "AGROT.IS", "AHSGY.IS", "AKFIS.IS", "ALKLC.IS", "ALTNY.IS", "ALVES.IS", "ARMGD.IS", "ARTMS.IS",
        "AVPGY.IS", "BEGYO.IS", "BIGCH.IS", "BORLS.IS", "CATES.IS", "CEMZY.IS", "DCTTR.IS", "DMRGD.IS", "DOFER.IS", "DURKN.IS",
        "EKOSE.IS", "ENERY.IS", "FORTE.IS", "GOLDS.IS", "GUNDG.IS", "HOROZ.IS", "KBORU.IS", "KOCMT.IS", "KZGY0.IS",
        "MARBL.IS", "MEKAG.IS", "MHRGY.IS", "OBAMS.IS", "OFSYM.IS", "ONRYT.IS", "OZYSR.IS", "REEDR.IS", "SEGMN.IS", "SKYMD.IS",
        "SMRVA.IS", "SURGY.IS", "TCKRC.IS", "VRGYO.IS", "YAYLA.IS", "YIGIT.IS"
    ]
    return bist_all
