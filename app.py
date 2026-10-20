import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Gece İşlemi Terminali", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- KURUMSAL CSS TASARIMI ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #1E1E2E;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #3A3A5A;
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value { color: #00FFAA; font-size: 24px; font-weight: bold; }
    .metric-label { color: #A0A0C0; font-size: 14px; }
    .stButton>button { width: 100%; background-color: #4CAF50; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ BİLGİLERİ ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

# --- OTURUM DURUMU ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h2 style='text-align: center;'>🔒 Sisteme Giriş</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        kullanici_adi = st.text_input("Kullanıcı Adı").strip()
        sifre = st.text_input("Şifre", type="password").strip()
        if st.button("Terminale Bağlan"):
            if kullanici_adi == DOGRU_KULLANICI and sifre == DOGRU_SIFRE:
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")

# --- TERMİNAL EKRANI ---
else:
    st.sidebar.success(f"Hoş geldin, {DOGRU_KULLANICI}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("Sistem Ayarları")
    period = st.sidebar.selectbox("Analiz Periyodu (Geçmiş Veri)", ["6mo", "1y", "2y", "5y"], index=1)
    
    st.title("📈 Kurumsal Gece İşlemi (Overnight Gap) Terminali")
    st.markdown("Bu sistem, hisselerin **kapanıştan bir sonraki günün açılışına** kadar olan fiyat boşluklarını (gap) istatistiksel ve kantitatif yöntemlerle analiz eder.")

    varsayilan_hisseler = "AAPL, MSFT, TSLA, NVDA, AMZN, GOOGL"
    hisse_input = st.text_input("Analiz edilecek hisseleri virgülle ayırarak girin:", varsayilan_hisseler)
    hisseler = [h.strip().upper() for h in hisse_input.split(",") if h.strip()]

    if st.button("Kantitatif Analizi Başlat"):
        if not hisseler:
            st.warning("Lütfen en az bir hisse kodu girin.")
        else:
            sonuclar = []
            all_gap_data = pd.DataFrame()
            
            with st.spinner("Veriler Yahoo Finance üzerinden çekiliyor ve matematiksel modeller uygulanıyor..."):
                for hisse in hisseler:
                    try:
                        ticker = yf.Ticker(hisse)
                        df = ticker.history(period=period)
                        
                        if len(df) > 5:
                            # Gece Getirisi Formülü: (Bugünün Açılışı / Dünün Kapanışı) - 1
                            df['Onceki_Kapanis'] = df['Close'].shift(1)
                            df['Gece_Getirisi_%'] = ((df['Open'] / df['Onceki_Kapanis']) - 1) * 100
                            
                            gecerli_veri = df.dropna().copy()
                            
                            if len(gecerli_veri) > 0:
                                # 1. TEMEL METRİKLER
                                ort_getiri = gecerli_veri['Gece_Getirisi_%'].mean()
                                medyan_getiri = gecerli_veri['Gece_Getirisi_%'].median()
                                std_sapma = gecerli_veri['Gece_Getirisi_%'].std() # Risk Ölçüsü (Volatilite)
                                pozitif_oran = (gecerli_veri['Gece_Getirisi_%'] > 0).mean() * 100
                                
                                # 2. KANTİTATİF METRİKLER
                                kazananlar = gecerli_veri[gecerli_veri['Gece_Getirisi_%'] > 0]['Gece_Getirisi_%']
                                kaybedenler = gecerli_veri[gecerli_veri['Gece_Getirisi_%'] <= 0]['Gece_Getirisi_%']
                                
                                ort_kazanc = kazananlar.mean() if len(kazananlar) > 0 else 0
                                ort_kayip = abs(kaybedenler.mean()) if len(kaybedenler) > 0 else 0
                                
                                # Beklenen Getiri (Expectancy) = (Kazanma Oranı * Ort Kazanç) - (Kaybetme Oranı * Ort Kayıp)
                                kazanma_orani = pozitif_oran / 100
                                kaybetme_orani = 1 - kazanma_orani
                                beklenen_getiri = (kazanma_orani * ort_kazanc) - (kaybetme_orani * ort_kayip)
                                
                                # Risk/Ödül Oranı
                                risk_odul = ort_kazanc / ort_kayip if ort_kayip > 0 else 0
                                
                                # Maksimum Düşüş (Max Drawdown on Gaps)
                                kumulatif = (1 + gecerli_veri['Gece_Getirisi_%']/100).cumprod()
                                max_dd = ((kumulatif / kumulatif.cummax()) - 1).min() * 100
                                
                                sonuclar.append({
                                    "Hisse": hisse,
                                    "İşlem Günü": len(gecerli_veri),
                                    "Pozitif Açılış (%)": round(pozitif_oran, 2),
                                    "Ort. Kazanç (%)": round(ort_kazanc, 3),
                                    "Ort. Kayıp (%)": round(ort_kayip, 3),
                                    "Beklenen Getiri (%)": round(beklenen_getiri, 4),
                                    "Volatilite (Std Sapma)": round(std_sapma, 3),
                                    "Max Düşüş (%)": round(max_dd, 2)
                                })
                                
                                # Grafik için veriyi sakla
                                gecerli_veri['Hisse'] = hisse
                                all_gap_data = pd.concat([all_gap_data, gecerli_veri[['Hisse', 'Gece_Getirisi_%']]])
                                
                    except Exception as e:
                        st.error(f"{hisse} verisi çekilemedi: {e}")
                        
            if sonuclar:
                df_sonuc = pd.DataFrame(sonuclar)
                # Beklenen Getiriye göre sırala (En yüksekten en düşüğe)
                df_sonuc = df_sonuc.sort_values(by="Beklenen Getiri (%)", ascending=False).reset_index(drop=True)
                
                st.success("Kantitatif Analiz Tamamlandı!")
                
                # --- SEKMELER ---
                tab1, tab2, tab3 = st.tabs(["📊 İstatistiksel Özet", "💰 1000$ Simülasyonu", "📉 Görsel Analiz"])
                
                with tab1:
                    st.markdown("### 📊 Kantitatif Analiz Sonuçları")
                    # Tabloyu daha şık göstermek için index'i gizle
                    st.dataframe(
                        df_sonuc,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Hisse": st.column_config.TextColumn("Hisse Kodu", width="medium"),
                            "Beklenen Getiri (%)": st.column_config.NumberColumn("Beklenen Getiri", format="%.4f %%"),
                        }
                    )
                    
                    st.info("""
                    **Metrikler Ne Anlama Geliyor?**
                    *   **Beklenen Getiri (Expectancy):** En önemli metriktir. Sıfırdan büyükse, bu strateji uzun vadede kârlıdır. (Örn: 0.02 ise, her işlemde ortalama %0.02 kazanırsınız).
                    *   **Volatilite:** Risk göstergesidir. Düşük olması, sabah açılışların daha stabil olduğunu gösterir.
                    *   **Pozitif Açılış:** Yüzdesel olarak kaç günün kârlı açıldığıdır. %55 üzeri iyidir.
                    """)

                with tab2:
                    st.markdown("### 💰 Bileşik Getiri Simülasyonu (Sadece Gece İşlemleri)")
                    st.markdown("Diyelim ki bu hisseye **1000$** yatırdınız ve her akşam kapanışta alıp, her sabah açılışta sattınız. Paranız ne olurdu?")
                    
                    secilen_hisse_sim = st.selectbox("Simüle edilecek hisse:", df_sonuc['Hisse'].tolist())
                    
                    hisse_verisi = all_gap_data[all_gap_data['Hisse'] == secilen_hisse_sim].copy()
                    
                    baslangic_sermaye = st.number_input("Başlangıç Sermayesi ($):", min_value=100, value=1000, step=100)
                    
                    # Bileşik getiri hesabı
                    hisse_verisi['Sermaye'] = baslangic_sermaye * (1 + hisse_verisi['Gece_Getirisi_%']/100).cumprod()
                    son_sermaye = hisse_verisi['Sermaye'].iloc[-1]
                    toplam_getiri = ((son_sermaye / baslangic_sermaye) - 1) * 100
                    
                    col_s1, col_s2, col_s3 = st.columns(3)
                    col_s1.markdown(f"<div class='metric-card'><div class='metric-label'>Başlangıç</div><div class='metric-value'>${baslangic_sermaye}</div></div>", unsafe_allow_html=True)
                    col_s2.markdown(f"<div class='metric-card'><div class='metric-label'>Bitiş</div><div class='metric-value' style='color: #FFD700;'>${son_sermaye:.2f}</div></div>", unsafe_allow_html=True)
                    col_s3.markdown(f"<div class='metric-card'><div class='metric-label'>Net Kâr/Zarar</div><div class='metric-value' style='color: {'#00FFAA' if toplam_getiri > 0 else '#FF5555'};'>{toplam_getiri:.2f}%</div></div>", unsafe_allow_html=True)
                    
                    # Simülasyon Grafiği
                    fig_sim = px.line(hisse_verisi, y='Sermaye', title=f"{secilen_hisse_sim} - Sermaye Büyümesi (Sadece Gece İşlemleri)", labels={'Sermaye': 'Bakiye ($)', 'index': 'İşlem Günü'})
                    fig_sim.update_traces(line_color='#00FFAA')
                    st.plotly_chart(fig_sim, use_container_width=True)

                with tab3:
                    st.markdown("### 📉 Gece Getirilerinin Dağılımı")
                    secilen_hisse_grafik = st.selectbox("Grafiği görmek istediğiniz hisse:", df_sonuc['Hisse'].tolist(), key="grafik_sec")
                    
                    hisse_verisi_grafik = all_gap_data[all_gap_data['Hisse'] == secilen_hisse_grafik]
                    
                    fig_hist = px.histogram(
                        hisse_verisi_grafik, 
                        x='Gece_Getirisi_%', 
                        nbins=50, 
                        title=f"{secilen_hisse_grafik} - Gece Getirisi Dağılımı (Histogram)",
                        labels={'Gece_Getirisi_%': 'Gece Getirisi (%)', 'count': 'Gün Sayısı'},
                        color_discrete_sequence=['#4CAF50']
                    )
                    # Sıfır çizgisi ekle
                    fig_hist.add_vline(x=0, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    st.info("Histogramdaki yeşil çubukların sağa doğru (pozitif) kayması, o hissenin geceleri yükselme eğiliminde olduğunu gösterir.")
            else:
                st.error("Hiçbir hisse için geçerli veri bulunamadı.")
