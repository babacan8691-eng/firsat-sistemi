import streamlit as st
import pandas as pd
import requests
import time
import re
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")
st.title("♿ Erişilebilirlik Denetim ve Müşteri Yönetim Paneli")

if 'musteri_df' not in st.session_state:
    st.session_state.musteri_df = pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])
df = st.session_state.musteri_df

tab1, tab2, tab3, tab4 = st.tabs(["📊 Genel Bakış", "👥 Müşteri Yönetimi", "🔍 Gerçek Site Tarayıcı", "🤖 Müşteri Bulucu (SerpApi + Email Finder)"])

# ... (1, 2 ve 3. Sekmeler önceki kodla aynı kalacak) ...

# 4. SEKME: MÜŞTERİ BULUCU (SERPAPI + EMAIL FINDER MCP)
with tab4:
    st.header("🤖 Müşteri Bulucu: SerpApi + Email Finder MCP")
    st.write("SerpApi ile hedef sektördeki şirketleri bulun, **Email Finder MCP** (ücretsiz ve limitsiz) API'si ile bu şirketlerin e-posta adreslerini otomatik çekin.")
    
    with st.form("lead_gen_form_email_finder"):
        col_s1, col_s2 = st.columns(2)
        sektor = col_s1.text_input("Hedef Sektör (Örn: butik, mobilya, klinik)", placeholder="butik")
        sehir = col_s2.text_input("Şehir (İsteğe Bağlı, Örn: İstanbul)", placeholder="İstanbul")
        
        lead_sayisi = st.slider("Kaç adet şirket bulunsun ve e-postaları çekilsin?", 3, 10, 5)
        ara_butonu = st.form_submit_button("Şirketleri ve E-postaları Bul")
        
        if ara_butonu and sektor:
            with st.spinner("SerpApi ile şirketler aranıyor, Email Finder ile e-postalar keşfediliyor... (İlk istekte 10 sn gecikme olabilir)"):
                leads = []
                try:
                    # 1. AŞAMA: SERPAPI İLE ŞİRKETLERİ BUL
                    query = f'"{sektor}" "{sehir}"'
                    params = {
                      "engine": "google",
                      "q": query,
                      "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c", # SerpApi Anahtarınız
                      "num": lead_sayisi * 2,
                      "gl": "tr",
                      "hl": "tr"
                    }
                    
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    if "organic_results" not in results:
                        st.warning("SerpApi sonuç döndürmedi. Lütfen farklı bir sektör deneyin.")
                    else:
                        # 2. AŞAMA: HER ŞİRKET İÇİN EMAIL FINDER MCP'DEN E-POSTA KEŞFET
                        for res in results["organic_results"]:
                            if len(leads) >= lead_sayisi: break
                            
                            site_url = res.get("link", "")
                            site_title = res.get("title", "İsimsiz Şirket")
                            
                            if "google.com/goto" in site_url or "mailerlite.com" in site_url or "wixsite.com" in site_url:
                                continue
                            
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', site_url)
                            if not domain_match:
                                continue
                            domain = domain_match.group(1)
                            
                            # Email Finder MCP API'sine istek at
                            api_url = "https://startuphub-validator-service.onrender.com/api/discover-email"
                            payload = {
                                "firstName": "Owner", # Genel bir unvan kullanıyoruz
                                "lastName": "Founder",
                                "domain": domain
                            }
                            
                            try:
                                # İlk istekte 10 saniye gecikme olabileceği için timeout süresini uzun tutuyoruz
                                response = requests.post(api_url, json=payload, timeout=20)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    if data.get("success") and data.get("email"):
                                        leads.append({
                                            "Şirket": site_title,
                                            "Domain": domain,
                                            "E-posta": data.get("email"),
                                            "Kaynak URL": site_url
                                        })
                                    else:
                                        leads.append({
                                            "Şirket": site_title,
                                            "Domain": domain,
                                            "E-posta": "Bulunamadı",
                                            "Kaynak URL": site_url
                                        })
                                else:
                                    leads.append({
                                        "Şirket": site_title,
                                        "Domain": domain,
                                        "E-posta": f"API Hatası ({response.status_code})",
                                        "Kaynak URL": site_url
                                    })
                            except requests.exceptions.Timeout:
                                leads.append({
                                    "Şirket": site_title,
                                    "Domain": domain,
                                    "E-posta": "Zaman Aşımı",
                                    "Kaynak URL": site_url
                                })
                            except Exception as e:
                                leads.append({
                                    "Şirket": site_title,
                                    "Domain": domain,
                                    "E-posta": "Bağlantı Hatası",
                                    "Kaynak URL": site_url
                                })
                            
                            time.sleep(1) # API'yi yormamak için kısa bekleme
                    
                    if leads:
                        st.success(f"{len(leads)} şirket işlendi. Sonuçlar aşağıda:")
                        sonuc_df = pd.DataFrame(leads)
                        st.dataframe(sonuc_df, use_container_width=True)
                        
                        csv = sonuc_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Sonuçları CSV Olarak İndir",
                            data=csv,
                            file_name='musteri_adaylari_email_finder.csv',
                            mime='text/csv',
                        )
                        st.info("💡 E-postası bulunan şirketlere doğrudan satış e-postası gönderebilirsiniz. 'Bulunamadı' yazanlar için şirketin sitesindeki 'İletişim' sayfasını manuel kontrol etmeniz gerekebilir.")
                    else:
                        st.warning("Kriterlere uygun şirket bulunamadı. Lütfen arama terimlerini değiştirin.")
                        
                except Exception as e:
                    st.error(f"Genel bir hata oluştu: {e}")
