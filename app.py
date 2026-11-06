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
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")
st.title("♿ Erişilebilirlik Denetim ve Otomasyon Paneli")

# --- KOD İÇİNE GÖMÜLÜ GMAIL BİLGİLERİ ---
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"

# --- VERİ TABANI ---
if 'musteri_df' not in st.session_state:
    st.session_state.musteri_df = pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])
df = st.session_state.musteri_df

if 'lead_results' not in st.session_state:
    st.session_state.lead_results = pd.DataFrame()

if 'gelen_yanitlar' not in st.session_state:
    st.session_state.gelen_yanitlar = pd.DataFrame()

# --- SEKMELER ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Genel Bakış", 
    "👥 Müşteri Yönetimi", 
    "🔍 Gerçek Site Tarayıcı", 
    "🤖 Otomatik Müşteri Bulucu",
    "📧 E-posta Otomasyonu & Yanıtlar"
])

# 1. SEKME: GENEL BAKIŞ
with tab1:
    st.header("Sistem Özeti")
    col1, col2, col3, col4 = st.columns(4)
    toplam_gelir = df["Aylık Ücret (TL)"].sum() if not df.empty else 0.0
    col1.metric("Aylık Garantili Gelir", f"{toplam_gelir:,.2f} TL")
    col2.metric("Aktif Müşteri Sayısı", len(df))
    col3.metric("Tespit Edilen Toplam Hata", df["Hata Sayısı"].sum() if not df.empty else 0)
    
    if not df.empty:
        st.bar_chart(df.set_index("Müşteri Adı")["Aylık Ücret (TL)"], color="#00C853")

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
            yeni = pd.DataFrame({"Müşteri Adı": [musteri_adi], "Web Sitesi": [web_sitesi], "Hata Sayısı": [hata_sayisi], "Aylık Ücret (TL)": [ucret]})
            st.session_state.musteri_df = pd.concat([st.session_state.musteri_df, yeni], ignore_index=True)
            st.rerun()
    st.dataframe(df, use_container_width=True)

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
                        st.write(failures[:5])
                except: st.error("Hata oluştu.")

# 4. SEKME: OTOMATİK MÜŞTERİ BULUCU (TEK TIKLA AVCI)
with tab4:
    st.header("🤖 Tek Tıkla Otomatik Müşteri Bulucu")
    
    # Hazır Sektör Listesi
    hedef_sektorler = ["butik", "klinik", "emlak", "mobilya", "otel", "restoran", "diş kliniği", "avukat"]
    
    with st.form("otomatik_avci"):
        sehir_input = st.selectbox("Hangi Şehirde Aransın?", ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"])
        
        st.info(f"Sistem taranacak sektörleri otomatik seçecek: {', '.join(hedef_sektorler)}")
        baslat_butonu = st.form_submit_button("🚀 Tek Tıkla Taramayı Başlat")
        
        if baslat_butonu:
            # Arama yapılacak şehir ayarı
            arama_sehir = sehir_input
            
            # GÜÇLENDİRİLMİŞ KARA LİSTE
            kara_liste = [
                "yandex", "google", "facebook", "instagram", "sahibinden", "trendyol", 
                "hepsiburada", "n11", "gittigidiyor", "amazon", "wikipedia", "doktorum360", 
                "infobel", "eticaretlink", "com.com", "armut.com", "foursquare", "yelp",
                "bulurum", "rehber", "firmalar", "katalog", "harita", "eksisozluk", "tripadvisor",
                "doktorasistan", "tatilnokta", "menu-tr", "otelz", "etstur", "tatilbudur", "istanbul.net.tr"
            ]
            
            leads = []
            seen_domains = set() # Aynı siteyi tekrar eklememek için hafıza
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            limit = 3 # Her sektör için en fazla 3 site
            
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
                        
                        # Kara liste (URL kontrolü)
                        if any(x in url for x in kara_liste): continue
                        
                        # Başlık kontrolü: Eğer başlıkta bu kelimeler varsa rehber sitesidir, atla
                        if any(x in title for x in ["sarı sayfa", "rehber", "katalog", "firmalar", "listesi", "sayfaları"]): continue
                        
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                        if not domain_match: continue
                        domain = domain_match.group(1)
                        
                        # Eğer bu domain daha önce listeye eklendiyse atla
                        if domain in seen_domains: continue
                        
                        # Google API ile hata sayısını ölç
                        hata = 0
                        try:
                            api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{domain}&category=accessibility&key=AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                            rr = requests.get(api, timeout=20)
                            if rr.status_code == 200:
                                hata = len([d for a, d in rr.json()['lighthouseResult']['audits'].items() if d.get('score') == 0])
                        except: pass
                        
                        # HATA 2'DEN AZ İSE ÇÖPE AT
                        if hata < 2: continue
                            
                        mail = f"info@{domain}"
                        
                        leads.append({
                            "Sektör": sek,
                            "Şirket": r.get("title", domain)[:30],
                            "Domain": domain, 
                            "Hata": hata, 
                            "E-posta": mail,
                            "Durum": "🔥 Sıcak (Hemen Ara)" if hata >= 8 else "Ilık (E-posta At)"
                        })
                        
                        seen_domains.add(domain) # Bulunan siteyi hafızaya kaydet
                        count += 1
                except: pass
                progress_bar.progress((idx + 1) / len(hedef_sektorler))
            
            status_text.text("✅ Tarama tamamlandı!")
            time.sleep(1)
            
            if leads:
                st.session_state.lead_results = pd.DataFrame(leads).sort_values("Hata", ascending=False)
                st.success(f"Harika! Sistem arka planda çalıştı ve **{len(leads)}** adet gerçek/hatalı site buldu.")
            else:
                st.warning("Uygun site bulunamadı. Lütfen farklı bir şehir seçin.")

    if not st.session_state.lead_results.empty:
        st.dataframe(st.session_state.lead_results, use_container_width=True)

# 5. SEKME: E-POSTA OTOMASYONU VE YANITLAR
with tab5:
    st.header("📧 E-posta Gönderimi ve Gelen Kutusu Analizi")
    st.info(f"Sistem **{GMAIL_ADRESI}** adresine bağlı olarak çalışmaya hazır.")
    
    col_gonder, col_oku = st.columns(2)
    
    # --- E-POSTA GÖNDERME KISMI ---
    with col_gonder:
        st.subheader("1. E-posta Gönder")
        if not st.session_state.lead_results.empty:
            if st.button("🚀 Listeye Toplu E-posta Gönder"):
                basarili = 0
                hatali = 0
                progress = st.progress(0)
                
                for i, row in st.session_state.lead_results.iterrows():
                    alici = row['E-posta']
                    site = row['Domain']
                    hata_sayisi = row['Hata']
                    
                    msg = MIMEMultipart()
                    msg['From'] = GMAIL_ADRESI
                    msg['To'] = alici
                    msg['Subject'] = f"{site} sitenizdeki {hata_sayisi} kritik erişilebilirlik hatası hakkında"
                    
                    body = f"""Merhaba,
                    
{site} web sitenizi engelli bireylerin kullanımı açısından inceledim. Google standartlarına göre sitenizde, görme engelli müşterilerinizin alışveriş yapmasını zorlaştıran {hata_sayisi} kritik hata tespit ettim.
                    
Bu hatalar hem yasal risk oluşturuyor hem de potansiyel müşteri kaybına yol açıyor. İsterseniz detaylı raporu gönderebilirim.
                    
Sadece bu e-postaya "Evet" yazmanız yeterli.
                    
Saygılarımla,
Cuma Babacan"""
                    
                    msg.attach(MIMEText(body, 'plain'))
                    
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                        server.send_message(msg)
                        server.quit()
                        basarili += 1
                    except Exception as e:
                        hatali += 1
                        
                    progress.progress((i + 1) / len(st.session_state.lead_results))
                    time.sleep(2) # Spam'a düşmemek için 2 saniye bekle
                    
                st.success(f"İşlem tamam! {basarili} e-posta başarıyla gönderildi. {hatali} hata.")
        else:
            st.info("Gönderilecek liste boş. Önce 'Otomatik Müşteri Bulucu' sekmesinden arama yapın.")

    # --- YANITLARI OKUMA VE SINIFLANDIRMA KISMI ---
    with col_oku:
        st.subheader("2. Gelen Yanıtları Kontrol Et")
        if st.button("📥 Gelen Kutusunu Tara ve Sınıflandır"):
            with st.spinner("Gmail'e bağlanılıyor ve yanıtlar okunuyor..."):
                try:
                    mail = imaplib.IMAP4_SSL("imap.gmail.com")
                    mail.login(GMAIL_ADRESI, GMAIL_SIFRESI)
                    mail.select("inbox")
                    
                    status, messages = mail.search(None, "ALL")
                    mail_ids = messages[0].split()[-20:] # Son 20 mail
                    
                    yanitlar = []
                    olumlu_kelimeler = ["evet", "ilgileniyorum", "rapor", "detay", "fiyat", "görüşelim", "bilgi alabilir"]
                    olumsuz_kelimeler = ["istemiyorum", "ilgilenmiyorum", "çıkarın", "teşekkürler", "uygun değil"]
                    
                    for i in reversed(mail_ids):
                        typ, data = mail.fetch(i, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                konu = msg['Subject']
                                gonderen = msg['From']
                                
                                if "Re:" in konu or "Ynt:" in konu:
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
                        st.success(f"{len(yanitlar)} adet yanıt bulundu ve sınıflandırıldı!")
                    else:
                        st.info("Henüz bir yanıt bulunamadı.")
                        
                except Exception as e:
                    st.error(f"Bağlantı Hatası: {e}. Lütfen Gmail uygulama şifrenizi kontrol edin.")
                    
        if not st.session_state.gelen_yanitlar.empty:
            st.write("### 📊 Gelen Yanıtların Durumu")
            st.dataframe(st.session_state.gelen_yanitlar, use_container_width=True)
