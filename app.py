from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="BIST Katılım Profesyonel Analiz & Sanal İşlem Paneli",
    page_icon="🟢",
    layout="wide",
)

# Giriş bilgileri
KULLANICI_ADI = "Cuma Babacan"
SIFRE = "784512"

# Geniş BIST katılım hisse ve BYF havuzu (.IS uzantılı)
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

# Sanal işlem defteri ve sayaçlar
if "acik_islemler" not in st.session_state:
    st.session_state.acik_islemler = {}  # kod -> dict
if "kapanan_islemler" not in st.session_state:
    st.session_state.kapanan_islemler = []  # list of dict
if "kar_adet" not in st.session_state:
    st.session_state.kar_adet = 0
if "zarar_adet" not in st.session_state:
    st.session_state.zarar_adet = 0
if "net_kar_zarar_tl" not in st.session_state:
    st.session_state.net_kar_zarar_tl = 0.0

if not st.session_state.giris_yapildi:
    st.title("Panel Girişi")
    st.caption("Kişisel analiz ve takip paneline erişmek için bilgilerinizi girin.")
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

# Başlık ve kontrol butonları
ust_sol, ust_orta, ust_sag = st.columns([5, 2, 1])
with ust_sol:
    st.title("BIST Katılım Profesyonel Analiz & Simülasyon Paneli")
    st.caption("Açılışta tek işlem • Günlük kâr veya akşam stop • Sanal otomatik al-sat ve kâr/zarar sayacı")
with ust_orta:
    st.write("")
    if st.button("Sanal Sayacı Sıfırla"):
        st.session_state.acik_islemler = {}
        st.session_state.kapanan_islemler = []
        st.session_state.kar_adet = 0
        st.session_state.zarar_adet = 0
        st.session_state.net_kar_zarar_tl = 0.0
        st.rerun()
with ust_sag:
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
    st.success(f"Canlı Güncelleme Aktif (09:50 - 18:20 • 1 Dakika) — Son Güncelleme: {tr_simdi.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik 1 dakikalık yenileme 09:50 - 18:20 arasındadır. Şu anki saat: {tr_simdi.strftime('%H:%M:%S')}")

# Yan menü ayarları
st.sidebar.header("Sistem & Simülasyon Ayarları")
sanal_islem_tutari = st.sidebar.number_input("İşlem Başına Sanal Tutar (TL)", min_value=100.0, max_value=1000000.0, value=10000.0, step=500.0)
min_teyit_puani = st.sidebar.slider("Oto-Alım İçin Min. Teyit Puanı (0-100)", min_value=50, max_value=100, value=75, step=5)
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)
min_odul_risk = st.sidebar.number_input("Min. Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_yuzde = st.sidebar.slider("Maks. Sabah Enerji Tüketimi (%)", min_value=20, max_value=90, value=60, step=5)
oto_sanal_aktif = st.sidebar.checkbox("Uygun Olanları Sanal Olarak Otomatik Al/Sat", value=True)
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


ham_veri = toplu_veri_cek([x["kod"] for x in KATILIM_HAVUZU])

uygun_satirlar = []
bekle_satirlar = []
veri_yok_kodlar = []

# Önce açık sanal pozisyonların çıkış (hedef / stop / akşam kapanış) kontrolünü yap
for kod, poz in list(st.session_state.acik_islemler.items()):
    sub = tek_sembol_df(ham_veri, kod)
    if sub is None:
        continue
    guncel_fiyat = float(sub.iloc[-1]["Close"])
    hedef = poz["hedef"]
    stop = poz["stop"]
    adet = poz["adet"]
    giris = poz["giris"]

    cikis_nedeni = None
    cikis_fiyat = guncel_fiyat

    if guncel_fiyat >= hedef:
        cikis_nedeni = "Kâr Hedefi Tamamlandı"
        cikis_fiyat = hedef
    elif guncel_fiyat <= stop:
        cikis_nedeni = "Akşam Stop Çalıştı"
        cikis_fiyat = stop
    elif su_an >= time(18, 0):
        cikis_nedeni = "Seans Sonu Kapanış"
        cikis_fiyat = guncel_fiyat

    if cikis_nedeni is not None:
        brut_kz = (cikis_fiyat - giris) * adet
        maliyet_tl = (giris * adet + cikis_fiyat * adet) * (toplam_maliyet_yuzde / 100.0)
        net_kz = brut_kz - maliyet_tl

        st.session_state.net_kar_zarar_tl += net_kz
        if net_kz >= 0:
            st.session_state.kar_adet += 1
        else:
            st.session_state.zarar_adet += 1

        st.session_state.kapanan_islemler.insert(0, {
            "Saat": tr_simdi.strftime("%H:%M:%S"),
            "Kod": kod,
            "Giriş": round(giris, 2),
            "Çıkış": round(cikis_fiyat, 2),
            "Net K/Z (TL)": round(net_kz, 2),
            "Sonuç": "KÂRLI" if net_kz >= 0 else "ZARAR",
            "Neden": cikis_nedeni,
        })
        del st.session_state.acik_islemler[kod]

# Piyasa taraması ve teyit puanı hesabı
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

    onceki_kapanis = float(gecmis.iloc[-1]["Close"]) if len(gecmis) > 0 else float(sub.iloc[-1]["Close"])
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
    kapanis_ustu_ok = son_fiyat >= onceki_kapanis

    # 100 üzerinden çoklu doğrulama / teyit puanı
    puan = 0
    puan += 35 if enerji_ok else (15 if enerji_oran <= max_enerji_yuzde + 15 else 0)
    puan += 25 if maliyet_ok else 0
    puan += 25 if oran_ok else 0
    puan += 15 if kapanis_ustu_ok else 5

    uygun_mu = enerji_ok and maliyet_ok and oran_ok

    # Uygun ve puanı yeterliyse sanal otomatik alım aç (her varlık için en fazla 1 açık işlem)
    if (
        oto_sanal_aktif
        and uygun_mu
        and puan >= min_teyit_puani
        and kod not in st.session_state.acik_islemler
        and son_fiyat > 0
        and seans_aktif
    ):
        adet = sanal_islem_tutari / son_fiyat
        st.session_state.acik_islemler[kod] = {
            "kod": kod,
            "ad": ad,
            "giris": son_fiyat,
            "hedef": hedef_fiyat,
            "stop": stop_fiyat,
            "adet": adet,
            "saat": tr_simdi.strftime("%H:%M:%S"),
        }

    # Açık sanal pozisyon varsa anlık kâr/zararı hesapla
    if kod in st.session_state.acik_islemler:
        poz = st.session_state.acik_islemler[kod]
        anlik_kz = (son_fiyat - poz["giris"]) * poz["adet"]
        sanal_durum = f"Açık ({anlik_kz:+.2f} TL)"
    else:
        sanal_durum = "Pozisyon Yok"

    nedenler = []
    if not enerji_ok:
        nedenler.append("Enerji yüksek")
    if not maliyet_ok:
        nedenler.append("Hedef/maliyet dar")
    if not oran_ok:
        nedenler.append("Ödül/risk düşük")
    if not kapanis_ustu_ok:
        nedenler.append("Önceki kapanış altında")

    satir = {
        "Oncelik": 1 if uygun_mu else 2,
        "Puan": puan,
        "Durum": "🟢 UYGUN" if uygun_mu else "🔴 BEKLE",
        "Kod": kod,
        "Varlık": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH": round(ogh, 2),
        "Enerji": f"%{enerji_oran:.0f}" if enerji_oran < 900 else "-",
        "Hedef": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Sanal İşlem": sanal_durum,
        "Not": "Tüm temel kurallar sağlandı." if uygun_mu else ", ".join(nedenler),
    }

    if uygun_mu:
        uygun_satirlar.append(satir)
    else:
        bekle_satirlar.append(satir)

# Uygun olanları en üste, kendi içinde Teyit Puanına göre sırala
uygun_satirlar.sort(key=lambda x: x["Puan"], reverse=True)
bekle_satirlar.sort(key=lambda x: x["Puan"], reverse=True)
sirali_satirlar = uygun_satirlar + bekle_satirlar

# Açık sanal işlemlerin anlık yüzen K/Z toplamı
acik_yuzen_kz = 0.0
for kod, poz in st.session_state.acik_islemler.items():
    sub = tek_sembol_df(ham_veri, kod)
    if sub is not None:
        guncel = float(sub.iloc[-1]["Close"])
        acik_yuzen_kz += (guncel - poz["giris"]) * poz["adet"]

# Kâr / Zarar Sayacı Alanı
st.subheader("Canlı Kâr / Zarar Sayacı (Sanal Otomatik Sistem)")
s1, s2, s3, s4, s5 = st.columns(5)
s1.metric("🟢 Uygun Varlık", len(uygun_satirlar))
s2.metric("Kârlı Kapanan İşlem", st.session_state.kar_adet)
s3.metric("Zararlı Kapanan İşlem", st.session_state.zarar_adet)
s4.metric("Kapanan Net K/Z", f"{st.session_state.net_kar_zarar_tl:+.2f} TL")
s5.metric("Açık Pozisyon / Anlık K/Z", f"{len(st.session_state.acik_islemler)} ({acik_yuzen_kz:+.2f} TL)")

st.divider()

# Sıralı tarama tablosu
st.subheader("1. Sıralı Tarama Tablosu (Uygun Olanlar En Üstte)")
kaynak_liste = uygun_satirlar if sadece_uygun_goster else sirali_satirlar
temiz_tablo = [{k: v for k, v in s.items() if k != "Oncelik"} for s in kaynak_liste]

if temiz_tablo:
    st.dataframe(pd.DataFrame(temiz_tablo), use_container_width=True, hide_index=True)
else:
    st.warning("Seçili kriterlere göre şu an 🟢 UYGUN varlık bulunmuyor.")

if veri_yok_kodlar:
    st.caption(f"Veri kaynağında kaydı bulunamayan semboller: {', '.join(veri_yok_kodlar)}")

st.divider()

# Sanal işlem defteri
st.subheader("2. Sanal Otomatik İşlem Geçmişi")
if st.session_state.kapanan_islemler:
    st.dataframe(pd.DataFrame(st.session_state.kapanan_islemler), use_container_width=True, hide_index=True)
else:
    st.caption("Henüz hedef veya stop seviyesine ulaşıp kapanan sanal işlem bulunmuyor. Açık işlemler yukarıdaki sayaçta anlık takip ediliyor.")

st.divider()
st.caption(
    "Uyarı: Bu paneldeki otomatik al-sat ve kâr/zarar sayacı gerçek piyasa verileriyle çalışan bir simülasyon/takip aracıdır; "
    "kesin kâr garantisi sağlamaz ve gerçek işlemlerde zarar riski her zaman mevcuttur."
)
