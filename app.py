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

# --- GÜVENLİK AYARLARI ---
try:
    DOGRU_KULLANICI = st.secrets["KULLANICI_ADI"]
    DOGRU_SIFRE = st.secrets["SIFRE"]
except Exception:
    DOGRU_KULLANICI = "Cuma Babacan"
    DOGRU_SIFRE = "784512"

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
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("🏢 Lofty Gayrimenkul Yatırım Paneli")
    
    tab1, tab2, tab3 = st.tabs(["🏠 Pazar Yeri (Kart Görünümü)", "📊 İslami Uygunluk Analizi", "🔄 Alım-Satım (Emir Defteri)"])

    # --- DÜZELTİLMİŞ VERİ ÇEKME FONKSİYONU ---
    @st.cache_data(ttl=300)
    def verileri_cek():
        lofty_listesi = []
        try:
            url = "https://mainnet-idx.algonode.cloud/v2/assets"
            # API'ye doğrudan "isminde lofty geçenleri ara" komutu veriyoruz
            params = {"name": "lofty", "limit": 1000} 
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                for asset in data.get("assets", []):
                    params_data = asset.get("params", {})
                    mülk_adi = str(params_data.get("name", ""))
                    
                    # Çift kontrol: gelen veride lofty var mı ve AI geçmiyor mu?
                    if "lofty" in mülk_adi.lower() and "ai" not in mülk_adi.lower():
                        lofty_listesi.append({
                            "Asset ID": asset.get("index"),
                            "Mülk Adı": mülk_adi,
                            "Toplam Arz": params_data.get("total", 0),
                        })
            else:
                st.error(f"Algorand ağına bağlanılamadı. Hata Kodu: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Bağlantı hatası oluştu. Lütfen internetinizi kontrol edin. Detay: {e}")
            
        return pd.DataFrame(lofty_listesi)

    # --- TAB 1: PAZAR YERİ (KARTLAR) ---
    with tab1:
        st.markdown("### Blokzincirden Çekilen Güncel Mülkler")
        
        # Sayfa ilk açıldığında veriyi otomatik çekmesi için butonu kaldırıp doğrudan çağırabiliriz
        # veya manuel yenilemek için butonu tutabiliriz. Butonu tutuyoruz.
        if st.button("Verileri Yenile"):
            st.cache_data.clear()
            st.rerun()
            
        df = verileri_cek()
        
        if df.empty:
            st.warning("Algorand ağında 'lofty' isimli token arandı ancak bulunamadı. Lütfen tekrar deneyin.")
        else:
            st.success(f"Blokzincirden toplam {len(df)} adet Lofty mülkü başarıyla çekildi!")
            
            gosterilecek_mulkler = df.head(12)
            
            for i in range(0, len(gosterilecek_mulkler), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(gosterilecek_mulkler):
                        mülk = gosterilecek_mulkler.iloc[i + j]
                        with cols[j]:
                            st.markdown(f"""
                                <div class="mulk-karti">
                                    <div class="mulk-baslik">{mülk['Mülk Adı']}</div>
                                    <div class="mulk-detay">Asset ID: {mülk['Asset ID']}</div>
                                    <div class="mulk-detay">Toplam Hisse: {mülk['Toplam Arz']}</div>
                                    <hr style="border-color: #3A3A5A;">
                                    <div class="helal-uygun">✅ Reel Varlık (Helal)</div>
                                    <div class="mulk-detay">Ortalama Getiri: ~%8 - %10 (Tahmini)</div>
                                </div>
                            """, unsafe_allow_html=True)
            
            with st.expander("Tüm Mülk Listesini Tablo Olarak Gör"):
                st.dataframe(df, use_container_width=True)

    # --- TAB 2: İSLAMİ UYGUNLUK ANALİZİ ---
    with tab2:
        st.markdown("### 🕌 İslami Finans (Helal Yatırım) Açısından Lofty")
        st.info("""
        **Lofty modeli neden İslam'a uygundur?**
        *   **Reel Varlık:** Alım satım yaptığınız şey sanal bir balon değil, tapusu olan gerçek bir gayrimenkulün hissesidir.
        *   **Faiz (Riba) Yoktur:** Bankalar gibi faizle borç para vermezsiniz. Doğrudan mülke ortak olursunuz.
        *   **Kira Geliri:** Gayrimenkul kiraya verildiğinde elde edilen gelir, hisseniz oranında size yansır (Kira geliri İslam'da helaldir).
        *   **Spekülasyon (Garar) Riski:** Blokzincirde anlık alım-satım yapılabildiği için aşırı spekülatif (kumar benzeri) işlemlerden kaçınılmalıdır. Uzun vadeli yatırım tercih edilmelidir.
        
        *Not: Bu bir yatırım tavsiyesi değildir. Dini hükümler için ehil bir fetva makamına danışınız.*
        """)
        
        st.markdown("#### Mülk Kira Getirisi Hesaplama")
        yatirim = st.number_input("Yatırım Miktarınız ($):", min_value=100, value=1000, step=100)
        tahmini_yillik = yatirim * 0.08
        st.success(f"**${yatirim}** yatırım için tahmini yıllık kira geliri: **${tahmini_yillik:.2f}** (Aylık: **${tahmini_yillik/12:.2f}**)")

    # --- TAB 3: EMİR DEFTERİ ---
    with tab3:
        st.markdown("### 🔄 Alıcı ve Satıcı Listesi (Order Book)")
        st.warning("""
        **Bilgilendirme:**
        Blokzincir ağları sadece geçmişte gerçekleşmiş işlemleri kaydeder. 
        Anlık emir listeleri (Order Book) Lofty'nin kendi sunucusunda tutulur. 
        Şu an Lofty'nin API'si bize kapalı olduğu için (403 Hatası) anlık alıcı/satıcı listesini çekemiyoruz. SDK entegrasyonu sağlandığında bu sekmede canlı emir defterini görebileceksiniz.
        """)
