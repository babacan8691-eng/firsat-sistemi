import streamlit as st
import pandas as pd
import requests
import time
import re
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from supabase import create_client, Client

st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")
st.title("♿ Erişilebilirlik Denetim ve Otomasyon Paneli")

# --- SUPABASE VERİ TABANI BAĞLANTISI ---
SUPABASE_URL = "https://zdmswqunfnhabeumptsw.supabase.co"
SUPABASE_KEY = "sb_publishable_Au_J5CujUVFKyZzdx7zALw_5qLnIb3r"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- GMAIL BİLGİLERİ ---
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"

# --- HATA ÇEVİRİ SÖZLÜĞÜ ---
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

# --- VERİ TABANI FONKSİYONLARI ---
def musteri_getir():
    try:
        res = supabase.table("musteriler").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"musteri_adi": "Müşteri Adı", "web_sitesi": "Web Sitesi", "hata_sayisi": "Hata Sayısı", "aylik_ucret": "Aylık Ücret (TL)"})
            return df[["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"]]
    except Exception as e:
        st.error(f"Veritabanı Hatası (Müşteriler): {e}")
    return pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])

def log_getir():
    try:
        res = supabase.table("gonderilen_log").select("*").order("tarih", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"tarih": "Tarih", "domain": "Domain", "eposta": "E-posta", "hata_sayisi": "Hata Sayısı", "talep_edilen_ucret": "Talep Edilen Ücret"})
            return df[["Tarih", "Domain", "E-posta", "Hata Sayısı", "Talep Edilen Ücret"]]
    except Exception as e:
        st.error(f"Veritabanı Hatası (Loglar): {e}")
    return pd.DataFrame(columns=["Tarih", "Domain", "E-posta", "Hata Sayısı", "Talep Edilen Ücret"])

def yanit_getir():
    try:
        res = supabase.table("gelen_yanitlar").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"gonderen": "Gönderen", "konu": "Konu", "durum": "Durum"})
            return df[["Gönderen", "Konu", "Durum"]]
    except Exception as e:
        st.error(f"Veritabanı Hatası (Yanıtlar): {e}")
    return pd.DataFrame(columns=["Gönderen", "Konu", "Durum"])

# --- GEÇİCİ HAFIZA (Arama sonuçları için) ---
if 'lead_results' not in st.session_state:
    st.session_state.lead_results = pd.DataFrame()

# --- SEKMELER ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Genel Bakış", 
    "👥 Müşteri Yönetimi", 
    "🔍 Gerçek Site Tarayıcı", 
    "🤖 Otomatik Müşteri Bulucu",
    "📧 E-posta Otomasyonu & Loglar"
])

# 1. SEKME: GENEL BAKIŞ
with tab1:
    st.header("Sistem Özeti ve Başarı Skoru")
    
    df_musteri = musteri_getir()
    df_log = log_getir()
    df_yanit = yanit_getir()
    
    toplam_gonderilen = len(df_log)
    toplam_yanit = len(df_yanit)
    olumlu_yanit_sayisi = len(df_yanit[df_yanit["Durum"] == "🔥 Olumlu (Satışa Hazır)"]) if not df_yanit.empty else 0
    basari_orani = (olumlu_yanit_sayisi / toplam_gonderilen * 100) if toplam_gonderilen > 0 else 0.0
    potansiyel_gelir = df_log["Talep Edilen Ücret"].sum() if not df_log.empty else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gönderilen E-posta", toplam_gonderilen)
    col2.metric("Gelen Yanıt", toplam_yanit)
    col3.metric("Satış Başarı Oranı", f"% {basari_orani:.1f}")
    col4.metric("Potansiyel Ciro", f"{potansiyel_gelir:,.2f} TL")
    
    st.divider()
    st.subheader("Kazanılan Müşteriler (Aktif Gelir)")
    col_m1, col_m2 = st.columns(2)
    toplam_gelir = df_musteri["Aylık Ücret (TL)"].sum() if not df_musteri.empty else 0.0
    col_m1.metric("Aylık Garantili Gelir", f"{toplam_gelir:,.2f} TL")
    col_m2.metric("Aktif Müşteri Sayısı", len(df_musteri))
    
    if not df_musteri.empty:
        st.bar_chart(df_musteri.set_index("Müşteri Adı")["Aylık Ücret (TL)"], color="#00C853")

# 2. SEKME: MÜŞTERİ YÖNETİMİ
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
            try:
                supabase.table("musteriler").insert({
                    "musteri_adi": musteri_adi, 
                    "web_sitesi": web_sitesi, 
                    "hata_sayisi": int(hata_sayisi), 
                    "aylik_ucret": float(ucret)
                }).execute()
                st.success("Müşteri veritabanına kaydedildi!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Kayıt Hatası: {e}")
                
    st.dataframe(musteri_getir(), use_container_width=True)

# 3. SEKME: GERÇEK TARAYICI
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
                except: st.error("Hata oluştu.")

# 4. SEKME: OTOMATİK MÜŞTERİ BULUCU
with tab4:
    st.header("🤖 Tek Tıkla Otomatik Müşteri Bulucu")
    
    hedef_sektorler = ["butik", "klinik", "emlak", "mobilya", "otel", "restoran", "diş kliniği", "avukat"]
    
    with st.form("otomatik_avci"):
        sehir_input = st.selectbox("Hangi Şehirde Aransın?", ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"])
        baslat_butonu = st.form_submit_button("🚀 Tek Tıkla Taramayı Başlat")
        
        if baslat_butonu:
            arama_sehir = sehir_input
            kara_liste = ["yandex", "google", "facebook", "instagram", "sahibinden", "trendyol", "hepsiburada", "n11", "gittigidiyor", "amazon", "wikipedia", "doktorum360", "infobel", "eticaretlink", "com.com", "armut.com", "foursquare", "yelp", "bulurum", "rehber", "firmalar", "katalog", "harita", "eksisozluk", "tripadvisor", "doktorasistan", "tatilnokta", "menu-tr", "otelz", "etstur", "tatilbudur", "istanbul.net.tr", ".gov.tr", ".edu.tr", "ibb.istanbul", "x.com", "kent.edu.tr", "kto.edu.tr", "tim.org.tr", "saygi.tr", "iletisim.com.tr"]
            
            leads = []
            seen_domains = set() 
            progress_bar = st.progress(0)
            status_text = st.empty()
            limit = 3 
            
            for idx, sek in enumerate(hedef_sektorler):
                status_text.text(f"🔍 '{sek}' sektörü taranıyor... ({idx+1}/{len(hedef_sektorler)})")
                query = f'"{sek}" "{arama_sehir}" iletişim site:.com.tr'
                params = {"engine": "google", "q": query, "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c", "num": 20, "gl": "tr"}
                
                try:
                    res = GoogleSearch(params).get_dict().get("organic_results", [])
                    count = 0
                    for r in res:
                        if count >= limit: break
                        url = r.get("link", "")
                        title = r.get("title", "").lower()
                        
                        if any(x in url for x in kara_liste) or any(x in title for x in ["sarı sayfa", "rehber", "katalog", "firmalar", "listesi", "sayfaları", "belediyesi", "üniversitesi", "meclisi", "başkanlığı"]): continue
                        
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                        if not domain_match: continue
                        domain = domain_match.group(1)
                        
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
                        except: pass
                        
                        if hata < 2: continue
                            
                        mail = f"info@{domain}"
                        tahmini_ucret = 1500 + (hata * 200)
                        
                        leads.append({
                            "Sektör": sek, "Şirket": r.get("title", domain)[:30], "Domain": domain, 
                            "Hata": hata, "Tahmini Ücret (TL)": tahmini_ucret, "Hata Detayı (TR)": hata_detaylari,
                            "E-posta": mail, "Durum": "🔥 Sıcak" if hata >= 8 else "Ilık"
                        })
                        seen_domains.add(domain) 
                        count += 1
                except: pass
                progress_bar.progress((idx + 1) / len(hedef_sektorler))
            
            status_text.text("✅ Tarama tamamlandı!")
            time.sleep(1)
            if leads:
                st.session_state.lead_results = pd.DataFrame(leads).sort_values("Hata", ascending=False)
                st.success(f"Sistem **{len(leads)}** adet site buldu.")
            else: st.warning("Uygun site bulunamadı.")

    if not st.session_state.lead_results.empty:
        st.dataframe(st.session_state.lead_results, use_container_width=True)

# 5. SEKME: E-POSTA OTOMASYONU VE LOGLAR
with tab5:
    st.header("📧 E-posta Gönderimi ve Giden Kutusu Logları")
    
    col_gonder, col_oku = st.columns(2)
    
    # --- E-POSTA GÖNDERME KISMI ---
    with col_gonder:
        st.subheader("1. E-posta Gönder")
        if not st.session_state.lead_results.empty:
            if st.button("🚀 Listeye Toplu E-posta Gönder"):
                
                # Veritabanından daha önce gönderilenleri çek (Mükerrer engeli)
                df_eski_log = log_getir()
                gonderilmis_domainler = set(df_eski_log["Domain"].tolist()) if not df_eski_log.empty else set()
                
                gonderilecekler = st.session_state.lead_results[~st.session_state.lead_results["Domain"].isin(gonderilmis_domainler)]
                
                if gonderilecekler.empty:
                    st.warning("Bu listedeki tüm sitelere zaten e-posta gönderilmiş. Mükerrer gönderim engellendi.")
                else:
                    basarili = 0
                    hatali = 0
                    progress = st.progress(0)
                    
                    for i, row in gonderilecekler.iterrows():
                        alici, site, hata_sayisi = row['E-posta'], row['Domain'], row['Hata']
                        tahmini_ucret, hata_detayi = row['Tahmini Ücret (TL)'], row.get('Hata Detayı (TR)', 'çeşitli sorunlar')
                        
                        msg = MIMEMultipart()
                        msg['From'], msg['To'] = GMAIL_ADRESI, alici
                        msg['Subject'] = f"{site} sitenizdeki erişilebilirlik sorunu ve çözümü hakkında"
                        
                        body = f"""Merhaba,\n\n{site} web sitenizi engelli bireylerin kullanımı açısından inceledim. Google standartlarına göre sitenizde **{hata_sayisi}** kritik hata tespit ettim.\n\nTespit ettiğim en önemli sorun(lar): \n**{hata_detayi}**\n\nBu hataların giderilmesi için size özel bir bakım paketimiz mevcut. Tek seferlik çözüm ve aylık takip bedeli **{tahmini_ucret} TL** olarak belirlenmiştir.\n\nAyrıca, 2025 Erişilebilirlik Genelgesi kapsamında işletmelere yönelik idari para cezaları gündemde. \n\nİsterseniz sitenizdeki tüm hataların listesini ve çözüm önerilerini içeren **ücretsiz detaylı raporu** gönderebilirim.\n\nSadece bu e-postaya **"Evet"** yazmanız yeterli.\n\nSaygılarımla,\nCuma Babacan"""
                        msg.attach(MIMEText(body, 'plain', 'utf-8'))
                        
                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                            server.send_message(msg)
                            server.quit()
                            basarili += 1
                            
                            # SUPABASE'E LOG KAYDI
                            supabase.table("gonderilen_log").insert({
                                "domain": site, "eposta": alici, 
                                "hata_sayisi": int(hata_sayisi), "talep_edilen_ucret": float(tahmini_ucret)
                            }).execute()
                            
                        except Exception as e:
                            hatali += 1
                            
                        progress.progress((i + 1) / len(gonderilecekler))
                        time.sleep(2) 
                        
                    st.success(f"İşlem tamam! {basarili} yeni e-posta gönderildi. {hatali} hata.")
                    time.sleep(1)
                    st.rerun() # Sayfayı yenile ki loglar güncellensin
        else:
            st.info("Gönderilecek liste boş. Önce 'Otomatik Müşteri Bulucu' sekmesinden arama yapın.")

    # --- YANITLARI OKUMA KISMI ---
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
                    
                    yeni_yanit_sayisi = 0
                    olumlu_kelimeler = ["evet", "ilgileniyorum", "rapor", "detay", "fiyat", "görüşelim", "bilgi alabilir"]
                    olumsuz_kelimeler = ["istemiyorum", "ilgilenmiyorum", "çıkarın", "teşekkürler", "uygun değil"]
                    
                    for i in reversed(mail_ids):
                        typ, data = mail.fetch(i, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                konu, gonderen = msg['Subject'], msg['From']
                                
                                if "Re:" in konu or "Ynt:" in konu:
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
                                    
                                    # Veritabanına kaydetmeden önce bu yanıt var mı diye kontrol et (Basit mükerrer kontrolü)
                                    mevcut_yanitlar = yanit_getir()
                                    if mevcut_yanitlar.empty or gonderen not in mevcut_yanitlar["Gönderen"].values:
                                        supabase.table("gelen_yanitlar").insert({
                                            "gonderen": gonderen, "konu": konu, "durum": durum
                                        }).execute()
                                        yeni_yanit_sayisi += 1
                    mail.logout()
                    
                    if yeni_yanit_sayisi > 0:
                        st.success(f"{yeni_yanit_sayisi} adet yeni yanıt bulundu ve veritabanına kaydedildi!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("Yeni bir yanıt bulunamadı.")
                        
                except Exception as e:
                    st.error(f"Bağlantı Hatası: {e}.")
                    
        df_y = yanit_getir()
        if not df_y.empty:
            st.write("### 📊 Gelen Yanıtlar")
            st.dataframe(df_y, use_container_width=True)

    # --- GİDEN E-POSTA LOGLARI ---
    st.divider()
    st.subheader("📤 Giden E-posta Logları (Veritabanından Çekiliyor)")
    df_l = log_getir()
    if n
