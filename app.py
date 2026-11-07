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

# ================= GİRİŞ EKRANI =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Sisteme Giriş")
    st.info("Lütfen devam etmek için kullanıcı bilgilerinizi girin.")
    with st.form("login_form"):
        kullanici_adi = st.text_input("Kullanıcı Adı").strip()
        sifre = st.text_input("Şifre", type="password").strip()
        submit = st.form_submit_button("Giriş Yap")
        if submit:
            if kullanici_adi == "Cuma Babacan" and sifre == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

st.title("♿ Erişilebilirlik Denetim ve Otomasyon Paneli")

if st.sidebar.button("Çıkış Yap"):
    st.session_state.logged_in = False
    st.rerun()

# ================= KALICI DEPOLAMA =================
SUPABASE_KEY = "sb_publishable_Au_J5CujUVFKyZzdx7zALw_5qLnIb3r"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
DATA_DIR = Path("app_data")
DATA_DIR.mkdir(exist_ok=True)

def _get_sb():
    if not SUPABASE_URL: return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception: return None

_sb = _get_sb()

KOLONLAR = {
    "musteri_df": ["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"],
    "lead_results": ["Sektör", "Şirket", "Domain", "Hata", "Tahmini Ücret (TL)", "Hata Detayı (TR)", "E-posta", "Durum"],
    "gelen_yanitlar": ["Gönderen", "Konu", "Durum"],
    "gonderilenler_log": ["Tarih", "Domain", "E-posta", "Hata Sayısı", "Talep Edilen Ücret", "Durum"],
}

def _kaydet(anahtar, df):
    try:
        df.to_json(DATA_DIR / f"{anahtar}.json", orient="records", force_ascii=False, indent=2)
    except Exception: pass
    if _sb:
        try: _sb.table("app_state").upsert({"key": anahtar, "data": df.to_dict(orient="records")}).execute()
        except Exception: pass

def _yukle(anahtar):
    kolonlar = KOLONLAR[anahtar]
    if _sb:
        try:
            res = _sb.table("app_state").select("data").eq("key", anahtar).execute()
            if res.data and res.data[0].get("data") is not None:
                return pd.DataFrame(res.data[0]["data"], columns=kolonlar)
        except Exception: pass
    path = DATA_DIR / f"{anahtar}.json"
    if path.exists():
        try: return pd.read_json(path, orient="records").reindex(columns=kolonlar)
        except Exception: pass
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

# ================= GENİŞLETİLMİŞ HATA ÇEVİRİ =================
hata_sozlugu = {
    "Image elements do not have [alt] attributes": "Görsellerde alternatif metin (alt etiketi) eksik. Çözüm: Her görsele 'alt' metni ekleyin.",
    "Heading elements are not in a sequentially-descending order": "Başlık etiketleri (H1, H2, H3) sıralı değil. Çözüm: Hiyerarşik sırayla kullanın.",
    "Elements with role=\"none\" or role=\"presentation\" have conflicts": "Sunum rolü çakışması. Çözüm: role=\"presentation\" etiketini kaldırın.",
    "Touch targets do not have sufficient size or spacing": "Dokunmatik hedefler çok küçük. Çözüm: Butonları en az 48x48 piksel yapın.",
    "Buttons do not have an accessible name": "Butonların adı yok. Çözüm: Butona metin veya aria-label ekleyin.",
    "Background and foreground colors do not have a sufficient contrast ratio": "Renk kontrastı yetersiz. Çözüm: Metin/arka plan kontrastını artırın.",
    "elements do not have a title": "Iframe başlığı eksik. Çözüm: Gömülü içeriklere 'title' ekleyin.",
    "ARIA input fields do not have accessible names": "Form alanlarının adı yok. Çözüm: Giriş alanlarına 'label' ekleyin.",
    "Links do not have a discernible name": "Linklerin anlaşılır adı yok. Çözüm: İkon linklere 'aria-label' ekleyin.",
    "[aria-*] attributes do not have valid values": "Geçersiz ARIA değerleri. Çözüm: Değerleri standartlara uygun yapın.",
    "Document does not have a main landmark": "Ana içerik (main) etiketi eksik. Çözüm: İçeriği <main> içine alın.",
    "List items": "Liste öğeleri yanlış yerde. Çözüm: <li> etiketlerini <ul> içine alın.",
    "role=\"dialog\" or role=\"alertdialog\" do not have accessible names": "Açılır pencerelerin adı yok. Çözüm: 'aria-label' ekleyin.",
    "<html> element does not have a [lang] attribute": "HTML dil özelliği (lang) eksik. Çözüm: <html lang='tr'> ekleyin.",
    "[user-scalable=\"no\"]": "Mobilde büyütme engellenmiş. Çözüm: user-scalable=yes yapın.",
    "Lists do not contain only <li>": "Liste yapısı hatalı. Çözüm: <ul> içinde sadece <li> kullanın."
}

def hatayi_cevir(hata_ingilizce):
    for key, val in hata_sozlugu.items():
        if key.lower() in hata_ingilizce.lower(): return val
    return f"{hata_ingilizce}"

# ================= SEKMELER =================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Genel Bakış", "👥 Müşteri Yönetimi", "🔍 Gerçek Site Tarayıcı", 
    "🤖 Otomatik Müşteri Bulucu", "📧 E-posta Otomasyonu & Loglar", "🌟 Vitrin & Hakkımda"
])

# ================= 1. SEKME =================
with tab1:
    st.header("Sistem Özeti ve Başarı Skoru")
    toplam_gonderilen = len(st.session_state.gonderilenler_log)
    toplam_yanit = len(st.session_state.gelen_yanitlar)
    olumlu_yanit_sayisi = 0
    if not st.session_state.gelen_yanitlar.empty:
        olumlu_yanit_sayisi = len(st.session_state.gelen_yanitlar[st.session_state.gelen_yanitlar["Durum"] == "🔥 Olumlu (Satışa Hazır)"])
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
            yeni = pd.DataFrame({"Müşteri Adı": [musteri_adi], "Web Sitesi": [web_sitesi], "Hata Sayısı": [hata_sayisi], "Aylık Ücret (TL)": [ucret]})
            st.session_state.musteri_df = pd.concat([st.session_state.musteri_df, yeni], ignore_index=True)
            persist("musteri_df")
            st.rerun()
    st.dataframe(df, use_container_width=True) # ================= YARDIMCI FONKSİYON: E-POSTA KAZIMA =================
def eposta_bul(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=10)
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = re.findall(email_pattern, r.text)
        fake_emails = ["ornek@", "example@", "test@", "email@", "adsoyad@", "mail@example", "info@example"]
        
        for em in emails:
            em_lower = em.lower()
            if not em_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico')):
                if not any(fake in em_lower for fake in fake_emails):
                    return em
        for path in ['/iletisim', '/contact', '/iletisim/']:
            contact_url = url.rstrip('/') + path
            try:
                r2 = requests.get(contact_url, headers=headers, timeout=5)
                emails2 = re.findall(email_pattern, r2.text)
                for em in emails2:
                    em_lower = em.lower()
                    if not em_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico')):
                        if not any(fake in em_lower for fake in fake_emails):
                            return em
            except: continue
    except Exception: pass
    return None

# ================= 3. SEKME =================
with tab3:
    st.header("Gerçek Erişilebilirlik Tarayıcı")
    with st.form("tarama_formu"):
        hedef_url = st.text_input("Site Linki")
        if st.form_submit_button("Tara"):
            if not hedef_url.startswith("http"): hedef_url = "https://" + hedef_url
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
                        for hata in failures[:5]: st.info(hatayi_cevir(hata))
                except Exception: st.error("Hata oluştu.")

# ================= 4. SEKME =================
with tab4:
    st.header("🤖 Tek Tıkla Otomatik Müşteri Bulucu")
    
    col_temizle1, col_temizle2 = st.columns([1, 4])
    with col_temizle1:
        if st.button("🗑️ Listeyi Temizle"):
            st.session_state.lead_results = pd.DataFrame()
            persist("lead_results")
            st.rerun()
            
    arama_modu = st.radio("Nasıl Arama Yapmak İstersiniz?", ["Hedefli Arama (Sektör + Şehir)", "Genel Arama (Serbest Metin)"], horizontal=True)
    
    with st.form("otomatik_avci"):
        if arama_modu == "Hedefli Arama (Sektör + Şehir)":
            sehir_input = st.selectbox("Hangi Şehirde Aransın?", ["Tüm Türkiye", "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"])
            tum_sektorler = ["klinik", "otel", "emlak", "butik", "restoran", "diş kliniği", "avukat", "kuaför", "spor salonu", "veteriner", "e-ticaret", "güzellik merkezi", "estetik", "mobilya", "oto galeri", "düğün salonu"]
            secili_sektorler = st.multiselect("Hangi Sektörler Taranacak?", tum_sektorler, default=tum_sektorler)
            arama_kelimeleri = secili_sektorler
        else:
            st.info("Genel arama yaparken şehir veya sektör sınırı yoktur.")
            serbest_metin = st.text_input("Aramak istediğiniz kelime veya cümle")
            sehir_input = "" 
            arama_kelimeleri = [serbest_metin] if serbest_metin else []
            
        baslat_butonu = st.form_submit_button("🚀 Tek Tıkla Taramayı Başlat")

        if baslat_butonu:
            st.session_state.lead_results = pd.DataFrame()
            persist("lead_results")
            
            if not arama_kelimeleri:
                st.warning("Lütfen en az bir sektör veya arama kelimesi seçin.")
            else:
                # NİHAİ VE EN GENİŞ KARA LİSTE (Kurumlar, Rehberler, Bozuk Siteler)
                kara_liste = [
                    # Sosyal Medya ve Arama Motorları
                    "yandex", "google", "facebook", "instagram", "twitter", "x.com", "linkedin", "pinterest", "tiktok", "youtube",
                    # E-ticaret Devleri
                    "sahibinden", "trendyol", "hepsiburada", "n11", "gittigidiyor", "amazon", "aliexpress", "getir", "yemeksepeti", "çiçeksepeti",
                    # Dizin / Portal / Rehber Siteleri
                    "wikipedia", "doktorum360", "infobel", "eticaretlink", "com.com", "armut.com", "foursquare", "yelp",
                    "bulurum", "rehber", "firmalar", "katalog", "harita", "eksisozluk", "tripadvisor", "doktorasistan",
                    "tatilnokta", "menu-tr", "otelz", "etstur", "tatilbudur", "istanbul.net.tr", "firmasehri", "ankaraesnaf",
                    "chicco", "forum", "turk.net", "g.co", "adresci", "firmanyo", "iletisimadresleri", "demo.", "dijifa",
                    "bebee", "arvingo", "softbutik", "scheddy", "yazilim", "saas", "platform", "kolayrandevu",
                    "find.com", "find", "bulucu", "portal", "dizin", "arama", "search", "lookup", "listele", "firma", "rehberi",
                    # Resmi Kurumlar / Devlet / Eğitim
                    ".gov.tr", ".edu.tr", ".bel.tr", ".org.tr", "ibb.istanbul", "kent.edu.tr", "kto.edu.tr",
                    "tim.org.tr", "saygi.tr", "iletisim.com.tr", ".istanbul", "iett", "belediyesi", "valiligi", "bakanligi", "odasi",
                    # Uygulama Mağazaları ve Kısa Linkler
                    "apple.com", "play.google.com", "wa.me", "whatsapp", "appstore", "android", "ios",
                    # Büyük Markalar / Kurumsal
                    "audi", "volkswagen", "mercedes", "bmw", "toyota", "honda", "ford", "hyundai", "renault", "fiat",
                    "apple", "samsung", "sony", "lg", "huawei", "xiaomi", "oppo", "vestel", "arcelik", "beko", "turkcell", "vodafone", "turktelekom"
                ]

                leads = []
                seen_domains = set()
                progress_bar = st.progress(0)
                status_text = st.empty()
                limit = 5 

                for idx, kelime in enumerate(arama_kelimeleri):
                    status_text.text(f"🔍 '{kelime}' taranıyor... ({idx+1}/{len(arama_kelimeleri)})")
                    
                    if arama_modu == "Hedefli Arama (Sektör + Şehir)":
                        if sehir_input == "Tüm Türkiye":
                            query = f'{kelime} firma iletişim' 
                        else:
                            query = f'{kelime} {sehir_input} firma iletişim'
                    else:
                        query = f'{kelime} firma iletişim'

                    params = {"engine": "google", "q": query, "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c", "num": 30, "gl": "tr"}

                    try:
                        res = GoogleSearch(params).get_dict().get("organic_results", [])
                        count = 0
                        for r in res:
                            if count >= limit: break
                            url = r.get("link", "")
                            title = r.get("title", "").lower()
                            domain = ""

                            # URL ve Başlık Kara Liste Kontrolü
                            if any(x in url.lower() for x in kara_liste) or any(x in title for x in kara_liste): continue
                            
                            # Bozuk Site / Hata Sayfası Kontrolü (Çok Önemli)
                            hatali_basliklar = ["index of", "application error", "500 internal", "404 not found", "403 forbidden", "just a moment", "cloudflare", "erişim engellendi", "sayfa bulunamadı"]
                            if any(x in title for x in hatali_basliklar): continue
                            
                            # Gereksiz rehber kelimeleri
                            if any(x in title for x in ["sarı sayfa", "katalog", "firmalar", "listesi", "sayfaları", "meclisi", "başkanlığı", "derneği", "vakfı"]): continue

                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                            if not domain_match: continue
                            domain = domain_match.group(1).lower()
                            
                            # Domain Kara Liste Kontrolü (Ekstra Güvenlik)
                            if any(x in domain for x in ["apple", "wa.me", "whatsapp", "play.google", "appstore", "etso", "odasi", "sorgulama", "sportcard", "yazilim", "platform", "audi", "forum", "g.co", "iett", "istanbul", "find"]): continue
                            if domain in seen_domains: continue

                            hata = 0
                            hata_detaylari = "Erişilebilirlik eksiklikleri"
                            try:
                                api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{domain}&category=accessibility&key=AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                                rr = requests.get(api, timeout=20)
                                if rr.status_code == 200:
                                    audits = rr.json()['lighthouseResult']['audits']
                                    failures = [d['title'] for a, d in audits.items() if d.get('score') == 0]
                                    hata = len(failures)
                                    if failures: hata_detaylari = " ... ".join([hatayi_cevir(h) for h in failures[:2]])
                            except Exception: pass

                            if hata < 1: continue

                            status_text.text(f"📧 {domain} için e-posta aranıyor...")
                            gercek_mail = eposta_bul(f"https://{domain}")
                            mail = gercek_mail if gercek_mail else f"info@{domain}"
                            tahmini_ucret = 1500 + (hata * 200)

                            leads.append({
                                "Sektör": kelime, "Şirket": r.get("title", domain)[:30], "Domain": domain, "Hata": hata,
                                "Tahmini Ücret (TL)": tahmini_ucret, "Hata Detayı (TR)": hata_detaylari, "E-posta": mail,
                                "Durum": "🔥 Sıcak" if hata >= 8 else "Ilık"
                            })
                            seen_domains.add(domain)
                            count += 1
                    except Exception: pass
                    progress_bar.progress((idx + 1) / len(arama_kelimeleri))

                status_text.text("✅ Tarama tamamlandı!")
                time.sleep(1)
                if leads:
                    st.session_state.lead_results = pd.DataFrame(leads).sort_values("Hata", ascending=False)
                    persist("lead_results")
                    st.success(f"Sistem **{len(leads)}** adet site buldu.")
                else:
                    st.warning("Uygun site bulunamadı.")

    if not st.session_state.lead_results.empty:
        st.write("### 📋 Bulunan Müşteri Adayları (Kart Görünümü)")
        for idx, row in st.session_state.lead_results.iterrows():
            durum_ikon = "🔥" if row['Durum'] == "🔥 Sıcak" else "🟡"
            with st.expander(f"{durum_ikon} {row['Şirket']} - {row['Domain']} ({row['Hata']} Hata)"):
                st.write(f"**Sektör/Kelime:** {row['Sektör']}")
                st.write(f"**E-posta:** {row['E-posta']}")
                st.write(f"**Tahmini Ücret:** {row['Tahmini Ücret (TL)']} TL")
                st.write(f"**Hata Detayı:** {row['Hata Detayı (TR)']}") # ================= 5. SEKME =================
with tab5:
    st.header("📧 E-posta Gönderimi ve Giden Kutusu Logları")
    st.info(f"Sistem **{GMAIL_ADRESI}** adresine bağlı.")

    col_gonder, col_oku = st.columns(2)

    with col_gonder:
        st.subheader("1. E-posta Gönder")
        if not st.session_state.lead_results.empty:
            if st.button("🚀 Listeye Toplu E-posta Gönder"):
                gonderilmis_domainler = set(st.session_state.gonderilenler_log["Domain"].tolist())
                gonderilecekler = st.session_state.lead_results[~st.session_state.lead_results["Domain"].isin(gonderilmis_domainler)]

                if gonderilecekler.empty:
                    st.warning("Bu listedeki tüm sitelere zaten e-posta gönderilmiş. Mükerrer gönderim engellendi.")
                else:
                    basarili = 0
                    hatali = 0
                    progress = st.progress(0)
                    PANEL_LINKI = "https://yimf3leyv.streamlit.app"

                    for i, row in gonderilecekler.iterrows():
                        alici = row['E-posta']
                        site = row['Domain']
                        sirket_adi = row['Şirket']
                        hata_sayisi = row['Hata']
                        tahmini_ucret = row['Tahmini Ücret (TL)']
                        hata_detayi = row.get('Hata Detayı (TR)', 'çeşitli sorunlar')

                        msg = MIMEMultipart()
                        msg['From'] = GMAIL_ADRESI
                        msg['To'] = alici
                        msg['Subject'] = f"Dikkat: {site} sitenizde {hata_sayisi} kritik hata bulundu"

                        body = f"""Merhaba {sirket_adi} Yetkilisi,

Ben Cuma Babacan. Kendim de bir engelli bireyim ve engelli bireylerin web sitelerine sorunsuz erişebilmesi için bir erişilebilirlik denetim sistemi geliştirdim.

Bugün sizin sitenizi sistemimle test ettim ve **{site}** adresinde engelli bireylerin (ve Google botlarının) karşılaştığı **{hata_sayisi}** adet kritik engel tespit ettim.

Tespit ettiğim en önemli sorunlar şunlar:
👉 **{hata_detayi}**

**Bunu neden size yazıyorum?**
Sadece satış yapmak için değil; 2025 yılında yürürlüğe girecek Erişilebilirlik Genelgesi kapsamında, web sitesi engelli erişimine uygun olmayan işletmelere idari para cezaları uygulanacak. Ayrıca Google, erişilebilirliği tam olan siteleri arama sonuçlarında daha üst sıralarda gösteriyor.

Bu hataların giderilmesi için size özel bir bakım paketimiz mevcut. Çözüm ve aylık takip bedeli **{tahmini_ucret} TL** olarak belirlenmiştir. 

Ancak hemen bir ödeme yapmanıza gerek yok. İsterseniz sitenizin tamamının taranıp, hangi sayfada hangi hatanın olduğunu gösteren **ücretsiz detaylı denetim raporunu** size gönderebilirim.

Bu ücretsiz raporu talep etmek için sadece bu e-postaya **"Raporu Gönder"** yazmanız yeterli.

Benim kim olduğumu, hikayemi ve bu işi neden yaptığımı merak ediyorsanız, geliştirdiğim sistemi ve vitrinimi buradan inceleyebilirsiniz:
🌐 {PANEL_LINKI}

Sağlıklı ve kazançlı günler dilerim.

Saygılarımla,
Cuma Babacan
Erişilebilirlik Danışmanı"""

                        msg.attach(MIMEText(body, 'plain', 'utf-8'))

                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                            server.send_message(msg)
                            server.quit()
                            basarili += 1

                            yeni_log = pd.DataFrame({
                                "Tarih": [datetime.now().strftime("%Y-%m-%d %H:%M")], "Domain": [site],
                                "E-posta": [alici], "Hata Sayısı": [hata_sayisi],
                                "Talep Edilen Ücret": [tahmini_ucret], "Durum": ["Gönderildi (Yanıt Bekleniyor)"]
                            })
                            st.session_state.gonderilenler_log = pd.concat([st.session_state.gonderilenler_log, yeni_log], ignore_index=True)
                        except Exception: hatali += 1

                        progress.progress((i + 1) / len(gonderilecekler))
                        time.sleep(2)

                    persist("gonderilenler_log")
                    st.success(f"İşlem tamam! {basarili} yeni e-posta gönderildi. {hatali} hata.")
        else:
            st.info("Gönderilecek liste boş. Önce 'Otomatik Müşteri Bulucu' sekmesinden arama yapın.")

    with col_oku:
        st.subheader("2. Gelen Yanıtları Kontrol Et")
        if st.button("📥 Gelen Kutusunu Tara ve Sınıflandır"):
            with st.spinner("Gmail'e bağlanılıyor..."):
                try:
                    mail = imaplib.IMAP4_SSL("imap.gmail.com")
                    mail.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                    mail.select("inbox")
                    status, messages = mail.search(None, "ALL")
                    mail_ids = messages[0].split()[-20:]

                    yanitlar = []
                    olumlu_kelimeler = ["evet", "raporu gönder", "ilgileniyorum", "rapor", "detay", "fiyat", "görüşelim", "bilgi alabilir"]
                    olumsuz_kelimeler = ["istemiyorum", "ilgilenmiyorum", "çıkarın", "teşekkürler", "uygun değil", "spam"]

                    for i in reversed(mail_ids):
                        typ, data = mail.fetch(i, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                konu = msg['Subject'] or ""
                                gonderen = msg['From'] or ""

                                if "Re:" in konu or "Ynt:" in konu or "Dikkat:" in konu:
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore').lower()
                                                break
                                    else:
                                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore').lower()

                                    durum = "Belirsiz"
                                    if any(k in body for k in olumlu_kelimeler): durum = "🔥 Olumlu (Satışa Hazır)"
                                    elif any(k in body for k in olumsuz_kelimeler): durum = "❌ Olumsuz"

                                    yanitlar.append({"Gönderen": gonderen, "Konu": konu, "Durum": durum})
                    mail.logout()

                    if yanitlar:
                        st.session_state.gelen_yanitlar = pd.DataFrame(yanitlar)
                        persist("gelen_yanitlar")
                        st.success(f"{len(yanitlar)} adet yanıt bulundu ve sınıflandırıldı!")
                    else: st.info("Henüz bir yanıt bulunamadı.")
                except Exception as e: st.error(f"Bağlantı Hatası: {e}.")

        if not st.session_state.gelen_yanitlar.empty:
            st.write("### 📊 Gelen Yanıtlar")
            st.dataframe(st.session_state.gelen_yanitlar, use_container_width=True)

    st.divider()
    st.subheader("📤 Giden E-posta Logları")
    if not st.session_state.gonderilenler_log.empty:
        st.dataframe(st.session_state.gonderilenler_log.sort_values(by="Tarih", ascending=False), use_container_width=True)
    else: st.info("Henüz hiç e-posta gönderilmedi.")

# ================= 6. SEKME: VİTRİN & HAKKIMDA =================
with tab6:
    st.markdown("""
    <style>
    .hero { background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%); padding: 40px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px; }
    .hero h1 { font-size: 40px; margin-bottom: 10px; }
    .hero p { font-size: 18px; font-weight: 300; }
    .card { background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; color: #333; }
    .card h3 { margin-top: 0; color: #1f4037; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero">
        <h1>♿ Engelsiz Web, Erişilebilir Gelecek</h1>
        <p>Engelli bir birey olarak, kimsenin geride kalmadığı bir dijital dünya için çalışıyorum.</p>
    </div>
    """, unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("""
        <div class="card">
            <h3>👋 Ben Kimim?</h3>
            <p>Merhaba, ben <b>Cuma Babacan</b>. Kendim de bir engelli bireyim ve internetin herkes için eşit derecede erişilebilir olması gerektiğine inanıyorum.</p>
            <p>İşletmelerin web sitelerini engelli bireylerin (görme, işitme, ortopedik engelliler) rahatça kullanabilmesi için denetliyorum. Sadece bir hizmet sunmuyorum; aynı zamanda bir sosyal sorumluluk projesini yürütüyorum.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
            <h3>🛠️ Ne Yapıyorum?</h3>
            <ul>
                <li><b>Erişilebilirlik Denetimi:</b> Sitenizdeki engelleri tespit ediyorum.</li>
                <li><b>Yasal Uyum Danışmanlığı:</b> 2025 Erişilebilirlik Genelgesi'ne uyum sağlamanıza yardımcı oluyorum.</li>
                <li><b>SEO ve Trafik Artışı:</b> Erişilebilir siteler Google tarafından daha üst sıralarda gösterilir, bu da size daha fazla müşteri getirir.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_v2:
        st.markdown("""
        <div class="card">
            <h3>📊 Neden Bana Güvenmelisiniz?</h3>
            <p>Çünkü bu işi <b>yaşayarak</b> yapıyorum.</p>
            <p>Kendi geliştirdiğim bu panel sayesinde saniyeler içinde sitenizin taramasını yapıp, size özel bir rapor çıkarıyorum.</p>
            <p>Müşterilerime sadece "hata listesi" değil, o hataların <b>Türkçe çözüm yollarını</b> ve nasıl düzeltileceğini de sunuyorum. <br><br><i>(İşte bu sistem, kendi sitemi %100 uyumlu hale getirmemi sağladı.)</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
            <h3>📞 İletişime Geçin</h3>
            <p>Web sitenizin engelli bireyler için uygun olup olmadığını ücretsiz öğrenmek ister misiniz?</p>
            <p><b>E-posta:</b> babacan.8691@gmail.com</p>
            <p><b>Hizmet Bölgesi:</b> Türkiye Geneli (Uzaktan Danışmanlık)</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.success("💡 **Unutmayın:** Erişilebilirlik sadece engelli bireyler için değil, geçici sakatlık yaşayanlar, yaşlılar ve mobil cihaz kullanan herkes için gereklidir. Bu, işletmeniz için bir yasal zorunluluk ve aynı zamanda bir fırsattır.")
