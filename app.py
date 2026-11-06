import streamlit as st
import pandas as pd
import numpy as np
import time

# Sayfa Ayarları (Geniş Ekran)
st.set_page_config(page_title="Erişilebilirlik Paneli", layout="wide")

# Başlık ve Açıklama
st.title("♿ Erişilebilirlik Denetim ve Müşteri Yönetim Paneli")
st.markdown("Web sitelerinin engelli erişilebilirliğini denetleyin, raporlayın ve aylık gelirinizi yönetin.")

# --- VERİ TABANI BAŞLANGICI (Örnek Veriler) ---
if 'musteri_df' not in st.session_state:
    # Sistem boş görünmesin diye örnek (demo) veriler ekliyoruz
    ornek_veri = {
        "Müşteri Adı": ["Örnek Tekstil A.Ş.", "Moda E-Ticaret", "Yerel Market Zinciri"],
        "Web Sitesi": ["www.ornektekstil.com", "www.modaeticaret.com", "www.yerelmarket.com"],
        "Hata Sayısı": [14, 8, 22],
        "Aylık Ücret (TL)": [1500.0, 2000.0, 1200.0]
    }
    st.session_state.musteri_df = pd.DataFrame(ornek_veri)

df = st.session_state.musteri_df

# --- SEKMELER (TABS) ---
tab1, tab2, tab3 = st.tabs(["📊 Genel Bakış (Dashboard)", "👥 Müşteri Yönetimi", "🔍 Otomatik Site Tarayıcı"])

# 1. SEKME: GENEL BAKIŞ
with tab1:
    st.header("Sistem Özeti")
    
    # İstatistikler (KPI)
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
    
    # Grafikler
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
    
    # Yeni Müşteri Ekleme Formu
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

    # Mevcut Müşteriler Tablosu
    st.subheader("Kayıtlı Müşteriler")
    st.dataframe(df, use_container_width=True)
    
    # Tabloyu indirme butonu
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Müşteri Listesini CSV olarak İndir",
        data=csv,
        file_name='musteri_listesi.csv',
        mime='text/csv',
    )

# 3. SEKME: OTOMATİK TARAYICI
with tab3:
    st.header("Hızlı Erişilebilirlik Tarayıcı (Potansiyel Müşteri Bulucu)")
    st.write("Bu araç, hedeflediğiniz bir sitenin erişilebilirlik durumunu simüle eder ve size potansiyel bir teklif sunar.")
    
    with st.form("tarama_formu"):
        hedef_url = st.text_input("Denetlemek istediğiniz site linkini girin (Örn: www.hedefsite.com)")
        tara_butonu = st.form_submit_button("Siteyi Tara")
        
        if tara_butonu and hedef_url:
            with st.spinner(f"{hedef_url} taranıyor... Lütfen bekleyin..."):
                time.sleep(2) # Gerçekçi bir bekleme süresi
                
                # Simüle edilmiş tarama sonuçları (Gerçekte burada WAVE API'si çağrılır)
                hata = np.random.randint(5, 35)
                tahmini_kayip = hata * 500 # Her hatanın aylık 500 TL kayba yol açtığını varsayalım
                
                st.success("Tarama tamamlandı!")
                
                col_r1, col_r2 = st.columns(2)
                col_r1.error(f"Bulunan Erişilebilirlik Hatası: **{hata}**")
                col_r2.warning(f"Tahmini Aylık Müşteri Kaybı: **{tahmini_kayip:,.2f} TL**")
                
                st.info(f"💡 **Satış Taktiki:** Bu siteye 'Sitenizde engelli müşterilerin alışveriş yapmasını engelleyen {hata} hata buldum. Aylık {tahmini_kayip} TL kaybediyorsunuz. Bu hataları çözmek için aylık 1.500 TL'lik bakım paketimiz var' diyebilirsiniz.")
