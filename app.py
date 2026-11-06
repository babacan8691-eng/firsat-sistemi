import streamlit as st
import pandas as pd

# Sayfa ayarları
st.set_page_config(page_title="Erişilebilirlik Paneli", layout="centered")

st.title("Erişilebilirlik Denetim ve Müşteri Takip Paneli")
st.write("WAVE veya Lighthouse ile denetlediğiniz siteleri buraya kaydedin ve aylık garantili gelirinizi takip edin.")

# Verilerin sayfa yenilenince kaybolmaması için session_state kullanıyoruz
if 'musteri_df' not in st.session_state:
    st.session_state.musteri_df = pd.DataFrame(columns=["Müşteri Adı", "Web Sitesi", "Hata Sayısı", "Aylık Ücret (TL)"])

# Yeni müşteri ekleme formu
with st.form("ekleme_formu", clear_on_submit=True):
    st.subheader("Yeni Müşteri / Denetim Ekle")
    
    musteri_adi = st.text_input("Müşteri Adı")
    web_sitesi = st.text_input("Web Sitesi URL")
    hata_sayisi = st.number_input("Bulunan Hata Sayısı", min_value=0, step=1)
    ucret = st.number_input("Aylık Abonelik Ücreti (TL)", min_value=0.0, step=100.0)
    
    kaydet_butonu = st.form_submit_button("Kaydet")
    
    if kaydet_butonu:
        if musteri_adi.strip() == "":
            st.error("Lütfen müşteri adını girin.")
        else:
            # Yeni veriyi tabloya ekle
            yeni_kayit = pd.DataFrame({
                "Müşteri Adı": [musteri_adi],
                "Web Sitesi": [web_sitesi],
                "Hata Sayısı": [hata_sayisi],
                "Aylık Ücret (TL)": [ucret]
            })
            st.session_state.musteri_df = pd.concat([st.session_state.musteri_df, yeni_kayit], ignore_index=True)
            st.success(f"{musteri_adi} başarıyla eklendi!")

# Müşteri listesini ve toplam geliri gösterme
st.subheader("Mevcut Müşteriler ve Denetimler")

if not st.session_state.musteri_df.empty:
    # Tabloyu göster
    st.dataframe(st.session_state.musteri_df, use_container_width=True)
    
    # Toplam geliri hesapla
    toplam_gelir = st.session_state.musteri_df["Aylık Ücret (TL)"].sum()
    
    # Toplam geliri büyük ve dikkat çekici bir kutuda göster
    st.metric(label="Toplam Aylık Garantili Gelir", value=f"{toplam_gelir:,.2f} TL")
else:
    st.info("Henüz kayıtlı bir müşteri yok. Yukarıdaki formu kullanarak ilk müşterinizi ekleyin.")
