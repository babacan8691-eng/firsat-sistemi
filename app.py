from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="BIST Katılım Analiz Paneli",
    page_icon="🟢",
    layout="wide",
)

# Giriş bilgileri
KULLANICI_ADI = "Cuma Babacan"
SIFRE = "784512"

# Geniş BIST katılım hisse ve BYF aday havuzu (.IS uzantılı)
# Kendi katılım listene göre istediğin sembolü ekleyip çıkarabilirsin.
KATILIM_HAVUZU = [
    {"kod": "TUPRS.IS", "ad": "Tüpraş", "tur": "Katılım Hisse"},
    {"kod": "BIMAS.IS", "ad": "BİM Mağazalar", "tur": "Katılım Hisse"},
    {"kod": "THYAO.IS", "ad": "Türk Hava Yolları", "tur": "Katılım Hisse"},
    {"kod": "ASELS.IS", "ad": "Aselsan", "tur": "Katılım Hisse"},
    {"kod": "ENKAI.IS", "ad": "Enka İnşaat", "tur": "Katılım Hisse"},
    {"kod": "EREGL.IS", "ad": "Ereğli Demir Çelik", "tur": "Katılım Hisse"},
    {"kod": "KCHOL.IS", "ad": "Koç Holding", "tur": "Katılım Hisse"},
    {"kod": "SAHOL.IS", "ad": "Sabancı Holding", "tur": "Katılım Hisse"},
    {"kod": "SASA.IS", "ad": "Sasa Polyester", "tur": "Katılım Hisse"},
    {"kod": "HEKTS.IS", "ad": "Hektaş", "tur": "Katılım Hisse"},
    {"kod": "PETKM.IS", "ad": "Petkim", "tur": "Katılım Hisse"},
    {"kod": "FROTO.IS", "ad": "Ford Otosan", "tur": "Katılım Hisse"},
    {"kod": "TOASO.IS", "ad": "Tofaş Oto", "tur": "Katılım Hisse"},
    {"kod": "ARCLK.IS", "ad": "Arçelik", "tur": "Katılım Hisse"},
    {"kod": "VESTL.IS", "ad": "Vestel", "tur": "Katılım Hisse"},
    {"kod": "GUBRF.IS", "ad": "Gübre Fabrikaları", "tur": "Katılım Hisse"},
    {"kod": "KONTR.IS", "ad": "Kontrolmatik", "tur": "Katılım Hisse"},
    {"kod": "ODAS.IS", "ad": "Odaş Elektrik", "tur": "Katılım Hisse"},
    {"kod": "KRDMD.IS", "ad": "Kardemir (D)", "tur": "Katılım Hisse"},
    {"kod": "SISE.IS", "ad": "Şişecam", "tur": "Katılım Hisse"},
    {"kod": "GLDTR.IS", "ad": "Altın Katılım BYF", "tur": "Katılım BYF"},
    {"kod": "GMSTR.IS", "ad": "Gümüş Katılım BYF", "tur": "Katılım BYF"},
]

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.title("Panel Girişi")
    st.caption("Kişisel analiz paneline erişmek için kullanıcı adı ve şifrenizi girin.")
    with st.form("giris_formu"):
        girilen_ad = st.text_input("Kullanıcı Adı")
        girilen_sifre = st.text_input("Şifre", type="password")
        gonder = st.form_submit_button("Giriş Yap")
        if gonder:
            if girilen_ad.strip() == KULLANICI_ADI and girilen_sifre.strip() == SIFRE:
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")
    st.stop()

# Üst başlık ve çıkış
sol_baslik, sag_buton = st.columns([6, 1])
with sol_baslik:
    st.title("BIST Katılım Otomatik Analiz Paneli")
    st.caption("Açılışta tek işlem • Günlük kâr veya akşam stop • Uygun olanlar en üstte")
with sag_buton:
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

# Türkiye saati ve 09:50 - 18:20 arası her 1 dakikada otomatik yenileme
tr_simdi = datetime.now(ZoneInfo("Europe/Istanbul"))
su_an = tr_simdi.time()
seans_aktif = time(9, 50) <= su_an <= time(18, 20)

if seans_aktif:
    st_autorefresh(interval=60 * 1000, key="bist_1dk_yenileme")
    st.success(f"Canlı Güncelleme Aktif (09:50 - 18:20 • Her 1 Dakika) — Son Güncelleme: {tr_simdi.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik 1 dakikalık yenileme 09:50 - 18:20 arasındadır. Şu anki saat: {tr_simdi.strftime('%H:%M:%S')}")

# Parametreler
st.sidebar.header("Sistem Parametreleri")
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)
min_odul_risk = st.sidebar.number_input("Min. Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_yuzde = st.sidebar.slider("Maks. Sabah Enerji Tüketimi (%)", min_value=20, max_value=90, value=60, step=5)
sadece_uygun_goster = st.sidebar.checkbox("Tabloda Sadece 🟢 UYGUN Olanları Göster", value=False)

toplam_maliyet_yuzde = (komisyon_binde / 10.0) + makas_yuzde


@st.cache_data(ttl=55)
def toplu_veri_cek(sembol_listesi):
    try:
        df = yf.download(
            tickers=sembol_listesi,
            period="10d",
            interval="1d",
            group_by="ticker",
            progress=False,
            auto_adjust=False,
            threads=True,
        )
        return df
    except Exception:
        return None


semboller = [x["kod"] for x in KATILIM_HAVUZU]
ham_veri = toplu_veri_cek(semboller)


def tek_sembol_df(ham, sembol):
    if ham is None or ham.empty:
        return None
    try:
        if isinstance(ham.columns, pd.MultiIndex):
            if sembol in ham.columns.get_level_values(0):
                sub = ham[sembol].copy()
            else:
                return None
        else:
            sub = ham.copy()
        if not {"High", "Low", "Close"}.issubset(set(sub.columns)):
            return None
        sub = sub.dropna(subset=["High", "Low", "Close"])
        if len(sub) < 2:
            return None
        return sub
    except Exception:
        return None


uygun_satirlar = []
bekle_satirlar = []
veri_yok_kodlar = []

for item in KATILIM_HAVUZU:
    kod = item["kod"]
    ad = item["ad"]
    tur = item["tur"]

    sub = tek_sembol_df(ham_veri, kod)
    if sub is None:
        veri_yok_kodlar.append(kod)
        continue

    gecmis = sub.iloc[-6:-1] if len(sub) >= 6 else sub.iloc[:-1]
    aralik_serisi = (gecmis["High"] - gecmis["Low"]).astype(float)
    ogh = float(aralik_serisi.mean()) if len(aralik_serisi) > 0 else 0.0

    son = sub.iloc[-1]
    son_fiyat = float(son["Close"])
    bugun_yuksek = float(son["High"])
    bugun_dusuk = float(son["Low"])
    bugun_aralik = max(0.0, bugun_yuksek - bugun_dusuk)

    enerji_oran = (bugun_aralik / ogh * 100.0) if ogh > 0 else 999.0

    risk_tutar = max(ogh * 0.30, son_fiyat * 0.008)
    hedef_tutar = risk_tutar * min_odul_risk

    stop_fiyat = max(0.01, son_fiyat - risk_tutar)
    hedef_fiyat = son_fiyat + hedef_tutar

    hedef_yuzde = (hedef_tutar / son_fiyat * 100.0) if son_fiyat > 0 else 0.0
    maliyet_esigi = toplam_maliyet_yuzde * 3.0

    enerji_ok = enerji_oran <= max_enerji_yuzde
    maliyet_ok = hedef_yuzde >= maliyet_esigi
    oran_ok = (hedef_tutar / risk_tutar) >= min_odul_risk if risk_tutar > 0 else False

    # Gün içi yön/durum senaryosu (gerçekleşmiş garanti değil, o anki fiyatın hedef/stop konumuna göre)
    if son_fiyat >= hedef_fiyat:
        senaryo = "Kârlı Hedef Bölgesi"
    elif son_fiyat <= stop_fiyat:
        senaryo = "Stop / Zarar Bölgesi"
    else:
        senaryo = "Hedef - Stop Arası"

    satir = {
        "Öncelik": 1 if (enerji_ok and maliyet_ok and oran_ok) else 2,
        "Durum": "🟢 UYGUN" if (enerji_ok and maliyet_ok and oran_ok) else "🔴 BEKLE",
        "Kod": kod,
        "Varlık": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH": round(ogh, 2),
        "Enerji": f"%{enerji_oran:.0f}" if enerji_oran < 900 else "-",
        "Hedef": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Senaryo": senaryo,
        "Not": (
            "Tüm kurallar sağlandı."
            if (enerji_ok and maliyet_ok and oran_ok)
            else ", ".join(
                [n for ok, n in [
                    (enerji_ok, "Enerji yüksek"),
                    (maliyet_ok, "Hedef/maliyet dar"),
                    (oran_ok, "Ödül/risk düşük"),
                ] if not ok]
            )
        ),
    }

    if satir["Öncelik"] == 1:
        uygun_satirlar.append(satir)
    else:
        bekle_satirlar.append(satir)

# Uygun olanları en üste al
sirali_satirlar = uygun_satirlar + bekle_satirlar

# Uygun olanlar arasında kârlı / zararlı senaryo sayımı
uygun_karli_adet = sum(1 for x in uygun_satirlar if x["Senaryo"] == "Kârlı Hedef Bölgesi")
uygun_zarar_adet = sum(1 for x in uygun_satirlar if x["Senaryo"] == "Stop / Zarar Bölgesi")
uygun_bekleyen_adet = sum(1 for x in uygun_satirlar if x["Senaryo"] == "Hedef - Stop Arası")

# Üst Özet Alanı
st.subheader("Uygun İşlem Özeti")
m1, m2, m3, m4 = st.columns(4)
m1.metric("🟢 Uygun Varlık Adedi", len(uygun_satirlar))
m2.metric("Hedef Bölgesinde (Kârlı Senaryo)", uygun_karli_adet)
m3.metric("Stop Bölgesinde (Zarar Senaryosu)", uygun_zarar_adet)
m4.metric("Hedef-Stop Arasında Açık Senaryo", uygun_bekleyen_adet)

st.divider()

# Tablo gösterimi
st.subheader("1. Sıralı Tarama Tablosu (Uygun Olanlar Üstte)")
if sadece_uygun_goster:
    gosterilecek = [ {k: v for k, v in s.items() if k != "Öncelik"} for s in uygun_satirlar ]
else:
    gosterilecek = [ {k: v for k, v in s.items() if k != "Öncelik"} for s in sirali_satirlar ]

if len(gosterilecek) > 0:
    st.dataframe(pd.DataFrame(gosterilecek), use_container_width=True, hide_index=True)
else:
    st.warning("Seçili kriterlere göre şu an 🟢 UYGUN statüsünde varlık bulunmuyor.")

if veri_yok_kodlar:
    st.caption(f"Veri kaynağında fiyat kaydı bulunamayan semboller (tabloya boş satır eklenmedi): {', '.join(veri_yok_kodlar)}")

st.divider()

# Detaylı inceleme bölümü
st.subheader("2. Detaylı Rakamsal İnceleme")
secenekler = [f"{s['Kod']} — {s['Varlık']}" for s in sirali_satirlar]
if secenekler:
    secili = st.selectbox("İncelemek istediğin varlığı seç:", secenekler)
    secili_kod = secili.split(" — ")[0].strip()
    detay = next((s for s in sirali_satirlar if s["Kod"] == secili_kod), None)
    if detay:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Son Fiyat", f"{detay['Son Fiyat']} TL")
        d2.metric("5 Günlük OGH", f"{detay['OGH']} TL")
        d3.metric("Kâr Hedefi", f"{detay['Hedef']} TL")
        d4.metric("Akşam Stop", f"{detay['Akşam Stop']} TL")

        st.markdown(
            f"""
            * **Genel Durum:** {detay['Durum']}
            * **Sabah Enerji Tüketimi:** {detay['Enerji']} (Sınır: %{max_enerji_yuzde})
            * **Mevcut Konum / Senaryo:** {detay['Senaryo']}
            * **Sistem Notu:** {detay['Not']}
            """
        )

st.divider()
st.caption(
    "Not: Bu ekran belirlenen rakamsal kurallara göre otomatik tarama yapar; kesin kâr garantisi vermez "
    "ve zararlı işlemler her zaman mümkündür. Emir vermeden önce kendi hesabınızdaki anlık veriyi ve katılım uygunluğunu kontrol edin."
)
