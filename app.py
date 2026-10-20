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

# --- GİRİŞ BİLGİLERİ (Sabit) ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

# --- OTURUM DURUMU (Hafıza) ---
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
    # --- YAN MENÜ (API AYARLARI) ---
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Lofty API Ayarı")
    st.sidebar.info("Canlı verileri çekmek için API anahtarınızı girin.")
    
    # Anahtar daha önce girilmediyse veya değiştirilmek isteniyorsa
    api_input = st.sidebar.text_input("Lofty API Anahtarı:", type="password", value=st.session_state.lofty_api_key)
    
    if st.sidebar.button("Anahtarı Kaydet"):
        if api_input:
            st.session_state.lofty_api_key = api_input
            st.sidebar.success("API Anahtarı başarıyla kaydedildi!")
            st.rerun()
        else:
            st.sidebar.error("Lütfen bir anahtar girin.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.session_state.lofty_api_key = "" # Çıkışta anahtarı temizle
        st.rerun()

    # --- ANA EKRAN ---
    st.title("🏢 Lofty Gayrimenkul Yatırım Paneli")
    
    tab1, tab2, tab3 = st.tabs(["🏠 Pazar Yeri (Kart Görünümü)", "📊 İslami Uygunluk Analizi", "🔄 Alım-Satım (Emir Defteri)"])

    # --- VERİ ÇEKME FONKSİYONU (Algorand) ---
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

    # --- CANLI FİYAT ÇEKME FONKSİYONU (Lofty API) ---
    @st.cache_data(ttl=60) 
    def canli_fiyat_cek(asset_id, api_key):
        if not api_key:
            return {"error": "API Anahtarı girilmedi."}
            
        url = "https://api.lofty.ai/api/v1/properties" 
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json() 
            elif response.status_code == 403:
                return {"error": "API Anahtarı Yetkisiz (403). Lütfen anahtarınızı kontrol edin."}
            else:
                return {"error": f"Bilinmeyen Hata: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}

    # --- TAB 1: PAZAR YERİ (KARTLAR) ---
    with tab1:
        st.markdown("### Blokzincirden Çekilen Güncel Mülkler")
        
        # Eğer anahtar girilmemişse kullanıcıyı uyar
        if not st.session_state.lofty_api_key:
            st.warning("⚠️ Sol menüden Lofty API anahtarınızı girip 'Kaydet' butonuna basın. Aksi takdirde canlı fiyatlar çekilemez.")

        if st.button("Verileri Yenile"):
            st.cache_data.clear()
            st.rerun()
            
        df = mülk_listesini_cek()
        
        if df.empty:
            st.warning("Mülkler çekilemedi.")
        else:
            st.success(f"Blokzincirden toplam {len(df)} adet Lofty mülkü çekildi!")
            
            gosterilecek_mulkler = df.head(12)
            
            for i in range(0, len(gosterilecek_mulkler), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(gosterilecek_mulkler):
                        mülk = gosterilecek_mulkler.iloc[i + j]
                        with cols[j]:
                            # API anahtarını session_state'ten alıyoruz
                            canli_veri = canli_fiyat_cek(mülk['Asset ID'], st.session_state.lofty_api_key)
                            
                            # API'den veri gelip gelmediğine göre kart tasarımı
                            if "error" in canli_veri:
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
            
            with st.expander("API Bağlantı Test Çıktısı (Geliştirici İçin)"):
                st.write("Lofty API'sinden gelen yanıt:")
                # İlk mülkün verisini test amaçlı gösteriyoruz
                st.json(canli_fiyat_cek(df.iloc[0]['Asset ID'], st.session_state.lofty_api_key))

    # --- TAB 2: İSLAMİ UYGUNLUK ANALİZİ ---
    with tab2:
        st.markdown("### 🕌 İslami Finans (Helal Yatırım) Açısından Lofty")
        st.info("""
        **Lofty modeli neden İslam'a uygundur?**
        *   **Reel Varlık:** Alım satım yaptığınız şey sanal bir balon değil, tapusu olan gerçek bir gayrimenkulün hissesidir.
        *   **Faiz (Riba) Yoktur:** Bankalar gibi faizle borç para vermezsiniz. Doğrudan mülke ortak olursunuz.
        *   **Kira Geliri:** Gayrimenkul kiraya verildiğinde elde edilen gelir, hisseniz oranında size yansır.
        """)
        
        st.markdown("#### Mülk Kira Getirisi Hesaplama")
        yatirim = st.number_input("Yatırım Miktarınız ($):", min_value=100, value=1000, step=100)
        tahmini_yillik = yatirim * 0.08
        st.success(f"**${yatirim}** yatırım için tahmini yıllık kira geliri: **${tahmini_yillik:.2f}** (Aylık: **${tahmini_yillik/12:.2f}**)")

    # --- TAB 3: EMİR DEFTERİ (ALICI/SATICI) ---
    with tab3:
        st.markdown("### 🔄 Alıcı ve Satıcı Listesi (Order Book)")
        st.info("Lofty API bağlantısı sağlandığında burada canlı emir defteri görüntülenecektir. Şu an API test aşamasındadır.")
