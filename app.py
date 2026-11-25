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

# Dahili katılım varlık listesi (veri/katilim_listesi.py varsa otomatik üzerine ekler)
VARSAYILAN_VARLIKLAR = [
    {"kod": "GLDTR.IS", "ad": "QNB Altın Katılım BYF", "tur": "Katılım BYF"},
    {"kod": "GMSTR.IS", "ad": "QNB Gümüş Katılım BYF", "tur": "Katılım BYF"},
    {"kod": "THYAO.IS", "ad": "Türk Hava Yolları", "tur": "Pay Senedi"},
    {"kod": "BIMAS.IS", "ad": "BİM Mağazalar", "tur": "Pay Senedi"},
    {"kod": "TUPRS.IS", "ad": "Tüpraş", "tur": "Pay Senedi"},
]

try:
    from veri.katilim_listesi import KATILIM_VARLIKLARI as HARICI_LISTE

    if isinstance(HARICI_LISTE, list) and len(HARICI_LISTE) > 0:
        VARLIK_LISTESI = HARICI_LISTE
    else:
        VARLIK_LISTESI = VARSAYILAN_VARLIKLAR
except Exception:
    VARLIK_LISTESI = VARSAYILAN_VARLIKLAR

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.title("Panel Girişi")
    st.caption("Devam etmek için kullanıcı adı ve şifrenizi girin.")
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

# Başlık ve çıkış butonu
sol_baslik, sag_buton = st.columns([6, 1])
with sol_baslik:
    st.title("BIST Katılım Günlük Analiz Paneli")
    st.caption("Açılışta tek işlem • Günlük kâr veya akşam stop • Gerçek fiyat ve maliyet matematiği")
with sag_buton:
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

# Türkiye saati ve 09:50 - 18:20 otomatik yenileme (her 1 dakikada bir)
tr_simdi = datetime.now(ZoneInfo("Europe/Istanbul"))
su_an = tr_simdi.time()
seans_aktif = time(9, 50) <= su_an <= time(18, 20)

if seans_aktif:
    st_autorefresh(interval=60 * 1000, key="otomatik_1dk")
    st.success(f"Canlı Takip Aktif (09:50 - 18:20 • 1 Dakika) — Saat: {tr_simdi.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik yenileme 09:50 - 18:20 arasındadır. Şu anki saat: {tr_simdi.strftime('%H:%M:%S')}")

# Yan menü ayarları
st.sidebar.header("Sistem Parametreleri")
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)
min_odul_risk = st.sidebar.number_input("Min. Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_yuzde = st.sidebar.slider("Maks. Sabah Enerji Tüketimi (%)", min_value=20, max_value=90, value=60, step=5)

toplam_maliyet_yuzde = (komisyon_binde / 10.0) + makas_yuzde


@st.cache_data(ttl=55)
def fiyat_verisi_getir(sembol: str):
    try:
        df = yf.download(sembol, period="10d", interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        gerekli = {"High", "Low", "Close"}
        if not gerekli.issubset(set(df.columns)):
            return None
        df = df.dropna(subset=["High", "Low", "Close"])
        if len(df) < 2:
            return None
        return df
    except Exception:
        return None


tablo_satirlari = []

for item in VARLIK_LISTESI:
    kod = str(item.get("kod", "")).strip()
    ad = str(item.get("ad", kod)).strip()
    tur = str(item.get("tur", "Varlık")).strip()

    df = fiyat_verisi_getir(kod)
    if df is None:
        tablo_satirlari.append({
            "Durum": "⚪ VERİ YOK",
            "Kod": kod,
            "Varlık": f"{ad} ({tur})",
            "Son Fiyat": "-",
            "OGH": "-",
            "Enerji": "-",
            "Hedef": "-",
            "Akşam Stop": "-",
            "Açıklama": "Veri kaynağı yanıt vermedi veya sembol bulunamadı.",
        })
        continue

    gecmis = df.iloc[-6:-1] if len(df) >= 6 else df.iloc[:-1]
    aralik_serisi = (gecmis["High"] - gecmis["Low"]).astype(float)
    ogh = float(aralik_serisi.mean()) if len(aralik_serisi) > 0 else 0.0

    son_satir = df.iloc[-1]
    son_fiyat = float(son_satir["Close"])
    bugun_yuksek = float(son_satir["High"])
    bugun_dusuk = float(son_satir["Low"])
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

    if enerji_ok and maliyet_ok and oran_ok:
        durum = "🟢 UYGUN"
        aciklama = "Enerji, maliyet ve ödül/risk kuralları sağlandı."
    else:
        durum = "🔴 BEKLE"
        nedenler = []
        if not enerji_ok:
            nedenler.append("Enerji tüketimi yüksek")
        if not maliyet_ok:
            nedenler.append("Hedef/maliyet marjı dar")
        if not oran_ok:
            nedenler.append("Ödül/risk oranı düşük")
        aciklama = ", ".join(nedenler)

    tablo_satirlari.append({
        "Durum": durum,
        "Kod": kod,
        "Varlık": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH": round(ogh, 2),
        "Enerji": f"%{enerji_oran:.0f}" if enerji_oran < 900 else "-",
        "Hedef": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Açıklama": aciklama,
    })

sonuc_df = pd.DataFrame(tablo_satirlari)
st.dataframe(sonuc_df, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "Not: 🟢 UYGUN göstergesi yalnızca tanımlı rakamsal filtreleri geçen varlıkları listeler; "
    "kesin kâr garantisi sağlamaz ve zararlı işlemler her zaman mümkündür."
    )
                                                                          
