import streamlit as st
import requests
import pandas as pd

# --- GÜVENLİK AYARLARI ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

st.set_page_config(page_title="Lofty Otomatik Panel", page_icon="🌐", layout="wide")

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

# --- OTOMATİK PANEL EKRANI ---
else:
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    st.sidebar.markdown("---")
    st.sidebar.info("Sistem Algorand Blokzincirine bağlanarak tüm Lofty mülklerini otomatik listeler.")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🌐 Lofty Mülkleri (Otomatik Blokzincir Taraması)")
    
    if st.button("Tüm Mülkleri Getir"):
        with st.spinner("Algorand ağı taranıyor, Lofty mülkleri aranıyor..."):
            try:
                # Algorand Indexer API - Lofty birim adına (unit-name) sahip varlıkları ara
                # Limit 1000'e kadar çekebiliriz
                url = "https://mainnet-idx.algonode.cloud/v2/assets"
                params = {
                    "unit-name": "LOFTY", # Lofty tokenlarının kısaltması genellikle budur
                    "limit": 1000
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    assets = data.get("assets", [])
                    
                    if not assets:
                        st.warning("Algorand ağında 'LOFTY' birim adına sahip mülk bulunamadı. (Belki farklı bir arama kriteri gerekebilir).")
                    else:
                        # Verileri tabloya uygun hale getirelim
                        mulk_listesi = []
                        for asset in assets:
                            params = asset.get("params", {})
                            mülk_adi = params.get("name", "Bilinmeyen Mülk")
                            
                            # Sadece Lofty mülklerine benzeyenleri filtrele (Çok fazla çöp veri gelirse diye)
                            if "lofty" in mülk_adi.lower() or "lofty" in params.get("unit-name", "").lower():
                                mülk_listesi.append({
                                    "Asset ID": asset.get("index"),
                                    "Mülk Adı": mülk_adi,
                                    "Toplam Arz": params.get("total", 0),
                                    "Ondalık": params.get("decimals", 0),
                                    "Kısaltma (Unit)": params.get("unit-name", "")
                                })
                        
                        if mülk_listesi:
                            st.success(f"Blokzincirden {len(mülk_listesi)} adet Lofty mülkü başarıyla çekildi!")
                            
                            df = pd.DataFrame(mulk_listesi)
                            # Tabloyu göster
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.warning("Arama kriterlerine uyan Lofty mülkü bulunamadı.")
                else:
                    st.error(f"Algorand API Hatası: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")

    st.markdown("---")
    st.markdown("### 📌 Not")
    st.write("Bu panel, Lofty'nin kendi web sitesinden bağımsız olarak doğrudan **Algorand Blokzincirini** tarar. Gelen veriler gerçek ve anlıktır.")
