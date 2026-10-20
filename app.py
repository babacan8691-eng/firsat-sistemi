import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pro Kuantum Borsa Terminali", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- KURUMSAL CSS TASARIMI (Karanlık Tema) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .metric-card {
        background: linear-gradient(145deg, #1E1E2E, #151520);
        padding: 15px; border-radius: 10px; border: 1px solid #3A3A5A;
        text-align: center; box-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }
    .metric-value { color: #00FFAA; font-size: 26px; font-weight: bold; }
    .metric-label { color: #A0A0C0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;}
    .signal-buy { background-color: #008000; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    .signal-hold { background-color: #FFA500; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    .signal-sell { background-color: #FF0000; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    .halal-yes { color: #00FF00; font-weight: bold; }
    .halal-no { color: #FF0000; font-weight: bold; }
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
    st.markdown("<h2 style='text-align: center;'>🔒 Kuantum Terminale Giriş</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        kullanici_adi = st.text_input("Kullanıcı Adı").strip()
        sifre = st.text_input("Şifre", type="password").strip()
        if st.button("Sisteme Bağlan", use_container_width=True):
            if kullanici_adi == DOGRU_KULLANICI and sifre == DOGRU_SIFRE:
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Erişim Reddedildi. Bilgileri kontrol edin.")

# --- TERMİNAL EKRANI ---
else:
    # Yan Menü
    st.sidebar.markdown(f"### Hoş geldin,\n**{DOGRU_KULLANICI}**")
    st.sidebar.markdown(f"Son Güncelleme: `{datetime.now().strftime('%H:%M:%S')}`")
    if st.sidebar.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Analiz Ayarları")
    period = st.sidebar.selectbox("Geçmiş Veri Periyodu", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()
        
    st.title("⚡ Pro Kuantum Borsa Terminali")
    st.markdown("Bu sistem; **gece işlemleri (overnight)**, **döngüsel (mean-reversion) hareketler**, **İslami filtreler** ve **kantitatif metrikleri** harmanlar.")

    varsayilan_hisseler = "AAPL, MSFT, TSLA, NVDA, AMZN, GOOGL, JPM, KO"
    hisse_input = st.text_input("Analiz edilecek hisseleri virgülle ayırarak girin:", varsayilan_hisseler)
    hisseler = [h.strip().upper() for h in hisse_input.split(",") if h.strip()]

    @st.cache_data(ttl=60) # Her 60 saniyede bir otomatik güncelle
    def veri_analiz_et(hisse, period):
        try:
            ticker = yf.Ticker(hisse)
            info = ticker.info
            df = ticker.history(period=period)
            
            if len(df) < 5: return None
            
            # 1. GECE GETİRİSİ (Overnight Gap)
            df['Onceki_Kapanis'] = df['Close'].shift(1)
            df['Gece_Getirisi'] = ((df['Open'] / df['Onceki_Kapanis']) - 1) * 100
            gecerli = df.dropna().copy()
            
            if len(gecerli) == 0: return None
            
            # 2. TEMEL METRİKLER
            ort_getiri = gecerli['Gece_Getirisi'].mean()
            std_sapma = gecerli['Gece_Getirisi'].std()
            pozitif_oran = (gecerli['Gece_Getirisi'] > 0).mean() * 100
            
            kazananlar = gecerli[gecerli['Gece_Getirisi'] > 0]['Gece_Getirisi']
            kaybedenler = gecerli[gecerli['Gece_Getirisi'] <= 0]['Gece_Getirisi']
            ort_kazanc = kazananlar.mean() if len(kazananlar) > 0 else 0
            ort_kayip = abs(kaybedenler.mean()) if len(kaybedenler) > 0 else 0
            
            # Beklenen Getiri (Expectancy)
            kazanma_orani = pozitif_oran / 100
            beklenen_getiri = (kazanma_orani * ort_kazanc) - ((1 - kazanma_orani) * ort_kayip)
            
            # 3. DÖNGÜ ANALİZİ (MEAN REVERSION)
            # "Dün düştüyse bugün yükselir" mantığı
            dun_dusenler = gecerli['Gece_Getirisi'].shift(1) < 0
            bugun_yukselenler = gecerli['Gece_Getirisi'] > 0
            dongu_skoru = (bugun_yukselenler[dun_dusenler]).mean() * 100 if dun_dusenler.sum() > 0 else 0
            
            # 4. İSLAMİ UYGUNLUK (Sektör Filtresi)
            sektor = str(info.get('sector', '')).lower()
            industry = str(info.get('industry', '')).lower()
            haram_sektorler = ['financial services', 'banks', 'alcohol', 'tobacco', 'gambling', 'defense', 'aerospace']
            
            is_halal = True
            if any(h in sektor for h in haram_sektorler) or any(h in industry for h in haram_sektorler):
                is_halal = False
            
            # 5. SİNYAL ÜRETİMİ
            # Beklenen getiri > 0.10 VE Döngü Skoru > 50 VE Volatilite < 2.5 (Aşırı riskli değilse)
            if beklenen_getiri > 0.1 and dongu_skoru > 50 and std_sapma < 2.5 and is_halal:
                sinyal = "🟢 GÜÇLÜ AL"
                sinyal_renk = "signal-buy"
            elif beklenen_getiri > 0 and is_halal:
                sinyal = "🟡 BEKLE / İZLE"
                sinyal_renk = "signal-hold"
            else:
                sinyal = "🔴 RİSKLİ / ALMA"
                sinyal_renk = "signal-sell"

            return {
                "Hisse": hisse,
                "Şirket": info.get('shortName', hisse)[:15],
                "Beklenen Getiri (%)": round(beklenen_getiri, 4),
                "Pozitif Açılış (%)": round(pozitif_oran, 2),
                "Döngü Skoru (%)": round(dongu_skoru, 2),
                "Volatilite": round(std_sapma, 3),
                "Sinyal": sinyal,
                "Sinyal_Renk": sinyal_renk,
                "Helal": is_halal,
                "Sektor": sektor.title(),
                "Veri": gecerli
            }
        except Exception as e:
            return None

    if st.button("🚀 Piyasayı Tara ve Analiz Et", use_container_width=True):
        if not hisseler:
            st.warning("Lütfen hisse kodu girin.")
        else:
            sonuclar = []
            all_data = []
            
            with st.spinner("Gerçek piyasa verileri çekiliyor, algoritmalar çalıştırılıyor..."):
                for hisse in hisseler:
                    res = veri_analiz_et(hisse, period)
                    if res:
                        df_veri = res.pop("Veri")
                        df_veri['Hisse'] = hisse
                        all_data.append(df_veri)
                        sonuclar.append(res)
            
            if sonuclar:
                df_final = pd.DataFrame(sonuclar)
                df_final = df_final.sort_values(by="Beklenen Getiri (%)", ascending=False).reset_index(drop=True)
                df_all_data = pd.concat(all_data)
                
                st.success(f"Tarama Tamamlandı! {len(df_final)} hisse analiz edildi.")
                
                # --- SEKMELER ---
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Piyasa Tarayıcı", "🔍 Detaylı Hisse Kartı", "📈 Döngü ve Dağılım", "ℹ️ Sistem Nasıl Çalışır?"])
                
                # --- TAB 1: TARAYICI TABLOSU ---
                with tab1:
                    st.markdown("### 📊 Kantitatif Piyasa Tarayıcı")
                    # Tabloyu görsel olarak zenginleştirme
                    st.dataframe(
                        df_final[["Hisse", "Şirket", "Beklenen Getiri (%)", "Döngü Skoru (%)", "Pozitif Açılış (%)", "Volatilite", "Sinyal"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Hisse": st.column_config.TextColumn("Hisse", width="small"),
                            "Beklenen Getiri (%)": st.column_config.NumberColumn("Beklenen Getiri", format="%.3f %%"),
                            "Döngü Skoru (%)": st.column_config.ProgressColumn("Döngü Skoru", min_value=0, max_value=100, format="%.1f %%"),
                        }
                    )
                    
                # --- TAB 2: DETAYLI KART ---
                with tab2:
                    secilen_hisse = st.selectbox("Detaylarını görmek istediğiniz hisseyi seçin:", df_final['Hisse'].tolist())
                    secili_veri = df_final[df_final['Hisse'] == secilen_hisse].iloc[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Beklenen Getiri", f"% {secili_veri['Beklenen Getiri (%)']}")
                    col2.metric("Döngü (Bounce) Skoru", f"% {secili_veri['Döngü Skoru (%)']}")
                    col3.metric("Pozitif Açılış Oranı", f"% {secili_veri['Pozitif Açılış (%)']}")
                    col4.metric("Volatilite (Risk)", secili_veri['Volatilite'])
                    
                    st.markdown("---")
                    c_left, c_right = st.columns(2)
                    
                    with c_left:
                        st.subheader("🏢 Şirket ve İslami Filtre")
                        st.write(f"**Sektör:** {secili_veri['Sektor']}")
                        if secili_veri['Helal']:
                            st.markdown("Durum: <span class='halal-yes'>✅ İslami Açıdan Uygun (Sektör Filtresi)</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("Durum: <span class='halal-no'>❌ İslami Açıdan Şüpheli (Faiz, Alkol, Kumar vb.)</span>", unsafe_allow_html=True)
                            st.caption("Not: Bu otomatik bir sektör filtresidir. Kesin hüküm için finansal tablolara (borç/faiz oranı) bakılmalıdır.")
                            
                    with c_right:
                        st.subheader("⚖️ Yatırım Kararı")
                        st.markdown(f"<h3><span class='{secili_veri['Sinyal_Renk']}'>{secili_veri['Sinyal']}</span></h3>", unsafe_allow_html=True)
                        if "GÜÇLÜ" in secili_veri['Sinyal']:
                            st.write("Sistem, bu hissede gece işlemlerinin (akşam al, sabah sat) uzun vadede kârlı olduğunu ve düşüş sonrası toparlanma (döngü) ihtimalinin yüksek olduğunu öngörüyor.")
                        elif "BEKLE" in secili_veri['Sinyal']:
                            st.write("Getiri potansiyeli var ancak çok güçlü değil. Daha iyi fırsatlar beklenebilir.")
                        else:
                            st.write("Sistem bu hissede gece işlemi yapılmasını önermiyor. Getiri beklentisi negatif veya risk çok yüksek.")

                # --- TAB 3: GRAFİKLER ---
                with tab3:
                    secilen_grafik_hisse = st.selectbox("Grafiği çizilecek hisse:", df_final['Hisse'].tolist(), key="grafik_hisse")
                    hisse_gecmis = df_all_data[df_all_data['Hisse'] == secilen_grafik_hisse]
                    
                    # 1. Kümülatif Getiri Grafiği (1000$ Simülasyonu)
                    hisse_gecmis = hisse_gecmis.copy()
                    hisse_gecmis['Sermaye'] = 1000 * (1 + hisse_gecmis['Gece_Getirisi']/100).cumprod()
                    
                    fig_line = px.line(hisse_gecmis, y='Sermaye', title=f"{secilen_grafik_hisse} - 1000$ Sermaye Simülasyonu (Sadece Gece İşlemleri)",
                                       labels={'Sermaye': 'Bakiye ($)', 'Date': 'Tarih'})
                    fig_line.update_traces(line_color='#00FFAA', line_width=3)
                    fig_line.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                    # 2. Dağılım (Histogram)
                    fig_hist = px.histogram(hisse_gecmis, x='Gece_Getirisi', nbins=50, title=f"{secilen_grafik_hisse} - Gece Getirisi Dağılımı",
                                            color_discrete_sequence=['#FFA500'])
                    fig_hist.add_vline(x=0, line_dash="dash", line_color="red")
                    fig_hist.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_hist, use_container_width=True)

                # --- TAB 4: YARDIM ---
                with tab4:
                    st.markdown("""
                    ### 🧠 Sistem Mantığı ve Döngü Analizi
                    
                    **1. Döngü Skoru (Mean Reversion) Nedir?**
                    Sizin de belirttiğiniz gibi borsalarda bir "sarkaç" etkisi vardır. Bir gün sert düşen bir hisse, ertesi gün tepki olarak yükselebilir. 
                    Sistemimiz şu soruyu sorar: *"Bu hisse geçmişte, bir önceki gece düştüğünde, ertesi gece yükselme (veya tam tersi) ihtimali yüzde kaçtı?"*
                    Döngü skoru %60'ın üzerindeyse, hissenin "yay gibi" geri tepme potansiyeli yüksektir.
                    
                    **2. Beklenen Getiri (Expectancy)**
                    Sadece "kaç kere kazandım" değil, "kazandığımda ne kadar, kaybettiğimde ne kadar kaybediyorum" mantığıdır. 
                    Formül: `(Kazanma Oranı x Ortalama Kazanç) - (Kaybetme Oranı x Ortalama Kayıp)`
                    Eğer sonuç **artı** ise, bu strateji matematiksel olarak kârlıdır.
                    
                    **3. İslami Uygunluk**
                    Sistem, Yahoo Finance verilerini kullanarak şirketin ana faaliyet alanını (Sektör) kontrol eder. Faiz (Bankacılık), Alkol, Tütün, Kumar gibi sektörlerdeyse "Şüpheli" olarak işaretler. (Yatırım yapmadan önce güncel helal hisse listelerini kontrol etmeniz tavsiye edilir).
                    """)
            else:
                st.error("Analiz edilecek hisse bulunamadı veya veriler eksik.")
