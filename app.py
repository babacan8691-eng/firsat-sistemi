import streamlit as st
import requests
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Lofty Yatırım Paneli", page_icon="🏢", layout="wide")

# --- CSS İLE TASARIM ---
st.markdown("""
    <style>
    .mulk-karti {
        background-color: #1E1E2E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3A3A5A;
        margin-bottom: 20px;
    }
    .mulk-baslik { color: #FFFFFF; font-size: 20px; font-weight: bold; }
    .mulk-detay { color: #A0A0C0; font-size: 14px; }
    .helal-uygun { color: #4CAF50; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ BİLGİLERİ ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

# --- OTURUM DURUMU ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "lofty_api_key" not in st.session_state:
    st.session_state.lofty_api_key = ""

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
    # --- YAN MENÜ ---
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Lofty API Ayarı")
    st.sidebar.info("Canlı verileri çekmek için API anahtarınızı girin.")
    
    api_input = st.sidebar.text_input("Lofty API Anahtarı:", type="password", value=st.session_state.lofty_api_key).strip()
    
    if st.sidebar.button("Anahtarı Kaydet"):
        if api_input:
            st.session_state.lofty_api_key = api_input
            st.sidebar.success("API Anahtarı kaydedildi!")
            st.rerun()
        else:
            st.sidebar.error("Lütfen bir anahtar girin.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.session_state.lofty_api_key = ""
        st.rerun()

    # --- ANA EKRAN ---
    st.title("🏢 Lofty Gayrimenkul Yatırım Paneli")
    
    tab1, tab2, tab3 = st.tabs(["🏠 Pazar Yeri (Kart Görünümü)", "📊 İslami Uygunluk Analizi", "🔄 Alım-Satım (Emir Defteri)"])

    # --- VERİ ÇEKME (Algorand) ---
    @st.cache_data(ttl=300)
    def mülk_listesini_cek():
        lofty_listesi = []
        try:
            url = "https://mainnet-idx.algonode.cloud/v2/assets"
            params = {"name": "lofty", "limit": 1000} 
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                for asset in data.get("assets", []):
                    params_data = asset.get("params", {})
                    mülk_adi = str(params_data.get("name", ""))
                    if "lofty" in mülk_adi.lower() and "ai" not in mülk_adi.lower():
                        lofty_listesi.append({
                            "Asset ID": asset.get("index"),
                            "Mülk Adı": mülk_adi,
                            "Toplam Arz": params_data.get("total", 0),
                        })
        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")
        return pd.DataFrame(lofty_listesi)

    # --- GELİŞMİŞ API TEST FONKSİYONU (Tarayıcı Taklidi ve Çoklu URL Denemesi) ---
    @st.cache_data(ttl=60) 
    def gelismis_api_test(api_key):
        if not api_key:
            return {"error": "API Anahtarı girilmedi."}
            
        # 1. ADIM: Tarayıcı taklidi (Cloudflare/bot engelini aşmak için)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key, # Bazı API'ler bu başlığı ister
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 2. ADIM: Lofty'nin kullanma ihtimali olan farklı URL'leri deniyoruz
        denenecek_urller = [
            "https://api.lofty.ai/api/v1/properties",
            "https://api.lofty.ai/v1/properties",
            "https://api.lofty.ai/graphql",
            "https://www.lofty.ai/api/v1/properties"
        ]
        
        sonuclar = []
        
        for url in denenecek_urller:
            try:
                # GET isteği deniyoruz
                response = requests.get(url, headers=headers, timeout=10)
                
                # Eğer 200 dönerse harika, bu URL doğru!
                if response.status_code == 200:
                    return {"status": "success", "url": url, "data": response.json()}
                else:
                    sonuclar.append(f"{url} -> Hata Kodu: {response.status_code}")
                    
            except Exception as e:
                sonuclar.append(f"{url} -> Bağlantı Hatası: {str(e)}")
                
        # Eğer hiçbiri 200 dönmezse, hata detaylarını döndür
        return {"error": "Tüm URL'ler denendi ancak başarısız oldu.", "detaylar": sonuclar}

    # --- TAB 1: PAZAR YERİ ---
    with tab1:
        st.markdown("### Blokzincirden Çekilen Güncel Mülkler")
        
        if not st.session_state.lofty_api_key:
            st.warning("⚠️ Sol menüden Lofty API anahtarınızı girip 'Kaydet' butonuna basın.")

        if st.button("Verileri Yenile"):
            st.cache_data.clear()
            st.rerun()
            
        df = mülk_listesini_cek()
        
        if df.empty:
            st.warning("Mülkler çekilemedi.")
        else:
            # API Testini çalıştır
            api_test_sonucu = gelismis_api_test(st.session_state.lofty_api_key)
            
            st.success(f"Blokzincirden toplam {len(df)} adet Lofty mülkü çekildi!")
            
            gosterilecek_mulkler = df.head(12)
            
            for i in range(0, len(gosterilecek_mulkler), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(gosterilecek_mulkler):
                        mülk = gosterilecek_mulkler.iloc[i + j]
                        with cols[j]:
                            if "error" in api_test_sonucu:
                                fiyat_metni = f"<span style='color: #FF5555;'>API Hatası</span>"
                            else:
                                fiyat_metni = "<span style='color: #00FF00;'>Bağlantı Başarılı!</span>"

                            st.markdown(f"""
                                <div class="mulk-karti">
                                    <div class="mulk-baslik">{mülk['Mülk Adı']}</div>
                                    <div class="mulk-detay">Asset ID: {mülk['Asset ID']}</div>
                                    <div class="mulk-detay">Toplam Hisse: {mülk['Toplam Arz']}</div>
                                    <hr style="border-color: #3A3A5A;">
                                    <div class="helal-uygun">✅ Reel Varlık (Helal)</div>
                                    <div class="mulk-detay" style="margin-top: 5px;">Durum: {fiyat_metni}</div>
                                </div>
                            """, unsafe_allow_html=True)
            
            # GELİŞTİRİCİ ÇIKTISI (Hatanın tam sebebini burada göreceğiz)
            with st.expander("🛠️ Geliştirici API Test Çıktısı (Detaylar İçin Açın)", expanded=True):
                st.write("Lofty API'sinden gelen yanıtlar:")
                if "error" in api_test_sonucu:
                    st.error(api_test_sonucu["error"])
                    if "detaylar" in api_test_sonucu:
                        for detay in api_test_sonucu["detaylar"]:
                            st.write(f"- {detay}")
                else:
                    st.success(f"API Bağlantısı Başarılı! Çalışan URL: {api_test_sonucu['url']}")
                    st.json(api_test_sonucu["data"])

    # --- TAB 2 ve TAB 3 (Değişmedi) ---
    with tab2:
        st.markdown("### 🕌 İslami Finans (Helal Yatırım) Açısından Lofty")
        st.info("Lofty modeli reel varlığa dayandığı için helal kabul edilir. Detaylar...")
        
    with tab3:
        st.markdown("### 🔄 Alıcı ve Satıcı Listesi (Order Book)")
        st.info("Lofty API bağlantısı sağlandığında burada canlı emir defteri görüntülenecektir.")
