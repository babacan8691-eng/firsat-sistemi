import streamlit as st
import pandas as pd
import requests
import time

# Sayfa Ayarları
st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")

st.title("♿ Erişilebilirlik Denetim ve Müşteri Yönetim Paneli")
st.markdown("Web sitelerinin engelli erişilebilirliğini **gerçek Google API'si** ile denetleyin, raporlayın ve aylık gelirinizi yönetin.")

# --- VERİ TABANI (Kalıcı Hafıza) ---
if 'musteri_df' not in st.session_state:
    ornek_veri = {
        "Müşteri Adı": ["Örnek Tekstil A.Ş.", "Moda E-Ticaret"],
        "Web Sitesi": ["www.ornektekstil.com", "www.modaeticaret.com"],
        "Hata Sayısı": [14, 8],
        "Aylık Ücret (TL)": [1500.0, 2000.0]
    }
    st.session_state.musteri_df = pd.DataFrame(ornek_veri)

df = st.session_state.musteri_df

# --- SEKMELER ---
tab1, tab2, tab3 = st.tabs(["📊 Genel Bakış", "👥 Müşteri Yönetimi", "🔍 Gerçek Site Tarayıcı"])

# 1. SEKME: GENEL BAKIŞ
with tab1:
    st.header("Sistem Özeti")
    
    col1, col2, col3, col4 = st.columns(4)
    toplam_gelir = df["Aylık Ücret (TL)"].sum()
    toplam_musteri = len(df)
    toplam_hata = df["Hata Sayısı"].sum()
    ortalama_gelir = toplam_gelir / toplam_musteri if toplam_musteri > 0 else 0
    
    col1.metric("Aylık Garantili Gelir", f"{toplam_gelir:,.2f} TL")
    col2.metric("Aktif Müşteri Sayısı", toplam_musteri)
    col3.metric("Tespit Edilen Toplam Hata", toplam_hata)
    col4.metric("Müşteri Başına Ort. Gelir", f"{ortalama_gelir:,.2f} TL")
    
    st.divider()
    
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
            web_sitesi = col_f2.text_input("Web Sitesi URL (https:// olmadan)")
            
            col_f3, col_f4 = st.columns(2)
            hata_sayisi = col_f3.number_input("Bulunan Hata Sayısı", min_value=0, step=1)
            ucret = col_f4.number_input("Aylık Abonelik Ücreti (TL)", min_value=0.0, step=100.0)
            
            kaydet_butonu = st.form_submit_button("Sisteme Kaydet")
            
            if kaydet_butonu:
                if musteri_adi.strip() == "":
                    st.error("Lütfen müşteri adını girin.")
                else:
                    yeni_kayit = pd.DataFrame({
                        "Müşteri Adı": [musteri_adi],
                        "Web Sitesi": [web_sitesi],
                        "Hata Sayısı": [hata_sayisi],
                        "Aylık Ücret (TL)": [ucret]
                    })
                    st.session_state.musteri_df = pd.concat([st.session_state.musteri_df, yeni_kayit], ignore_index=True)
                    st.success(f"{musteri_adi} başarıyla eklendi!")
                    time.sleep(1)
                    st.rerun()

    st.subheader("Kayıtlı Müşteriler")
    st.dataframe(df, use_container_width=True)

# 3. SEKME: GERÇEK TARAYICI (GOOGLE API)
with tab3:
    st.header("Gerçek Erişilebilirlik Tarayıcı")
    st.write("Aşağıya bir site linki girin. Sistem **Google PageSpeed API**'sini kullanarak siteyi canlı olarak tarayacak ve erişilebilirlik skorunu getirecektir. (Büyük sitelerde tarama 1-2 dakika sürebilir, lütfen bekleyin).")
    
    with st.form("tarama_formu"):
        hedef_url = st.text_input("Denetlemek istediğiniz site linkini girin (Örn: trendyol.com, example.com)")
        tara_butonu = st.form_submit_button("Gerçek Taramayı Başlat")
        
        if tara_butonu and hedef_url:
            if not hedef_url.startswith("http"):
                hedef_url = "https://" + hedef_url
                
            with st.spinner(f"{hedef_url} taranıyor... Google sunucularından yanıt bekleniyor (Bu işlem büyük sitelerde 1-2 dakika sürebilir)..."):
                try:
                    # Sizin API Anahtarınız
                    API_KEY = "AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
                    
                    # strategy=desktop ekleyerek daha hızlı sonuç almayı sağlıyoruz
                    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={hedef_url}&category=accessibility&key={API_KEY}&strategy=desktop"
                    
                    # Zaman aşımını 120 saniyeye çıkardık
                    response = requests.get(api_url, timeout=120)
                    
                    if response.status_code != 200:
                        st.error(f"Google API Hatası: {response.status_code}. Site çok büyük olabilir veya API kotanız dolmuş olabilir.")
                    else:
                        data = response.json()
                        
                        if 'lighthouseResult' in data:
                            score = data['lighthouseResult']['categories']['accessibility']['score'] * 100
                            audits = data['lighthouseResult']['audits']
                            
                            # Skoru 0 olan (yani hata veren) testleri filtrele
                            failures = [details['title'] for audit, details in audits.items() if details.get('score') == 0]
                            hata_sayisi = len(failures)
                            
                            st.success("Tarama Tamamlandı! (Gerçek Veri)")
                            
                            col_r1, col_r2 = st.columns(2)
                            col_r1.metric(label="Erişilebilirlik Skoru", value=f"{score:.0f} / 100")
                            col_r2.metric(label="Bulunan Kritik Hata", value=hata_sayisi)
                            
                            if hata_sayisi > 0:
                                st.warning("Bulunan başlıca hatalar:")
                                for hata in failures[:10]:
                                    st.write(f"- {hata}")
                                    
                                st.info(f"💡 **Satış Taktiki:** Bu siteye 'Sitenizde engelli müşterilerin alışveriş yapmasını engelleyen {hata_sayisi} kritik hata buldum. Erişilebilirlik skorunuz 100 üzerinden {score:.0f}. Bu hataları çözmek için aylık bakım paketimiz var' diyebilirsiniz.")
                            else:
                                st.success("Harika! Bu sitede kritik bir erişilebilirlik hatası bulunamadı.")
                        else:
                            st.error("API yanıtı beklenen formatta değil. Lütfen site adresini kontrol edin.")
                            
                except requests.exceptions.Timeout:
                    st.error("Zaman aşımı! Site çok yavaş yanıt veriyor veya Google tarafından engellenmiş olabilir. Lütfen daha küçük bir site (örneğin bir blog) ile test edin.")
                except Exception as e:
                    st.error(f"Beklenmeyen bir hata oluştu: {e}")
