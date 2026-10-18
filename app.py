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
    st.sidebar.info("Sistem Algorand Blokzincirine bağlanarak isminde 'Lofty' geçen tüm mülkleri listeler.")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🌐 Lofty Mülkleri (Otomatik Blokzincir Taraması)")
    
    if st.button("Tüm Mülkleri Getir"):
        with st.spinner("Algorand ağında 'Lofty' mülkleri aranıyor..."):
            lofty_listesi = [] 
            
            try:
                # Algorand Indexer API - İsminde 'Lofty' geçen varlıkları ara
                url = "https://mainnet-idx.algonode.cloud/v2/assets"
                params = {
                    "name": "Lofty", # API'ye doğrudan isim filtresi gönderiyoruz
                    "limit": 1000
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    assets = data.get("assets", [])
                    
                    for asset in assets:
                        params_data = asset.get("params", {})
                        mülk_adi = str(params_data.get("name", ""))
                        
                        # Sadece gerçekten Lofty ile ilgili olanları ayıkla (bazen başka şeyler çıkabilir)
                        if "lofty" in mülk_adi.lower():
                            lofty_listesi.append({
                                "Asset ID": asset.get("index"),
                                "Mülk Adı": mülk_adi,
                                "Toplam Arz": params_data.get("total", 0),
                                "Ondalık": params_data.get("decimals", 0),
                            })
                    
                    if not lofty_listesi:
                        st.warning("Algorand ağında yapılan taramada Lofty mülkü bulunamadı. Algorand isimlendirmesi farklı olabilir.")
                    else:
                        st.success(f"Blokzincirden {len(lofty_listesi)} adet Lofty mülkü başarıyla çekildi!")
                        df = pd.DataFrame(lofty_listesi)
                        st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"Algorand API Hatası: {response.status_code} - {response.text}")
                    
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")

    st.markdown("---")
    st.markdown("### 📌 Not")
    st.write("Bu panel, Lofty'nin kendi web sitesinden bağımsız olarak doğrudan **Algorand Blokzincirini** tarar. Gelen veriler gerçek ve anlıktır.")
