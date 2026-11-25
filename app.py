from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="BIST Katılım Detaylı Analiz Paneli",
    page_icon="🟢",
    layout="wide",
)

KULLANICI_ADI = "Cuma Babacan"
SIFRE = "784512"

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

sol_baslik, sag_buton = st.columns([6, 1])
with sol_baslik:
    st.title("BIST Katılım Detaylı Analiz Paneli")
    st.caption("Açılışta tek işlem • Günlük kâr veya akşam stop • Gerçek fiyat, maliyet ve risk matematiği")
with sag_buton:
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

tr_simdi = datetime.now(ZoneInfo("Europe/Istanbul"))
su_an = tr_simdi.time()
seans_aktif = time(9, 50) <= su_an <= time(18, 20)

if seans_aktif:
    st_autorefresh(interval=60 * 1000, key="otomatik_1dk")
    st.success(f"Canlı Takip Aktif (09:50 - 18:20 • 1 Dakika) — Son Güncelleme: {tr_simdi.strftime('%H:%M:%S')}")
else:
    st.info(f"Otomatik 1 dakikalık yenileme 09:50 - 18:20 arasındadır. Şu anki saat: {tr_simdi.strftime('%H:%M:%S')}")

st.sidebar.header("Sistem Parametreleri")
komisyon_binde = st.sidebar.number_input("Toplam Komisyon (Alış+Satış Binde)", min_value=0.0, max_value=20.0, value=2.0, step=0.2)
makas_yuzde = st.sidebar.number_input("Tahmini Makas / Spread (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)
min_odul_risk = st.sidebar.number_input("Min. Ödül / Risk Oranı", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
max_enerji_yuzde = st.sidebar.slider("Maks. Sabah Enerji Tüketimi (%)", min_value=20, max_value=90, value=60, step=5)

toplam_maliyet_yuzde = (komisyon_binde / 10.0) + makas_yuzde
maliyet_esigi = toplam_maliyet_yuzde * 3.0


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
detay_sozlugu = {}

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
            "Özet Neden": "Veri kaynağında sembol bulunamadı.",
        })
        detay_sozlugu[kod] = {
            "veri_var": False,
            "ad": ad,
            "tur": tur,
        }
        continue

    gecmis = df.iloc[-6:-1] if len(df) >= 6 else df.iloc[:-1]
    aralik_serisi = (gecmis["High"] - gecmis["Low"]).astype(float)
    ogh = float(aralik_serisi.mean()) if len(aralik_serisi) > 0 else 0.0

    son_satir = df.iloc[-1]
    son_fiyat = float(son_satir["Close"])
    bugun_yuksek = float(son_satir["High"])
    bugun_dusuk = float(son_satir["Low"])
    bugun_aralik = max(0.0, bugun_yuksek - bugun_dusuk)

    onceki_fiyat = float(df.iloc[-2]["Close"]) if len(df) >= 2 else son_fiyat
    gunluk_degisim_yuzde = ((son_fiyat - onceki_fiyat) / onceki_fiyat * 100.0) if onceki_fiyat > 0 else 0.0

    enerji_oran = (bugun_aralik / ogh * 100.0) if ogh > 0 else 999.0

    risk_tutar = max(ogh * 0.30, son_fiyat * 0.008)
    hedef_tutar = risk_tutar * min_odul_risk

    stop_fiyat = max(0.01, son_fiyat - risk_tutar)
    hedef_fiyat = son_fiyat + hedef_tutar

    risk_yuzde = (risk_tutar / son_fiyat * 100.0) if son_fiyat > 0 else 0.0
    hedef_yuzde = (hedef_tutar / son_fiyat * 100.0) if son_fiyat > 0 else 0.0
    gercek_oran = (hedef_tutar / risk_tutar) if risk_tutar > 0 else 0.0

    enerji_ok = enerji_oran <= max_enerji_yuzde
    maliyet_ok = hedef_yuzde >= maliyet_esigi
    oran_ok = gercek_oran >= min_odul_risk

    if enerji_ok and maliyet_ok and oran_ok:
        durum = "🟢 UYGUN"
        ozet = "Tüm rakamsal kurallar sağlandı."
    else:
        durum = "🔴 BEKLE"
        eksikler = []
        if not enerji_ok:
            eksikler.append("Enerji yüksek")
        if not maliyet_ok:
            eksikler.append("Hedef/maliyet marjı dar")
        if not oran_ok:
            eksikler.append("Ödül/risk düşük")
        ozet = ", ".join(eksikler)

    tablo_satirlari.append({
        "Durum": durum,
        "Kod": kod,
        "Varlık": f"{ad} ({tur})",
        "Son Fiyat": round(son_fiyat, 2),
        "OGH": round(ogh, 2),
        "Enerji": f"%{enerji_oran:.0f}" if enerji_oran < 900 else "-",
        "Hedef": round(hedef_fiyat, 2),
        "Akşam Stop": round(stop_fiyat, 2),
        "Özet Neden": ozet,
    })

    detay_sozlugu[kod] = {
        "veri_var": True,
        "ad": ad,
        "tur": tur,
        "durum": durum,
        "son_fiyat": son_fiyat,
        "onceki_fiyat": onceki_fiyat,
        "gunluk_degisim_yuzde": gunluk_degisim_yuzde,
        "bugun_yuksek": bugun_yuksek,
        "bugun_dusuk": bugun_dusuk,
        "bugun_aralik": bugun_aralik,
        "ogh": ogh,
        "enerji_oran": enerji_oran,
        "enerji_ok": enerji_ok,
        "risk_tutar": risk_tutar,
        "risk_yuzde": risk_yuzde,
        "hedef_tutar": hedef_tutar,
        "hedef_yuzde": hedef_yuzde,
        "stop_fiyat": stop_fiyat,
        "hedef_fiyat": hedef_fiyat,
        "gercek_oran": gercek_oran,
        "maliyet_ok": maliyet_ok,
        "oran_ok": oran_ok,
    }

st.subheader("1. Genel Tarama Tablosu")
st.dataframe(pd.DataFrame(tablo_satirlari), use_container_width=True, hide_index=True)

st.divider()
st.subheader("2. Seçili Varlık İçin Detaylı Analiz ve Karar Gerekçesi")

secili_kod = st.selectbox(
    "İncelemek istediğin varlığı seç:",
    options=[v["kod"] for v in VARLIK_LISTESI],
    format_func=lambda k: f"{k} — {detay_sozlugu[k]['ad']}",
)

d = detay_sozlugu[secili_kod]

if not d["veri_var"]:
    st.warning(f"**{secili_kod}** için veri kaynağından fiyat serisi alınamadı. Farklı bir BIST kodu veya katılım hissesi ile deneyebilirsin.")
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Son Fiyat", f"{d['son_fiyat']:.2f} TL", f"{d['gunluk_degisim_yuzde']:+.2f}%")
    m2.metric("5 Günlük Ort. Hareket (OGH)", f"{d['ogh']:.2f} TL", f"Bugün Aralık: {d['bugun_aralik']:.2f} TL")
    m3.metric("Kâr Hedefi", f"{d['hedef_fiyat']:.2f} TL", f"+{d['hedef_tutar']:.2f} TL (+%{d['hedef_yuzde']:.2f})")
    m4.metric("Akşam Stop", f"{d['stop_fiyat']:.2f} TL", f"-{d['risk_tutar']:.2f} TL (-%{d['risk_yuzde']:.2f})")

    st.markdown("#### Kural Bazlı Karar Analizi")
    st.markdown(
        f"""
        * **Genel Karar:** **{d['durum']}**
        * **1) Sabah Enerji Tüketimi:** Bugünkü hareket genişliği (**{d['bugun_aralik']:.2f} TL**), son 5 günün ortalama hareketinin (**{d['ogh']:.2f} TL**) **%{d['enerji_oran']:.0f}**'ine denk geliyor. Sınır **%{max_enerji_yuzde}** $\rightarrow$ **{'Geçti (Hareket alanı var)' if d['enerji_ok'] else 'Kalmadı (Enerji fazla tüketilmiş)'}**.
        * **2) Maliyet ve Hedef Marjı:** Hedeflenen kazanç oranı **%{d['hedef_yuzde']:.2f}**. Tahmini toplam maliyetin (%{toplam_maliyet_yuzde:.2f}) 3 katı eşiği **%{maliyet_esigi:.2f}** $\rightarrow$ **{'Geçti (Maliyet marjı yeterli)' if d['maliyet_ok'] else 'Kalmadı (Hedef, maliyete göre dar)'}**.
        * **3) Ödül / Risk Dengesi:** Her **1,00 TL** riske karşılık **{d['gercek_oran']:.2f} TL** potansiyel hedef bulunuyor (Hedef en az **{min_odul_risk:.1f}x** olmalı) $\rightarrow$ **{'Geçti' if d['oran_ok'] else 'Kalmadı'}**.
        * **Gün İçi Fiyat Aralığı:** En Düşük **{d['bugun_dusuk']:.2f} TL** — En Yüksek **{d['bugun_yuksek']:.2f} TL** (Önceki Kapanış: **{d['onceki_fiyat']:.2f} TL**).
        """
    )

st.divider()
with st.expander("3. Bu Panelde Neye Göre İşlem Kararı Verilir? (Kural Rehberi)"):
    st.markdown(
        """
        * **Tek İşlem Kuralı:** Gün içinde şartlar sağlansa bile **yalnızca 1 işlem** açılır; kâr hedefi veya akşam stop sonrasında aynı gün ikinci işlem açılmaz.
        * **Yeşil Işık (🟢 UYGUN) Ne Anlama Gelir?** Sadece o anki fiyat, geçmiş 5 günlük hareket kapasitesi, maliyet eşiği ve risk/ödül oranının senin kurallarına uyduğunu gösterir; **kesin kâr garantisi değildir**.
        * **Zarar Riski:** Piyasadaki ani haberler veya fiyat boşlukları nedeniyle zararlı günler ve stop seviyelerinin altında kapanışlar her zaman mümkündür.
        """
    )
    
