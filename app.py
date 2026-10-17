import streamlit as st
import requests

# --- GÜVENLİK AYARLARI ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

# Sayfa ayarları
st.set_page_config(page_title="Lofty Panelim", page_icon="🏢")

# Oturum durumunu (session state) başlat
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.title("Sisteme Giriş")
    kullanici_adi = st.text_input("Kullanıcı Adı")
    sifre = st.text_input("Şifre", type="password")
    
    if st.button("Giriş Yap"):
        if kullanici_adi == DOGRU_KULLANICI and sifre == DOGRU_SIFRE:
            st.session_state.giris_yapildi = True
            st.rerun() # Sayfayı yenile
        else:
            st.error("Kullanıcı adı veya şifre hatalı!")

# --- PANEL EKRANI (Giriş başarılıysa çalışır) ---
else:
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🏢 Lofty Yatırım Kontrol Paneli")
    
    # API ANAHTARI (Lofty'den aldığın anahtarı tırnak içine yaz)
    API_KEY = "BURAYA_LOFTY_API_ANAHTARINI_YAZ"
    API_URL = "https://api.lofty.ai/v1/" # Örnek URL, dokümana göre güncellenmeli

    if st.button("Verileri Çek"):
        if API_KEY == "BURAYA_LOFTY_API_ANAHTARINI_YAZ":
            st.warning("Lütfen önce kod içindeki API_KEY kısmına Lofty anahtarınızı yazın.")
        else:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            try:
                # Lofty API'sine istek atılıyor
                response = requests.get(f"{API_URL}properties", headers=headers)
                
                if response.status_code == 200:
                    st.success("Bağlantı Başarılı!")
                    st.json(response.json())
                else:
                    st.error(f"Hata: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")
