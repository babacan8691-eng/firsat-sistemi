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

# --- SEKMELER (Hatanın çözümü buradaki tanımlamadır) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Genel Bakış", 
    "👥 Müşteri Yönetimi", 
    "🔍 Gerçek Site Tarayıcı", 
    "🤖 Müşteri Bulucu"
])

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
    if not df.empty: 
        st.dataframe(df, use_container_width=True)
    else: 
        st.warning("Sistemde kayıtlı müşteri yok.")

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
                        st.error("Google API Hatası.")
                except Exception as e:
                    st.error("Zaman aşımı veya bağlantı hatası.")

# 4. SEKME: MÜŞTERİ BULUCU (SERPAPI + EMAIL FINDER MCP)
with tab4:
    st.header("🤖 Müşteri Bulucu: SerpApi + Email Finder")
    st.write("SerpApi ile hedef sektördeki şirketleri bulun, **Email Finder MCP** API'si ile e-postalarını otomatik çekin.")
    
    # Form bloğu (Girişler ve Buton)
    with st.form("lead_gen_form"):
        col_s1, col_s2 = st.columns(2)
        sektor = col_s1.text_input("Hedef Sektör (Örn: butik, klinik)", placeholder="butik")
        sehir = col_s2.text_input("Şehir (İsteğe Bağlı)", placeholder="İstanbul")
        lead_sayisi = st.slider("Kaç adet şirket bulunsun?", 3, 10, 5)
        ara_butonu = st.form_submit_button("Şirketleri ve E-postaları Bul")
        
        if ara_butonu and sektor:
            with st.spinner("Arama yapılıyor ve e-postalar keşfediliyor..."):
                leads = []
                try:
                    # 1. AŞAMA: SERPAPI
                    query = f'"{sektor}" "{sehir}"'
                    params = {
                      "engine": "google", "q": query,
                      "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c",
                      "num": lead_sayisi * 2, "gl": "tr", "hl": "tr"
                    }
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    if "organic_results" in results:
                        for res in results["organic_results"]:
                            if len(leads) >= lead_sayisi: break
                            site_url = res.get("link", "")
                            site_title = res.get("title", "İsimsiz Şirket")
                            
                            # Gereksiz linkleri atla
                            if "google.com/goto" in site_url or "mailerlite.com" in site_url or "wixsite.com" in site_url or "facebook.com" in site_url:
                                continue
                            
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', site_url)
                            if not domain_match: continue
                            domain = domain_match.group(1)
                            
                            # 2. AŞAMA: EMAIL FINDER MCP API
                            api_url = "https://startuphub-validator-service.onrender.com/api/discover-email"
                            payload = {"firstName": "Owner", "lastName": "Founder", "domain": domain}
                            
                            try:
                                response = requests.post(api_url, json=payload, timeout=20)
                                if response.status_code == 200:
                                    data = response.json()
                                    if data.get("success") and data.get("email"):
                                        leads.append({"Şirket": site_title, "Domain": domain, "E-posta": data.get("email"), "Kaynak URL": site_url})
                                    else:
                                        leads.append({"Şirket": site_title, "Domain": domain, "E-posta": "Bulunamadı", "Kaynak URL": site_url})
                                else:
                                    leads.append({"Şirket": site_title, "Domain": domain, "E-posta": "API Hatası", "Kaynak URL": site_url})
                            except:
                                leads.append({"Şirket": site_title, "Domain": domain, "E-posta": "Bağlantı Hatası", "Kaynak URL": site_url})
                            
                            time.sleep(1)
                            
                        # Sonuçları geçici hafızaya al (Buton form dışına taşınabilsin diye)
                        st.session_state.lead_results = leads
                    else:
                        st.warning("Sonuç bulunamadı.")
                except Exception as e:
                    st.error(f"Hata: {e}")

    # Formun DIŞINDA: Sonuçları göster ve indirme butonu ekle
    if 'lead_results' in st.session_state and st.session_state.lead_results:
        sonuc_df = pd.DataFrame(st.session_state.lead_results)
        st.success(f"{len(sonuc_df)} şirket işlendi:")
        st.dataframe(sonuc_df, use_container_width=True)
        
        csv = sonuc_df.to_csv(index=False).encode('utf-8')
        # İndirme butonu artık güvenli bir şekilde formun dışında
        st.download_button(
            label="📥 Sonuçları CSV Olarak İndir",
            data=csv,
            file_name='musteri_adaylari.csv',
            mime='text/csv',
        )
