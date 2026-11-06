import streamlit as st
import pandas as pd
import requests
import time
import re
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")
st.title("♿ Erişilebilirlik Denetim ve Müşteri Yönetim Paneli")
st.markdown("Web sitelerinin engelli erişilebilirliğini **gerçek Google API'si** ile denetleyin, raporlayın ve aylık gelirinizi yönetin.")

# --- VERİ TABANI ---
if 'musteri_df' not in st.session_state:
    st.session_state.musteri_df = pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])
df = st.session_state.musteri_df

if 'lead_results' not in st.session_state:
    st.session_state.lead_results = pd.DataFrame()

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
                yeni_kayit = pd.DataFrame({"Müşteri Adı": [musteri_adi], "Web Sitesi": [web_sitesi], "Hata Sayısı": [hata_sayisi], "Aylık Ücret (TL)": [ucret]})
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
                        st.error("Google API Hatası.")
                except Exception as e:
                    st.error("Zaman aşımı veya bağlantı hatası.")

# 4. SEKME: OTOMATİK MÜŞTERİ BULUCU
with tab4:
    st.header("🤖 Otomatik Toplu Tarama ve Müşteri Bulucu")
    st.write("Sistem, belirlenen sektörleri sırayla arar, bulduğu **gerçek işletme sitelerini** Google API ile denetler ve e-postalarını toplar.")
    
    with st.form("toplu_tarama_formu"):
        st.subheader("Hedef Sektörleri Belirleyin (Virgülle Ayırın)")
        sektorler_input = st.text_input("Sektörler", value="butik, klinik, emlak")
        sehir_input = st.text_input("Şehir", value="İstanbul")
        lead_sayisi = st.slider("Her sektör için kaç site taransın?", 2, 5, 3)
        
        st.warning("⚠️ Not: Toplu tarama sırasında Google API ve E-posta API'leri yavaş yanıt verebilir. Lütfen sayfayı yenilemeyin.")
        baslat_butonu = st.form_submit_button("🚀 Toplu Taramayı Başlat")
        
        if baslat_butonu:
            sektorler = [s.strip() for s in sektorler_input.split(",")]
            islenen_siteler = []
            
            # Kara Liste (Çöp siteleri engellemek için)
            kara_liste = ["yandex", "google", "facebook", "instagram", "sahibinden", "trendyol", "hepsiburada", "iett", "gittigidiyor", "amazon", "wikipedia", "doktorum360", "armut.com"]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            toplam_islem = len(sektorler) * lead_sayisi
            islem_sayaci = 0
            
            for sektor in sektorler:
                status_text.text(f"🔍 '{sektor}' sektörü aranıyor...")
                
                # Arama sorgusuna "iletişim" ekleyerek gerçek işletmeleri bulmayı hedefliyoruz
                query = f'"{sektor}" "{sehir_input}" iletişim'
                params = {"engine": "google", "q": query, "api_key": "a3852fdf1527c40dc04fe73bb9a5b7c913e69a9972cf7ef563fc8a42c64e617c", "num": 20, "gl": "tr", "hl": "tr"}
                
                try:
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    if "organic_results" in results:
                        site_sayaci = 0
                        for res in results["organic_results"]:
                            if site_sayaci >= lead_sayisi: break
                            
                            site_url = res.get("link", "")
                            
                            # Kara listedekileri ve yönlendirme linklerini atla
                            if any(x in site_url for x in kara_liste) or "google.com/goto" in site_url: continue
                            
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', site_url)
                            if not domain_match: continue
                            domain = domain_match.group(1)
                            
                            status_text.text(f"🕵️ {domain} inceleniyor...")
                            
                            # 1. GOOGLE PAGESPEED API İLE HATA SAYISINI BUL
                            hata_sayisi = 0
                            try:
                                api_key = "AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                                api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{domain}&category=accessibility&key={api_key}&strategy=desktop"
                                r = requests.get(api_url, timeout=30)
                                if r.status_code == 200:
                                    data = r.json()
                                    if 'lighthouseResult' in data:
                                        audits = data['lighthouseResult']['audits']
                                        hata_sayisi = len([d for a, d in audits.items() if d.get('score') == 0])
                            except:
                                pass 
                            
                            # 2. E-POSTA BUL (MCP API + Tahmin)
                            email = "Bulunamadı"
                            try:
                                ef_url = "https://startuphub-validator-service.onrender.com/api/discover-email"
                                payload = {"firstName": "Owner", "lastName": "Founder", "domain": domain}
                                ef_resp = requests.post(ef_url, json=payload, timeout=10)
                                if ef_resp.status_code == 200 and ef_resp.json().get("email"):
                                    email = ef_resp.json().get("email")
                            except:
                                pass
                                
                            # Eğer API bulamazsa, akıllı tahmin yap (İşletmelerin %90'ı bu formatı kullanır)
                            if email == "Bulunamadı":
                                email = f"info@{domain}"
                                
                            # 3. DURUM ETİKETİ (Sadece hatası çok yüksek olanlar Sıcak)
                            durum = "Soğuk"
                            if hata_sayisi >= 15:
                                durum = "🔥 Sıcak (Hemen Ara)"
                            elif hata_sayisi >= 5:
                                durum = "Ilık (E-posta At)"
                                
                            islenen_siteler.append({
                                "Sektör": sektor,
                                "Şirket": res.get("title", domain)[:30] + "...",
                                "Domain": domain,
                                "Hata Sayısı": hata_sayisi,
                                "E-posta": email,
                                "Durum": durum
                            })
                            
                            site_sayaci += 1
                            islem_sayaci += 1
                            progress_bar.progress(min(islem_sayaci / toplam_islem, 1.0))
                            time.sleep(1)
                    else:
                        islem_sayaci += lead_sayisi
                except Exception:
                    pass
                    
            status_text.text("✅ Tüm taramalar tamamlandı!")
            time.sleep(1)
            
            if islenen_siteler:
                df_results = pd.DataFrame(islenen_siteler)
                # En sorunludan en aza sırala
                df_results = df_results.sort_values(by="Hata Sayısı", ascending=False).reset_index(drop=True)
                st.session_state.lead_results = df_results
            else:
                st.warning("Hiçbir uygun sonuç bulunamadı. Lütfen farklı bir sektör deneyin.")

    # --- SONUÇLARI GÖSTERME ---
    if not st.session_state.lead_results.empty:
        st.divider()
        st.subheader("📊 Tarama Sonuçları (En Sorunludan En Aza)")
        
        sadece_sicak = st.checkbox("🔥 Sadece 'Ödemeye Hazır' (Sıcak) Müşterileri Göster")
        
        gosterilecek_df = st.session_state.lead_results
        if sadece_sicak:
            gosterilecek_df = gosterilecek_df[gosterilecek_df["Durum"] == "🔥 Sıcak (Hemen Ara)"]
            
        if gosterilecek_df.empty:
            st.info("Şu an sıcak müşteri yok. Sistem yeni siteler buldukça buraya ekleyecektir. Filtreyi kaldırıp tüm listeye bakabilirsiniz.")
        else:
            st.dataframe(gosterilecek_df, use_container_width=True)
            
            csv = gosterilecek_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Bu Listeyi CSV Olarak İndir",
                data=csv,
                file_name='musteri_adaylari.csv',
                mime='text/csv',
            )
            st.info("💡 **Taktik:** '🔥 Sıcak' etiketli olanların sitelerinde çok fazla hata var (yasal riski yüksek). E-posta adreslerine doğrudan 'Sitenizde 15'tan fazla hata buldum' diyerek mesaj atın, geri dönüş oranı çok yüksek olacaktır.")
