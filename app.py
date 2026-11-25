from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Katılım Takip & Analiz Paneli",
    page_icon="🟢",
    layout="wide",
)

# İslami / katılım hassasiyetine uygun aday liste (BIST sembolleri .IS uzantısıyla)
KATILIM_VARLIKLARI = [
    {"kod": "GLDTR.IS", "ad": "QNB Altın Katılım BYF", "tur": "Katılım BYF"},
    {"kod": "GMSTR.IS", "ad": "QNB Gümüş Katılım BYF", "tur": "Katılım BYF"},
    {"kod": "THYAO.IS", "ad": "Türk Hava Yolları (Katılım Örnek)", "tur": "Pay Senedi"},
    {"kod": "BIMAS.IS", "ad": "BİM Mağazalar (Katılım Örnek)", "tur": "Pay Senedi"},
    {"kod": "TUPRS.IS", "ad": "Tüpraş (Katılım Örnek)", "tur": "Pay Senedi"},
]

# Kullanıcı adı ve şifre kontrolü
KULLANICI_ADI = "Cuma Babacan"
SIFRE = "784512"

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

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

# Üst bilgi ve çıkış butonu
ust_sol, ust_sag = st.columns([5, 1])
with ust_sol:
    st.title("Katılım Varlıkları Günlük Analiz Paneli")
    st.caption("Kurallar: Açılışta tek işlem • Günlük kâr veya akşam stop • Gerçek fiyat ve maliyet matematiği")
with ust_sag:
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

# Türkiye saati ve 09:50 - 18:20 otomatik yenileme kontrolü
tr_saat = datetime.now(ZoneInfo("Europe/Istanbul"))
su_anki_zaman = tr_saat.time()
baslangic = time(9, 50)
bitis = time(18, 20)
seans_aktif = baslangic <= su_anki_zaman <= bitis

if seans_aktif:
    st_autorefresh(interval=60 * 1000, key="bist_1dk_yenileme")
    st.success(f"Otomatik Güncelleme Aktif (09:50 - 18:20 • Her 1 Dakika) — Son Kontrol: {tr_saat.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik 1 dakikalık yenileme 09:50 - 18:20 saatleri arasında çalışır. Şu anki saat: {tr_saat.strftime('%H:%M:%S')}")

# Parametre çubuğu
st.sidebar.header("Rakamsal Sistem Ayarları")
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Alış+Satış Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
tahmini_makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)
min_odul_risk = st.sidebar.number_input("Minimum Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_oran = st.sidebar.slider("Maks. Sabah Enerji Tüketimi (%)", min_value=20, max_value=90, value=60, step=5)

toplam_maliyet_yuzde = (komisyon_binde / 10.0) + tahmini_makas_yuzde


@st.cache_data(ttl=55)
def veri_cek(sembol: str):
    try:
        df = yf.download(sembol, period="10d", interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty or len(df) < 3:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["High", "Low", "Close"])
        if len(df) < 3:
            return None
        return df
    except Exception:
        return None


satirlar = []

for varlik in KATILIM_VARLIKLARI:
    kod = varlik["kod"]
    ad = varlik["ad"]
    tur = varlik["tur"]

    df = veri_cek(kod)
    if df is None or len(df) < 2:
        satirlar.append({
            "Durum": "⚪ VERİ YOK",
            "Kod": kod,
            "Ad / Tür": f"{ad} ({tur})",
            "Son Fiyat": "-",
            "OGH (Ort. Hareket)": "-",
            "Enerji Tüketimi": "-",
            "Hedef Fiyat": "-",
            "Akşam Stop": "-",
            "Not": "Veri çekilemedi veya sembol farklı.",
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
    maliyet_esigi = toplam_maliyet_yuzde * 3.0

    enerji_uygun = enerji_yuzde <= max_enerji_oran
    maliyet_uygun = hedef_yuzde >= maliyet_esigi
    odul_risk_uygun = (hedef_tutar / risk_tutar) >= min_odul_risk if risk_tutar > 0 else False

    if enerji_uygun and maliyet_uygun and odul_risk_uygun:
        durum = "🟢 UYGUN"
        not_metni = "Tüm rakamsal filtreler sağlandı."
    else:
        durum = "🔴 BEKLE"
        eksikler = []
        if not enerji_uygun:
            eksikler.append("Enerji yüksek")
        if not maliyet_uygun:
            eksikler.append("Hedef/maliyet marjı dar")
        if not odul_risk_uygun:
            eksikler.append("Ödül/risk düşük")
        not_metni = ", ".join(eksikler)

    satirlar.append({
        "Durum": durum,
        "Kod": kod,
        "Ad / Tür": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH (Ort. Hareket)": round(ogh, 2),
        "Enerji Tüketimi": f"%{enerji_yuzde:.0f}" if enerji_yuzde < 900 else "-",
        "Hedef Fiyat": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Not": not_metni,
    })

tablo = pd.DataFrame(satirlar)
st.dataframe(tablo, use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    """
    **Hatırlatma ve Sınırlar:**
    * **🟢 UYGUN** ışığı yalnızca belirlediğin rakamsal oranları (enerji tüketimi, maliyet marjı ve ödül/risk oranı) geçen varlıkları gösterir; **kesin kâr garantisi vermez** ve zararlı günler her zaman mümkündür.
    * Ücretsiz piyasa verilerinde fiyatlar gecikmeli gelebilir; gerçek emir vermeden önce kendi hesabındaki anlık fiyatı ve katılım uygunluğunu teyit etmelisin.
    """
        )
