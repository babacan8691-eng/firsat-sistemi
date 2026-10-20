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
    .mulk-baslik { color: #FFFFFF; font-size: 20px; font-weight: bold; margin-bottom: 5px; }
    .mulk-detay { color: #A0A0C0; font-size: 14px; margin-bottom: 5px; }
    .helal-uygun { color: #4CAF50; font-weight: bold; margin-bottom: 10px; }
    .sinyal-iyi { color: #00FF00; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(0,255,0,0.1); }
    .sinyal-orta { color: #FFD700; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(255,215,0,0.1); }
    .sinyal-kotu { color: #FF5555; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(255,85,85,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ BİLGİLERİ ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

# --- OTURUM DURUMU ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "secili_mulk" not in st.session_state:
    st.session_state.secili_mulk = None

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
    
    if st.session_state.secili_mulk is not None:
        if st.sidebar.button("⬅️ Panele Geri Dön"):
            st.session_state.secili_mulk = None
            st.rerun()
            
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

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

    def yatirim_sinyali(arz):
        if arz >= 2500:
            return "🟢 Yatırım İçin Uygun", "sinyal-iyi"
        elif arz >= 1500:
            return "🟡 Orta Risk", "sinyal-orta"
        else:
            return "🔴 Riskli (Düşük Likidite)", "sinyal-kotu"

    # --- DETAY SAYFASI ---
    if st.session_state.secili_mulk is not None:
        mülk = st.session_state.secili_mulk
        st.title(f"🔍 Mülk Detayı: {mülk['Mülk Adı']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Asset ID:** {mülk['Asset ID']}")
            st.info(f"**Toplam Arz:** {mülk['Toplam Arz']} Hisse")
            sinyal, renk = yatirim_sinyali(mülk['Toplam Arz'])
            st.markdown(f"**Yatırım Sinyali:** <span class='{renk}'>{sinyal}</span>", unsafe_allow_html=True)
            
            st.markdown("### 💰 Fiyat Hesaplama")
            # Manuel Fiyat Girişi
            manuel_fiyat = st.number_input("Lofty'den baktığınız anlık hisse fiyatını girin ($):", min_value=1.0, value=50.0, step=1.0)
            
            # Kira Getirisi Hesaplama (Yıllık %8 varsayımı ile)
            tahmini_yillik_getiri = manuel_fiyat * 0.08
            st.success(f"Girdiğiniz fiyata göre tahmini yıllık hisse başı kira geliri: **${tahmini_yillik_getiri:.2f}**")

        with col2:
            st.warning("⚠️ **Bilgilendirme:** Lofty API'si ve web sitesi, dışarıdan (Python üzerinden) otomatik veri çekilmesini engellediği için (403/404 Hataları) anlık fiyatlar otomatik alınamamaktadır. Lütfen Lofty uygulamanızdan baktığınız güncel fiyatı sol taraftaki kutuya manuel olarak giriniz.")
            
        st.markdown("---")
        st.subheader("📜 Son Blokzincir İşlemleri (Algorand)")
        try:
            url = f"https://mainnet-idx.algonode.cloud/v2/assets/{mülk['Asset ID']}/transactions?limit=5"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                txs = res.json().get("transactions", [])
                if txs:
                    for tx in txs:
                        from datetime import datetime
                        zaman_str = datetime.fromtimestamp(tx.get("round-time")).strftime('%Y-%m-%d %H:%M:%S') if tx.get("round-time") else "Bilinmiyor"
                        st.text(f"İşlem ID: {tx.get('id')} | Zaman: {zaman_str}")
                else:
                    st.info("Bu mülke ait son işlem bulunamadı.")
        except Exception as e:
            st.error(f"İşlemler yüklenirken hata: {e}")

    # --- ANA SAYFA ---
    else:
        st.title("🏢 Lofty Gayrimenkul Yatırım Paneli")
        
        df = mülk_listesini_cek()
        
        if not df.empty:
            st.markdown("### 📊 Sistem Metrikleri")
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Mülk Sayısı", f"{len(df)} Adet")
            m2.metric("Sistemdeki Toplam Hisse", f"{df['Toplam Arz'].sum():,}")
            m3.metric("Ortalama Hisse Arzı", f"{int(df['Toplam Arz'].mean())}")
            
            st.markdown("---")
            
            tab1, tab2 = st.tabs(["🏠 Pazar Yeri (Kartlar)", "📋 Tüm Liste (Tablo)"])

            with tab1:
                st.markdown("### Blokzincirden Çekilen Güncel Mülkler")
                gosterilecek_adet = st.slider("Kaç mülk gösterilsin?", min_value=3, max_value=100, value=12, step=3)
                
                if st.button("Verileri Yenile"):
                    st.cache_data.clear()
                    st.rerun()
                    
                gosterilecek_mulkler = df.head(gosterilecek_adet)
                
                for i in range(0, len(gosterilecek_mulkler), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(gosterilecek_mulkler):
                            mülk = gosterilecek_mulkler.iloc[i + j]
                            with cols[j]:
                                sinyal, renk = yatirim_sinyali(mülk['Toplam Arz'])
                                
                                st.markdown(f"""
                                    <div class="mulk-karti">
                                        <div class="mulk-baslik">{mülk['Mülk Adı']}</div>
                                        <div class="mulk-detay">Asset ID: {mülk['Asset ID']}</div>
                                        <div class="mulk-detay">Toplam Hisse: {mülk['Toplam Arz']}</div>
                                        <hr style="border-color: #3A3A5A;">
                                        <div class="helal-uygun">✅ Reel Varlık (Helal)</div>
                                        <div class="{renk}">{sinyal}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                if st.button(f"İncele", key=f"btn_{mülk['Asset ID']}"):
                                    st.session_state.secili_mulk = mülk
                                    st.rerun()

            with tab2:
                st.markdown("### 📋 Tüm Mülklerin Tablosu")
                st.dataframe(df, use_container_width=True, height=600)
        else:
            st.error("Sistem Algorand ağına bağlanamadı.")
