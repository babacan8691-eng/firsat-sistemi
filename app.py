import streamlit as st
import requests

# --- GÜVENLİK AYARLARI ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

st.set_page_config(page_title="Lofty Panelim", page_icon="🏢")

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.title("Sisteme Giriş")
    kullanici_adi = st.text_input("Kullanıcı Adı").strip()
    sifre = st.text_input("Şifre", type="password").strip()
    
    if st.button("Giriş Yap"):
        if kullanici_adi == DOGRU_KULLANICI and sifre == DOGRU_SIFRE:
            st.session_state.giris_yapildi = True
            st.rerun()
        else:
            st.error("Kullanıcı adı veya şifre hatalı!")

# --- PANEL EKRANI ---
else:
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    
    # API ANAHTARI BURADAN GİRİLECEK
    st.sidebar.markdown("---")
    API_KEY = st.sidebar.text_input("Lofty API Anahtarınızı Girin:", type="password")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🏢 Lofty Yatırım Kontrol Paneli")
    
    # Lofty API Dokümantasyonuna göre bu URL ve endpoint değişebilir
    API_URL = "https://api.lofty.ai/v1/" 
    ENDPOINT = "properties" # Eğer hata alırsak burayı "portfolio" veya "marketplace" yapacağız

    if st.button("Verileri Çek"):
        if not API_KEY:
            st.warning("Lütfen sol menüden (sidebar) API anahtarınızı girin.")
        else:
            # YETKİLENDİRME BAŞLIĞI x-api-key OLARAK GÜNCELLENDİ
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            }
            try:
                response = requests.get(f"{API_URL}{ENDPOINT}", headers=headers)
                if response.status_code == 200:
                    st.success("Bağlantı Başarılı!")
                    st.json(response.json())
                else:
                    st.error(f"Hata: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")
