import streamlit as st
import requests
import pandas as pd

# --- GÜVENLİK AYARLARI ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

st.set_page_config(page_title="Lofty Yatırım Paneli", page_icon="🏢", layout="wide")

# CSS ile tasarımı güzelleştirelim
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
    
    # Sekmeler oluşturalım
    tab1, tab2, tab3 = st.tabs(["🏠 Pazar Yeri (Kart Görünümü)", "📊 İslami Uygunluk Analizi", "🔄 Alım-Satım (Emir Defteri)"])

    # Veri çekme fonksiyonu
    @st.cache_data(ttl=300) # 5 dakika önbellekle
    def verileri_cek():
        lofty_listesi = []
        try:
            url = "https://mainnet-idx.algonode.cloud/v2/assets"
            params = {"name": "Lofty", "limit": 1000}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for asset in data.get("assets", []):
                    params_data = asset.get("params", {})
                    mülk_adi = str(params_data.get("name", ""))
                    if "lofty" in mülk_adi.lower() and "AI" not in mülk_adi: # "Lofty AI" token'ını filtrele
                        lofty_listesi.append({
                            "Asset ID": asset.get("index"),
                            "Mülk Adı": mülk_adi,
                            "Toplam Arz": params_data.get("total", 0),
                        })
        except:
            pass
        return pd.DataFrame(lofty_listesi)

    # --- TAB 1: PAZAR YERİ (KARTLAR) ---
    with tab1:
        st.markdown("### Blokzincirden Çekilen Güncel Mülkler")
        if st.button("Verileri Yenile"):
            st.cache_data.clear()
            
        df = verileri_cek()
        
        if df.empty:
            st.warning("Henüz veri çekilmedi. Lütfen 'Verileri Yenile' butonuna basın.")
        else:
            # İlk 12 mülkü kart olarak gösterelim
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
        tahmini_yillik = yatirim * 0.08 # Ortalama %8 varsayımı
        st.success(f"**${yatirim}** yatırım için tahmini yıllık kira geliri: **${tahmini_yillik:.2f}** (Aylık: **${tahmini_yillik/12:.2f}**)")

    # --- TAB 3: EMİR DEFTERİ (ALICI/SATICI) ---
    with tab3:
        st.markdown("### 🔄 Alıcı ve Satıcı Listesi (Order Book)")
        st.warning("""
        **Bilgilendirme:**
        Blokzincir ağları (Algorand) sadece **geçmişte gerçekleşmiş** işlemleri kaydeder. 
        "Şu an kim satıyor, kim almak istiyor" gibi anlık emir listeleri (Order Book) Lofty'nin kendi merkezi sunucusunda tutulur. 
        
        Şu an Lofty'nin API'si bize kapalı olduğu için (403 Hatası) anlık alıcı/satıcı listesini çekemiyoruz. Ancak API erişimi açıldığında bu sekmede canlı emir defterini görebileceksiniz.
        """)
