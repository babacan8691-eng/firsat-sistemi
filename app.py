from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

from veri.katilim_listesi import KATILIM_VARLIKLARI

st.set_page_config(
    page_title="BIST Katılım Takip & Analiz Paneli",
    page_icon="🟢",
    layout="wide",
)

KULLANICI_ADI = "Cuma Babacan"
SIFRE = "784512"

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if "ek_varliklar" not in st.session_state:
    st.session_state.ek_varliklar = []

if not st.session_state.giris_yapildi:
    st.title("Panel Girişi")
    st.caption("Kişisel analiz paneline erişmek için bilgilerinizi girin.")
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

ust_sol, ust_sag = st.columns([5, 1])
with ust_sol:
    st.title("Katılım Varlıkları Günlük Analiz Paneli")
    st.caption("Açılışta tek işlem • Günlük kâr veya akşam stop • Gerçek fiyat ve maliyet matematiği")
with ust_sag:
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

tr_saat = datetime.now(ZoneInfo("Europe/Istanbul"))
su_anki_zaman = tr_saat.time()
seans_aktif = time(9, 50) <= su_anki_zaman <= time(18, 20)

if seans_aktif:
    st_autorefresh(interval=60 * 1000, key="bist_1dk_yenileme")
    st.success(f"Otomatik Güncelleme Aktif (09:50 - 18:20 • Her 1 Dakika) — Son Kontrol: {tr_saat.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik 1 dakikalık yenileme 09:50 - 18:20 saatleri arasında çalışır. Şu anki saat: {tr_saat.strftime('%H:%M:%S')}")

# Kenar çubuğu: Kod düzenlemeden sembol ekleme ve kural ayarları
st.sidebar.header("Hızlı Sembol Ekle (Kod Yazmadan)")
with st.sidebar.form("sembol_ekle_formu", clear_on_submit=True):
    yeni_kod = st.text_input("BIST Kodu (Örn: SASA veya GLDTR.F)")
    yeni_ad = st.text_input("Açıklama (İsteğe bağlı)")
    ekle_btn = st.form_submit_button("Listeye Ekle")
    if ekle_btn and yeni_kod.strip():
        temiz = yeni_kod.strip().upper()
        if not temiz.endswith(".IS") and not temiz.endswith(".F"):
            temiz = f"{temiz}.IS"
        if all(x["kod"] != temiz for x in st.session_state.ek_varliklar):
            st.session_state.ek_varliklar.append({
                "kod": temiz,
                "ad": yeni_ad.strip() or temiz,
                "tur": "Eklenen Varlık",
            })
        st.rerun()

st.sidebar.header("Rakamsal Sistem Ayarları")
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
tahmini_makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.20, step=0.05)
min_odul_risk = st.sidebar.number_input("Minimum Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_oran = st.sidebar.slider("Maks. Enerji Tüketimi (%)", min_value=20, max_value=95, value=65, step=5)
sadece_veri_olani_goster = st.sidebar.checkbox("Veri gelmeyenleri gizle", value=True)

toplam_maliyet_yuzde = (komisyon_binde / 10.0) + tahmini_makas_yuzde


@st.cache_data(ttl=55)
def veri_cek_akilli(sembol: str):
    aday_semboller = [sembol]
    if sembol.endswith(".IS"):
        kok = sembol[:-3]
        aday_semboller.append(f"{kok}.F")
    elif sembol.endswith(".F"):
        kok = sembol[:-2]
        aday_semboller.append(f"{kok}.IS")

    for aday in aday_semboller:
        try:
            df = yf.download(aday, period="10d", interval="1d", progress=False, auto_adjust=False)
            if df is None or df.empty or len(df) < 3:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["High", "Low", "Close"])
            if len(df) >= 3:
                return df, aday
        except Exception:
            continue
    return None, sembol


tum_varliklar = list(KATILIM_VARLIKLARI) + list(st.session_state.ek_varliklar)
satirlar = []

for varlik in tum_varliklar:
    kod = varlik["kod"]
    ad = varlik["ad"]
    tur = varlik["tur"]

    df, aktif_sembol = veri_cek_akilli(kod)
    if df is None or len(df) < 2:
        if not sadece_veri_olani_goster:
            satirlar.append({
                "Durum": "⚪ VERİ YOK",
                "Kod": kod,
                "Ad / Tür": f"{ad} ({tur})",
                "Son Fiyat": "-",
                "OGH": "-",
                "Enerji": "-",
                "Hedef": "-",
                "Akşam Stop": "-",
                "Not": "Veri sağlayıcıda bu kod için günlük veri bulunamadı.",
            })
        continue

    gecmis = df.iloc[-6:-1] if len(df) >= 6 else df.iloc[:-1]
    araliklar = (gecmis["High"] - gecmis["Low"]).astype(float)
    ogh = float(araliklar.mean()) if len(araliklar) > 0 else 0.0

    son_gun = df.iloc[-1]
    son_fiyat = float(son_gun["Close"])
    bugun_yuksek = float(son_gun["High"])
    bugun_dusuk = float(son_gun["Low"])
    bugun_aralik = max(0.0, bugun_yuksek - bugun_dusuk)

    enerji_yuzde = (bugun_aralik / ogh * 100.0) if ogh > 0 else 999.0

    risk_tutar = max(ogh * 0.30, son_fiyat * 0.008)
    hedef_tutar = risk_tutar * min_odul_risk

    stop_fiyat = max(0.01, son_fiyat - risk_tutar)
    hedef_fiyat = son_fiyat + hedef_tutar

    hedef_yuzde = (hedef_tutar / son_fiyat * 100.0) if son_fiyat > 0 else 0.0
    maliyet_esigi = toplam_maliyet_yuzde * 2.5

    enerji_uygun = enerji_yuzde <= max_enerji_oran
    maliyet_uygun = hedef_yuzde >= maliyet_esigi
    odul_risk_uygun = (hedef_tutar / risk_tutar) >= min_odul_risk if risk_tutar > 0 else False

    if enerji_uygun and maliyet_uygun and odul_risk_uygun:
        durum = "🟢 UYGUN"
        not_metni = "Kriterler uygun."
    else:
        durum = "🔴 BEKLE"
        eksikler = []
        if not enerji_uygun:
            eksikler.append("Enerji sınırda/yüksek")
        if not maliyet_uygun:
            eksikler.append("Hedef/maliyet dar")
        if not odul_risk_uygun:
            eksikler.append("Ödül/risk düşük")
        not_metni = ", ".join(eksikler)

    satirlar.append({
        "Durum": durum,
        "Kod": aktif_sembol,
        "Ad / Tür": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH": round(ogh, 2),
        "Enerji": f"%{enerji_yuzde:.0f}" if enerji_yuzde < 900 else "-",
        "Hedef": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Not": not_metni,
    })

if len(satirlar) > 0:
    tablo = pd.DataFrame(satirlar)
    st.dataframe(tablo, use_container_width=True, hide_index=True)
else:
    st.warning("Seçili filtrelere göre şu an gösterilecek veri satırı bulunamadı.")

st.divider()
st.markdown(
    """
    **Kural ve Sınır Hatırlatması:**
    * **🟢 UYGUN** işareti yalnızca belirlediğin rakamsal oranları (enerji tüketimi, maliyet marjı ve ödül/risk oranı) geçen adayları gösterir; **kesin kâr garantisi değildir** ve zararlı günler her zaman mümkündür.
    * Emir vermeden önce kendi hesabındaki anlık fiyatı ve katılım uygunluğunu teyit et; gün içinde kural dışı ikinci işlem açma.
    """
)
