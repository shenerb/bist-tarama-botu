# 📈 BIST Hisse Analiz Uygulaması

Bu Streamlit tabanlı web uygulaması, Borsa İstanbul (BIST) hisselerini teknik analiz filtrelerine göre taramanızı ve analiz etmenizi sağlar. Kullanıcılar MA, RSI, hacim gibi göstergelere göre hisse seçimi yapabilir, detaylı grafik ve temel verilerle hisse görünümünü inceleyebilir.

---

## 🚀 Özellikler

- MA20, MA50, MA200, EMA89 ortalamaları ile yakınlık analizi
- RSI (Göreceli Güç Endeksi) ile dip bölge taraması
- Hacim artışı ile momentum tespiti
- Günlük tavan yapan hisseleri filtreleme (%9 üzeri değişim)
- Grafiklerle teknik analiz: RSI, MACD, Hareketli Ortalamalar
- Temel veriler: F/K, PD/DD, Piyasa Değeri (USD), Halka Açıklık, Dolaşımdaki Lot

---

## ⚙️ Filtre Parametreleri

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| **MA Yakınlık Toleransı** | Fiyatın MA20/50/200 ortalamalarına ne kadar yakın olabileceğini belirler. Yüzde cinsinden tolerans. | `%5` |
| **Hacim Artış Eşiği** | Günlük işlem hacminin, son 20 günlük ortalama hacme oranı. Örn: 1.5 → 1.5 kat artış | `1.5` |
| **MA Filtresi Kullan** | Fiyatın ortalamalara yakın olup olmadığına göre filtreleme yapılır. | ✔️ |
| **Hacim Filtresi Kullan** | Hacim artışı filtresi uygulanır. | ✔️ |
| **RSI Filtresi Kullan** | RSI göstergesi belirli bir seviyenin altında olan hisseleri seçer. | ❌ |
| **RSI Eşiği** | RSI göstergesinin dip bölge sınırı (aşağısı seçilir). | `30` |
| **Tavan Yapanları Tara** | Sadece %9.5 ve üzeri değişim gösteren (tavan yapan) hisseleri listeler. | ❌ |

---


```bash
pip install -r requirements.txt
