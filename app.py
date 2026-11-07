import streamlit as st
import pandas as pd
import requests
import time
import re
import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")
st.title("♿ Erişilebilirlik Denetim ve Otomasyon Paneli")

# ================= KALICI DEPOLAMA =================
SUPABASE_KEY = "sb_publishable_Au_J5CujUVFKyZzdx7zALw_5qLnIb3r"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()

DATA_DIR = Path("app_data")
DATA_DIR.mkdir(exist_ok=True)

def _get_sb():
    if not SUPABASE_URL:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

_sb = _get_sb()

KOLONLAR = {
    "musteri_df": ["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"],
    "lead_results": ["Sektör", "Şirket", "Domain", "Hata", "Tahmini Ücret (TL)",
                     "Hata Detayı (TR)", "E-posta", "Durum"],
    "gelen_yanitlar": ["Gönderen", "Konu", "Durum"],
    "gonderilenler_log": ["Tarih", "Domain", "E-posta", "Hata Sayısı",
                          "Talep Edilen Ücret", "Durum"],
}

def _kaydet(anahtar, df):
    # 1) Yerel JSON (her zaman çalışır – kalıcı)
    try:
        df.to_json(DATA_DIR / f"{anahtar}.json", orient="records",
                   force_ascii=False, indent=2)
    except Exception:
        pass
    # 2) Supabase (SUPABASE_URL verilmişse)
    if _sb:
        try:
            _sb.table("app_state").upsert(
                {"key": anahtar, "data": df.to_dict(orient="records")}
            ).execute()
        except Exception:
            pass

def _yukle(anahtar):
    kolonlar = KOLONLAR[anahtar]
    if _sb:
        try:
            res = _sb.table("app_state").select("data").eq("key", anahtar).execute()
            if res.data and res.data[0].get("data") is not None:
                return pd.DataFrame(res.data[0]["data"], columns=kolonlar)
        except Exception:
            pass
    path = DATA_DIR / f"{anahtar}.json"
    if path.exists():
        try:
            df = pd.read_json(path, orient="records")
            return df.reindex(columns=kolonlar)
        except Exception:
            pass
    return pd.DataFrame(columns=kolonlar)

def init_state():
    for k in KOLONLAR:
        if k not in st.session_state:
            st.session_state[k] = _yukle(k)

def persist(anahtar):
    _kaydet(anahtar, st.session_state[anahtar])

init_state()
df = st.session_state.musteri_df

# ================= GMAIL =================
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"

# ================= HATA ÇEVİRİ =================
hata_sozlugu = {
    "Image elements do not have [alt] attributes": "Görsellerde alternatif metin (alt etiketi) eksik. Çözüm: Her görsele içeriği tanımlayan bir 'alt' metni ekleyin.",
    "Heading elements are not in a sequentially-descending order": "Başlık etiketleri (H1, H2, H3) sıralı değil. Çözüm: Başlıkları hiyerarşik sırayla kullanın.",
    "Elements with role=\"none\" or role=\"presentation\" have conflicts": "Sunum rolü çakışması. Çözüm: Etkileşimli öğelerden role=\"presentation\" etiketini kaldırın.",
    "Touch targets do not have sufficient size or spacing": "Dokunmatik hedefler çok küçük. Çözüm: Buton boyutlarını en az 48x48 piksel yapın.",
    "Buttons do not have an accessible name": "Butonların erişilebilir bir adı yok. Çözüm: Buton içine metin ekleyin veya aria-label ile adlandırın.",
    "Background and foreground colors do not have a sufficient contrast ratio": "Renk kontrastı yetersiz. Çözüm: Metin ve arka plan arasındaki kontrastı artırın."
}

def hatayi_cevir(hata_ingilizce):
    for key, val in hata_sozlugu.items():
        if key.lower() in hata_ingilizce.lower():
            return val
    return f"{hata_ingilizce} (Çözüm için incelenmeli)"

# ================= SEKMELER =================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Genel Bakış",
    "👥 Müşteri Yönetimi",
    "🔍 Gerçek Site Tarayıcı",
    "🤖 Otomatik Müşteri Bulucu",
    "📧 E-posta Otomasyonu & Loglar"
])

# ================= 1. SEKME =================
with tab1:
    st.header("Sistem Özeti ve Başarı Skoru")
    toplam_gonderilen = len(st.session_state.gonderilenler_log)
    toplam_yanit = len(st.session_state.gelen_yanitlar)

    olumlu_yanit_sayisi = 0
    if not st.session_state.gelen_yanitlar.empty:
        olumlu_yanit_sayisi = len(
            st.session_state.gelen_yanitlar[
                st.session_state.gelen_yanitlar["Durum"] == "🔥 Olumlu (Satışa Hazır)"
            ]
        )

    basari_orani = (olumlu_yanit_sayisi / toplam_gonderilen * 100) if toplam_gonderilen > 0 else 0.0
    potansiyel_gelir = st.session_state.gonderilenler_log["Talep Edilen Ücret"].sum() if not st.session_state.gonderilenler_log.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gönderilen E-posta", toplam_gonderilen)
    col2.metric("Gelen Yanıt", toplam_yanit)
    col3.metric("Satış Başarı Oranı", f"% {basari_orani:.1f}")
    col4.metric("Potansiyel Ciro (Tümü)", f"{potansiyel_gelir:,.2f} TL")

    st.divider()
    st.subheader("Kazanılan Müşteriler (Aktif Gelir)")
    col_m1, col_m2 = st.columns(2)
    toplam_gelir = df["Aylık Ücret (TL)"].sum() if not df.empty else 0.0
    col_m1.metric("Aylık Garantili Gelir", f"{toplam_gelir:,.2f} TL")
    col_m2.metric("Aktif Müşteri Sayısı", len(df))

    if not df.empty:
        st.bar_chart(df.set_index("Müşteri Adı")["Aylık Ücret (TL)"], color="#00C853")

# ================= 2. SEKME =================
with tab2:
    st.header("Müşteri ve Denetim Kayıtları")
    with st.form("ekleme_formu", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        musteri_adi = col_f1.text_input("Müşteri Adı")
        web_sitesi = col_f2.text_input("Web Sitesi")
        col_f3, col_f4 = st.columns(2)
        hata_sayisi = col_f3.number_input("Hata Sayısı", min_value=0)
        ucret = col_f4.number_input("Aylık Ücret (TL)", min_value=0.0)
        if st.form_submit_button("Kaydet") and musteri_adi:
            yeni = pd.DataFrame({
                "Müşteri Adı": [musteri_adi],
                "Web Sitesi": [web_sitesi],
                "Hata Sayısı": [hata_sayisi],
                "Aylık Ücret (TL)": [ucret],
            })
            st.session_state.musteri_df = pd.concat(
                [st.session_state.musteri_df, yeni], ignore_index=True
            )
            persist("musteri_df")
            st.rerun()
    st.dataframe(df, use_container_width=True) # ================= 3. SEKME =================
with tab3:
    st.header("Gerçek Erişilebilirlik Tarayıcı")
    with st.form("tarama_formu"):
        hedef_url = st.text_input("Site Linki")
        if st.form_submit_button("Tara"):
            if not hedef_url.startswith("http"):
                hedef_url = "https://" + hedef_url
            with st.spinner("Taranıyor..."):
                try:
                    API_KEY = "AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                    url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={hedef_url}&category=accessibility&key={API_KEY}"
                    r = requests.get(url, timeout=60)
                    if r.status_code == 200:
                        data = r.json()
                        score = data['lighthouseResult']['categories']['accessibility']['score'] * 100
                        audits = data['lighthouseResult']['audits']
                        failures = [d['title'] for a, d in audits.items() if d.get('score') == 0]
                        st.metric("Erişilebilirlik Skoru", f"{score:.0f}/100")
                        st.metric("Kritik Hata", len(failures))

                        st.write("**Türkçe Hata Detayları ve Çözümleri:**")
                        for hata in failures[:5]:
                            st.info(hatayi_cevir(hata))
                except Exception:
                    st.error("Hata oluştu.")

# ================= 4. SEKME =================
with tab4:
    st.header("🤖 Tek Tıkla Otomatik Müşteri Bulucu")
    hedef_sektorler = ["butik", "klinik", "emlak", "mobilya", "otel", "restoran", "diş kliniği", "avukat"]

    with st.form("otomatik_avci"):
        sehir_input = st.selectbox("Hangi Şehirde Aransın?",
                                   ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"])
        baslat_butonu = st.form_submit_button("🚀 Tek Tıkla Taramayı Başlat")

        if baslat_butonu:
            arama_sehir = sehir_input

            kara_liste = [
                "yandex", "google", "facebook", "instagram", "sahibinden", "trendyol",
                "hepsiburada", "n11", "gittigidiyor", "amazon", "wikipedia", "doktorum360",
                "infobel", "eticaretlink", "com.com", "armut.com", "foursquare", "yelp",
                "bulurum", "rehber", "firmalar", "katalog", "harita", "eksisozluk", "tripadvisor",
                "doktorasistan", "tatilnokta", "menu-tr", "otelz", "etstur", "tatilbudur", "istanbul.net.tr",
                ".gov.tr", ".edu.tr", "ibb.istanbul", "x.com", "kent.edu.tr", "kto.edu.tr",
                "tim.org.tr", "saygi.tr", "iletisim.com.tr"
            ]

            leads = []
            seen_domains = set()
            progress_bar = st.progress(0)
            status_text = st.empty()
            limit = 3

            for idx, sek in enumerate(hedef_sektorler):
                status_text.text(f"🔍 '{sek}' sektörü taranıyor... ({idx+1}/{len(hedef_sektorler)})")

                query = f'"{sek}" "{arama_sehir}" iletişim site:.com.tr'
                params = {
                    "engine": "google", "q": query,
                    "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c",
                    "num": 20, "gl": "tr"
                }

                try:
                    res = GoogleSearch(params).get_dict().get("organic_results", [])
                    count = 0
                    for r in res:
                        if count >= limit:
                            break
                        url = r.get("link", "")
                        title = r.get("title", "").lower()

                        if any(x in url for x in kara_liste):
                            continue
                        if any(x in title for x in ["sarı sayfa", "rehber", "katalog", "firmalar", "listesi", "sayfaları", "belediyesi", "üniversitesi", "meclisi", "başkanlığı"]):
                            continue

                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                        if not domain_match:
                            continue
                        domain = domain_match.group(1)

                        if domain in seen_domains:
                            continue

                        hata = 0
                        hata_detaylari = "Erişilebilirlik eksiklikleri"
                        try:
                            api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{domain}&category=accessibility&key=AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                            rr = requests.get(api, timeout=20)
                            if rr.status_code == 200:
                                audits = rr.json()['lighthouseResult']['audits']
                                failures = [d['title'] for a, d in audits.items() if d.get('score') == 0]
                                hata = len(failures)
                                if failures:
                                    hata_detaylari = " ... ".join([hatayi_cevir(h) for h in failures[:2]])
                        except Exception:
                            pass

                        if hata < 2:
                            continue

                        mail = f"info@{domain}"
                        tahmini_ucret = 1500 + (hata * 200)

                        leads.append({
                            "Sektör": sek,
                            "Şirket": r.get("title", domain)[:30],
                            "Domain": domain,
                            "Hata": hata,
                            "Tahmini Ücret (TL)": tahmini_ucret,
                            "Hata Detayı (TR)": hata_detaylari,
                            "E-posta": mail,
                            "Durum": "🔥 Sıcak" if hata >= 8 else "Ilık"
                        })

                        seen_domains.add(domain)
                        count += 1
                except Exception:
                    pass
                progress_bar.progress((idx + 1) / len(hedef_sektorler))

            status_text.text("✅ Tarama tamamlandı!")
            time.sleep(1)

            if leads:
                st.session_state.lead_results = pd.DataFrame(leads).sort_values("Hata", ascending=False)
                persist("lead_results")
                st.success(f"Sistem **{len(leads)}** adet site buldu.")
            else:
                st.warning("Uygun site bulunamadı.")

    if not st.session_state.lead_results.empty:
        st.dataframe(st.session_state.lead_results, use_container_width=True)

# ================= 5. SEKME =================
with tab5:
    st.header("📧 E-posta Gönderimi ve Giden Kutusu Logları")
    st.info(f"Sistem **{GMAIL_ADRESI}** adresine bağlı.")

    col_gonder, col_oku = st.columns(2)

    with col_gonder:
        st.subheader("1. E-posta Gönder")
        if not st.session_state.lead_results.empty:
            if st.button("🚀 Listeye Toplu E-posta Gönder"):
                gonderilmis_domainler = set(st.session_state.gonderilenler_log["Domain"].tolist())
                gonderilecekler = st.session_state.lead_results[
                    ~st.session_state.lead_results["Domain"].isin(gonderilmis_domainler)
                ]

                if gonderilecekler.empty:
                    st.warning("Bu listedeki tüm sitelere zaten e-posta gönderilmiş. Mükerrer gönderim engellendi.")
                else:
                    basarili = 0
                    hatali = 0
                    progress = st.progress(0)

                    for i, row in gonderilecekler.iterrows():
                        alici = row['E-posta']
                        site = row['Domain']
                        hata_sayisi = row['Hata']
                        tahmini_ucret = row['Tahmini Ücret (TL)']
                        hata_detayi = row.get('Hata Detayı (TR)', 'çeşitli sorunlar')

                        msg = MIMEMultipart()
                        msg['From'] = GMAIL_ADRESI
                        msg['To'] = alici
                        msg['Subject'] = f"{site} sitenizdeki erişilebilirlik sorunu ve çözümü hakkında"

                        body = f"""Merhaba,

{site} web sitenizi engelli bireylerin kullanımı açısından inceledim. Google standartlarına göre sitenizde **{hata_sayisi}** kritik hata tespit ettim.

Tespit ettiğim en önemli sorun(lar):
**{hata_detayi}**

Bu hataların giderilmesi için size özel bir bakım paketimiz mevcut. Tek seferlik çözüm ve aylık takip bedeli **{tahmini_ucret} TL** olarak belirlenmiştir.

Ayrıca, 2025 Erişilebilirlik Genelgesi kapsamında işletmelere yönelik idari para cezaları gündemde.

İsterseniz sitenizdeki tüm hataların listesini ve çözüm önerilerini içeren **ücretsiz detaylı raporu** gönderebilirim.

Sadece bu e-postaya **"Evet"** yazmanız yeterli.

Saygılarımla,
Cuma Babacan"""

                        msg.attach(MIMEText(body, 'plain', 'utf-8'))

                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                            server.send_message(msg)
                            server.quit()
                            basarili += 1

                            yeni_log = pd.DataFrame({
                                "Tarih": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                                "Domain": [site],
                                "E-posta": [alici],
                                "Hata Sayısı": [hata_sayisi],
                                "Talep Edilen Ücret": [tahmini_ucret],
                                "Durum": ["Gönderildi (Yanıt Bekleniyor)"]
                            })
                            st.session_state.gonderilenler_log = pd.concat(
                                [st.session_state.gonderilenler_log, yeni_log],
                                ignore_index=True
                            )
                        except Exception:
                            hatali += 1

                        progress.progress((i + 1) / len(gonderilecekler))
                        time.sleep(2)

                    persist("gonderilenler_log")
                    st.success(f"İşlem tamam! {basarili} yeni e-posta gönderildi. {hatali} hata.")
        else:
            st.info("Gönderilecek liste boş. Önce 'Otomatik Müşteri Bulucu' sekmesinden arama yapın.")

    with col_oku:
        st.subheader("2. Gelen Yanıtları Kontrol Et")
        if st.button("📥 Gelen Kutusunu Tara ve Sınıflandır"):
            with st.spinner("Gmail'e bağlanılıyor ve yanıtlar okunuyor..."):
                try:
                    mail = imaplib.IMAP4_SSL("imap.gmail.com")
                    mail.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                    mail.select("inbox")

                    status, messages = mail.search(None, "ALL")
                    mail_ids = messages[0].split()[-20:]

                    yanitlar = []
                    olumlu_kelimeler = ["evet", "ilgileniyorum", "rapor", "detay", "fiyat", "görüşelim", "bilgi alabilir"]
                    olumsuz_kelimeler = ["istemiyorum", "ilgilenmiyorum", "çıkarın", "teşekkürler", "uygun değil"]

                    for i in reversed(mail_ids):
                        typ, data = mail.fetch(i, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                konu = msg['Subject'] or ""
                                gonderen = msg['From'] or ""

                                if "Re:" in konu or "Ynt:" in konu:
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore').lower()
                                                break
                                    else:
                                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore').lower()

                                    durum = "Belirsiz"
                                    if any(k in body for k in olumlu_kelimeler):
                                        durum = "🔥 Olumlu (Satışa Hazır)"
                                    elif any(k in body for k in olumsuz_kelimeler):
                                        durum = "❌ Olumsuz"

                                    yanitlar.append({
                                        "Gönderen": gonderen,
                                        "Konu": konu,
                                        "Durum": durum
                                    })
                    mail.logout()

                    if yanitlar:
                        st.session_state.gelen_yanitlar = pd.DataFrame(yanitlar)
                        persist("gelen_yanitlar")
                        st.success(f"{len(yanitlar)} adet yanıt bulundu ve sınıflandırıldı!")
                    else:
                        st.info("Henüz bir yanıt bulunamadı.")
                except Exception as e:
                    st.error(f"Bağlantı Hatası: {e}. Lütfen Gmail uygulama şifrenizi kontrol edin.")

        if not st.session_state.gelen_yanitlar.empty:
            st.write("### 📊 Gelen Yanıtlar")
            st.dataframe(st.session_state.gelen_yanitlar, use_container_width=True)

    st.divider()
    st.subheader("📤 Giden E-posta Logları (Kimlere Ne Gönderildi?)")
    if not st.session_state.gonderilenler_log.empty:
        st.dataframe(
            st.session_state.gonderilenler_log.sort_values(by="Tarih", ascending=False),
            use_container_width=True
        )
    else:
        st.info("Henüz hiç e-posta gönderilmedi.")
