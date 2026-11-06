import streamlit as st
import pandas as pd
import requests
import time
import re
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

# Sayfa Ayarları
st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")

st.title("♿ Erişilebilirlik Denetim ve Müşteri Yönetim Paneli")
st.markdown("Web sitelerinin engelli erişilebilirliğini **gerçek Google API'si** ile denetleyin, raporlayın ve aylık gelirinizi yönetin.")

# --- VERİ TABANI ---
if 'musteri_df' not in st.session_state:
    st.session_state.musteri_df = pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])

df = st.session_state.musteri_df

# --- SEKMELER ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Genel Bakış", "👥 Müşteri Yönetimi", "🔍 Gerçek Site Tarayıcı", "🤖 Otomatik Müşteri Bulucu"])

# 1. SEKME: GENEL BAKIŞ
with tab1:
    st.header("Sistem Özeti")
    col1, col2, col3, col4 = st.columns(4)
    toplam_gelir = df["Aylık Ücret (TL)"].sum() if not df.empty else 0.0
    toplam_musteri = len(df)
    toplam_hata = df["Hata Sayısı"].sum() if not df.empty else 0
    ortalama_gelir = toplam_gelir / toplam_musteri if toplam_musteri > 0 else 0.0
    
    col1.metric("Aylık Garantili Gelir", f"{toplam_gelir:,.2f} TL")
    col2.metric("Aktif Müşteri Sayısı", toplam_musteri)
    col3.metric("Tespit Edilen Toplam Hata", toplam_hata)
    col4.metric("Müşteri Başına Ort. Gelir", f"{ortalama_gelir:,.2f} TL")
    
    st.divider()
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Müşterilere Göre Gelir Dağılımı")
            st.bar_chart(df.set_index("Müşteri Adı")["Aylık Ücret (TL)"], color="#00C853")
        with col_g2:
            st.subheader("Müşteri Sitelerindeki Hata Sayıları")
            st.bar_chart(df.set_index("Müşteri Adı")["Hata Sayısı"], color="#FF5252")

# 2. SEKME: MÜŞTERİ YÖNETİMİ
with tab2:
    st.header("Müşteri ve Denetim Kayıtları")
    with st.expander("➕ Yeni Müşteri / Denetim Ekle", expanded=False):
        with st.form("ekleme_formu", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            musteri_adi = col_f1.text_input("Müşteri Adı")
            web_sitesi = col_f2.text_input("Web Sitesi URL")
            col_f3, col_f4 = st.columns(2)
            hata_sayisi = col_f3.number_input("Bulunan Hata Sayısı", min_value=0, step=1)
            ucret = col_f4.number_input("Aylık Abonelik Ücreti (TL)", min_value=0.0, step=100.0)
            kaydet_butonu = st.form_submit_button("Sisteme Kaydet")
            
            if kaydet_butonu and musteri_adi.strip() != "":
                yeni_kayit = pd.DataFrame({
                    "Müşteri Adı": [musteri_adi], "Web Sitesi": [web_sitesi],
                    "Hata Sayısı": [hata_sayisi], "Aylık Ücret (TL)": [ucret]
                })
                st.session_state.musteri_df = pd.concat([st.session_state.musteri_df, yeni_kayit], ignore_index=True)
                st.success(f"{musteri_adi} eklendi!")
                time.sleep(1)
                st.rerun()

    st.subheader("Kayıtlı Müşteriler")
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.warning("Sistemde kayıtlı müşteri yok.")

# 3. SEKME: GERÇEK TARAYICI
with tab3:
    st.header("Gerçek Erişilebilirlik Tarayıcı")
    with st.form("tarama_formu"):
        hedef_url = st.text_input("Denetlemek istediğiniz site linkini girin (Örn: trendyol.com)")
        tara_butonu = st.form_submit_button("Gerçek Taramayı Başlat")
        
        if tara_butonu and hedef_url:
            if not hedef_url.startswith("http"): hedef_url = "https://" + hedef_url
            with st.spinner(f"{hedef_url} taranıyor..."):
                try:
                    API_KEY = "AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={hedef_url}&category=accessibility&key={API_KEY}&strategy=desktop"
                    response = requests.get(api_url, timeout=120)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'lighthouseResult' in data:
                            score = data['lighthouseResult']['categories']['accessibility']['score'] * 100
                            audits = data['lighthouseResult']['audits']
                            failures = [details['title'] for audit, details in audits.items() if details.get('score') == 0]
                            
                            st.success("Tarama Tamamlandı! (Gerçek Veri)")
                            col_r1, col_r2 = st.columns(2)
                            col_r1.metric("Erişilebilirlik Skoru", f"{score:.0f} / 100")
                            col_r2.metric("Bulunan Kritik Hata", len(failures))
                            
                            if failures:
                                st.warning("Bulunan başlıca hatalar:")
                                for hata in failures[:10]: st.write(f"- {hata}")
                                st.info(f"💡 **Satış Taktiki:** Bu siteye 'Sitenizde engelli müşterilerin alışveriş yapmasını engelleyen {len(failures)} kritik hata buldum. Skorunuz 100 üzerinden {score:.0f}' diyebilirsiniz.")
                    else:
                        st.error("Google API Hatası. Site büyük olabilir veya API kotanız dolmuş olabilir.")
                except Exception as e:
                    st.error("Zaman aşımı veya bağlantı hatası. Lütfen tekrar deneyin.")

# 4. SEKME: OTOMATİK MÜŞTERİ BULUCU (Geliştirilmiş)
with tab4:
    st.header("🤖 Otomatik Müşteri Bulucu")
    with st.form("lead_gen_form"):
        col_s1, col_s2 = st.columns(2)
        sektor = col_s1.text_input("Hedef Sektör (Örn: butik, mobilya, klinik)")
        sehir = col_s2.text_input("Şehir (İsteğe Bağlı, Örn: İstanbul)")
        lead_sayisi = st.slider("Kaç adet site taranıp e-posta aransın?", 5, 20, 10)
        ara_butonu = st.form_submit_button("Potansiyel Müşterileri Bul")
        
        if ara_butonu and sektor:
            with st.spinner("Canlı arama yapılıyor ve e-postalar kazınıyor... (Bu işlem 1-2 dakika sürebilir)"):
                try:
                    SERP_API_KEY = "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c"
                    # Sadece iletişim sayfalarını hedef alan daha akıllı bir arama
                    query = f'"{sektor}" "{sehir}" iletişim'
                    
                    params = {
                      "engine": "google",
                      "q": query,
                      "api_key": SERP_API_KEY,
                      "num": 30, # Daha fazla sonuç çekip içinden en iyilerini seçeceğiz
                      "gl": "tr", # Türkiye sonuçları
                      "hl": "tr"  # Türkçe sonuçlar
                    }
                    
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    leads = []
                    if "organic_results" in results:
                        for res in results["organic_results"]:
                            if len(leads) >= lead_sayisi: break # İstenen sayıya ulaşınca dur
                            
                            site_url = res.get("link", "")
                            site_title = res.get("title", "İsimsiz Site")
                            
                            # ÇÖP SONUÇLARI FİLTRELE
                            if "google.com/goto" in site_url or "mailerlite.com" in site_url or "wixsite.com" in site_url:
                                continue
                            
                            email = "Bulunamadı"
                            
                            # E-posta bulma fonksiyonu
                            def find_email(url):
                                try:
                                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                                    # Önce ana sayfayı dene, sonra /iletisim ve /contact sayfalarını dene
                                    urls_to_try = [url, url.rstrip('/') + '/iletisim', url.rstrip('/') + '/contact']
                                    
                                    for u in urls_to_try:
                                        resp = requests.get(u, timeout=5, headers=headers)
                                        if resp.status_code == 200:
                                            soup = BeautifulSoup(resp.text, 'html.parser')
                                            # mailto linki var mı?
                                            mailto = soup.select('a[href^="mailto:"]')
                                            if mailto:
                                                return mailto[0]['href'].replace('mailto:', '').split('?')[0].strip()
                                            # Metin içinde regex ile ara
                                            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
                                            if emails:
                                                return emails[0]
                                except:
                                    pass
                                return "Bulunamadı"

                            email = find_email(site_url)
                            
                            # Sadece e-posta bulunanları listeye ekle
                            if email != "Bulunamadı":
                                leads.append({"Site Adı": site_title, "URL": site_url, "E-posta": email})
                            else:
                                # E-posta bulunamasa bile siteyi listeye ekle (belki manuel bakarsın)
                                leads.append({"Site Adı": site_title, "URL": site_url, "E-posta": "Manuel Kontrol Et"})
                    
                    if leads:
                        st.success(f"{len(leads)} adet gerçek site bulundu ve e-postalar tarandı!")
                        st.dataframe(pd.DataFrame(leads), use_container_width=True)
                        st.info("💡 **İpucu:** E-postası olanlara hemen mesaj atın. 'Manuel Kontrol Et' yazanların sitesine girip iletişim sayfasından bulabilirsiniz.")
                    else:
                        st.warning("Arama kriterlerine uygun site bulunamadı. Lütfen sektör adını değiştirerek (örn: 'giyim' yerine 'butik') tekrar deneyin.")
                        
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
