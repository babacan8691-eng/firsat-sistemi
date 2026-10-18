import streamlit as st
import requests
import pandas as pd

# --- GÜVENLİK AYARLARI ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

st.set_page_config(page_title="Lofty Algorand Panelim", page_icon="🌐", layout="wide")

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
    st.sidebar.markdown("---")
    
    # Algorand API ayarları
    st.sidebar.info("Bu panel Algorand Blokzinciri üzerinden çalışır. API anahtarı gerekmez.")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🌐 Lofty Blokzincir Kontrol Paneli (Algorand)")
    
    st.markdown("""
    Aşağıya Lofty'deki bir mülkün **Asset ID (Varlık ID)** numarasını girerek, o mülkün blokzincir üzerindeki gerçek verilerini (toplam arz, isim, son işlemler) çekebilirsin.
    """)

    # Kullanıcıdan Asset ID girmesini iste
    asset_id = st.text_input("Lofty Mülk Asset ID (Örn: 123456789):", "")

    if st.button("Blokzincirden Veri Çek"):
        if not asset_id.isdigit():
            st.warning("Lütfen geçerli bir sayısal Asset ID girin.")
        else:
            try:
                # 1. Mülk (Token) Detaylarını Çek
                asset_url = f"https://mainnet-idx.algonode.cloud/v2/assets/{asset_id}"
                response = requests.get(asset_url)
                
                if response.status_code == 200:
                    data = response.json()
                    asset_info = data.get("asset", {})
                    params = asset_info.get("params", {})
                    
                    st.success("Gerçek Blokzincir Verisi Başarıyla Çekildi!")
                    
                    # Verileri Göster
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Mülk Adı (Token)", params.get("name", "Bilinmiyor"))
                    col2.metric("Toplam Hisse (Arz)", params.get("total", 0))
                    col3.metric("Ondalık (Decimal)", params.get("decimals", 0))
                    
                    st.write(f"**Birim Kısaltması (Unit):** {params.get('unit-name', 'Bilinmiyor')}")
                    st.write(f"**Oluşturan Cüzdan (Lofty):** {params.get('creator', 'Bilinmiyor')}")
                    
                    st.markdown("---")
                    st.markdown("### 📊 Son İşlemler (Blokzincir Kayıtları)")
                    
                    # 2. Son İşlemleri Çek
                    tx_url = f"https://mainnet-idx.algonode.cloud/v2/assets/{asset_id}/transactions?limit=10"
                    tx_response = requests.get(tx_url)
                    
                    if tx_response.status_code == 200:
                        tx_data = tx_response.json()
                        transactions = tx_data.get("transactions", [])
                        
                        if not transactions:
                            st.info("Bu mülk için henüz blokzincir üzerinde kayıtlı bir transfer/işlem bulunmuyor.")
                        else:
                            tx_list = []
                            for tx in transactions:
                                tx_list.append({
                                    "İşlem ID": tx.get("id")[:10] + "...", # Kısaltılmış ID
                                    "Zaman": tx.get("round-time", 0), # Unix zaman damgası
                                    "İşlem Miktarı": tx.get("asset-transfer-transaction", {}).get("amount", 0),
                                    "Gönderen": tx.get("sender", "")[:10] + "...",
                                })
                            df = pd.DataFrame(tx_list)
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("Son işlemler çekilemedi.")
                        
                elif response.status_code == 404:
                    st.error("Hata: Bu Asset ID'ye sahip bir varlık Algorand ağında bulunamadı. Lütfen ID'yi kontrol edin.")
                else:
                    st.error(f"Algorand API Hatası: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")
