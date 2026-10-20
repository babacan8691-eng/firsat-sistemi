import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh # Otomatik yenileme için

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quantum Sniper Terminali", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# --- KURUMSAL CSS TASARIMI ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .alpha-box {
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #10b981;
        margin-bottom: 25px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
    }
    .metric-card {
        background: #111827; padding: 15px; border-radius: 10px; 
        border: 1px solid #374151; text-align: center;
    }
    .metric-value { color: #10b981; font-size: 24px; font-weight: 800; }
    .metric-label { color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;}
    .signal-buy { background-color: #059669; color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
    .signal-hold { background-color: #d97706; color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
    .signal-sell { background-color: #dc2626; color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
    .halal-yes { color: #10b981; font-weight: bold; }
    .halal-no { color: #ef4444; font-weight: bold; }
    .warning-text { color: #f59e0b; font-size: 14px; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ BİLGİLERİ ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 Quantum Sniper Terminali</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        kullanici_adi = st.text_input("Kullanıcı Adı").strip()
        sifre = st.text_input("Şifre", type="password").strip()
        if st.button("Sisteme Bağlan", use_container_width=True):
            if kullanici_adi == DOGRU_KULLANICI and sifre == DOGRU_SIFRE:
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Erişim Reddedildi.")

# --- TERMİNAL EKRANI ---
else:
    # 100 Milyar Dolar Üzeri Dev Şirketler
    MEGA_CAP_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY", "AVGO",
        "JPM", "V", "XOM", "UNH", "MA", "JNJ", "PG", "HD", "COST", "ABBV",
        "MRK", "CVX", "ADBE", "CRM", "PEP", "AMD", "KO", "WMT", "BAC", "MCD",
        "TMO", "CSCO", "ACN", "LIN", "ABT", "ORCL", "DHR", "WFC", "TXN", "PM",
        "INTC", "NEE", "QCOM", "INTU", "IBM", "AMGN", "CAT", "GE", "DIS", "AMAT",
        "NOW", "UNP", "SPGI", "BA", "HON", "COP", "PFE", "UBER", "LOW", "ELV",
        "GS", "BLK", "RTX", "T", "MS", "DE", "BKNG", "TJX", "VRTX", "SYK",
        "MDT", "SCHW", "LMT", "C", "PLD", "MDLZ", "ADI", "REGN", "GILD", "MMC",
        "CVS", "ZTS", "CB", "SO", "DUK", "BDX", "CI", "MO", "PGR", "ETN",
        "BSX", "MU", "PANW", "KLAC", "SNPS", "CDNS", "WM", "ITW", "APH", "EQIX"
    ]

    # --- YAN MENÜ (MALİYET VE OTOMASYON AYARLARI) ---
    st.sidebar.markdown(f"### 👤 {DOGRU_KULLANICI}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Ticaret Ayarları")
    sermaye = st.sidebar.number_input("İşlem Başına Sermaye ($)", min_value=10, value=200, step=50)
    maliyet = st.sidebar.number_input("Toplam İşlem Maliyeti (Komisyon+Makas $)", min_value=0.0, value=5.0, step=0.5)
    
    # Maliyetin yüzdesel karşılığını hesapla (Örn: 200$'da 5$ maliyet = %2.5)
    maliyet_yuzdesi = (maliyet / sermaye) * 100
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Sniper Modu (Filtre)")
    min_getiri_esigi = st.sidebar.slider("Minimum Beklenen Getiri (%)", 0.1, 5.0, 0.5, 0.1)
    min_dongu_skoru = st.sidebar.slider("Minimum Döngü Skoru (%)", 50, 90, 60, 1)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Otomatik Güncelleme")
    auto_refresh = st.sidebar.checkbox("Otomatik Yenilemeyi Aç")
    refresh_mins = st.sidebar.number_input("Kaç dakikada bir yenilensin?", min_value=1, max_value=60, value=15)
    
    if auto_refresh:
        st_autorefresh(interval=refresh_mins * 60 * 1000, key="data_refresh")

    # --- ANALİZ FONKSİYONU (KANTİTATİF MATEMATİK) ---
    @st.cache_data(ttl=3600, show_spinner=False) 
    def kuantum_analiz(ticker_symbol, period):
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            df = ticker.history(period=period)
            
            if len(df) < 20: return None
            
            # 1. Gece Getirisi
            df['Prev_Close'] = df['Close'].shift(1)
            df['Gap'] = ((df['Open'] / df['Prev_Close']) - 1) * 100
            df = df.dropna()
            
            # 2. İstatistiksel Metrikler
            mean_gap = df['Gap'].mean()
            std_gap = df['Gap'].std()
            win_rate = (df['Gap'] > 0).mean()
            
            wins = df[df['Gap'] > 0]['Gap']
            losses = df[df['Gap'] <= 0]['Gap']
            avg_win = wins.mean() if len(wins) > 0 else 0
            avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
            
            # 3. Beklenen Getiri
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            
            # 4. Döngü Analizi
            prev_down = df['Gap'].shift(1) < 0
            curr_up = df['Gap'] > 0
            cycle_prob = curr_up[prev_down].mean() * 100 if prev_down.sum() > 0 else 0
            
            # 5. Z-Skoru
            last_gap = df['Gap'].iloc[-1]
            z_score = (last_gap - mean_gap) / std_gap if std_gap > 0 else 0

            # 6. İslami Filtre
            sektor = str(info.get('sector', '')).lower()
            haram = ['financial services', 'banks', 'alcohol', 'tobacco', 'gambling', 'defense', 'aerospace']
            is_halal = not (any(h in sektor for h in haram))
            
            return {
                "Hisse": ticker_symbol,
                "Şirket": info.get('shortName', ticker_symbol)[:15],
                "Beklenen Getiri (%)": round(expectancy, 3),
                "Döngü Skoru (%)": round(cycle_prob, 1),
                "Z-Skoru": round(z_score, 2),
                "Helal": is_halal,
                "Sektor": sektor.title(),
                "Grafik_Verisi": df
            }
        except:
            return None

    # --- TARAMA BAŞLATICI (OTOMATİK) ---
    st.title("🎯 Quantum Sniper Terminali (Maliyet Odaklı)")
    st.markdown(f"Sistem; **{sermaye}$** sermaye ve **{maliyet}$** maliyet ile çalışacak şekilde kalibre edildi. Sadece net kâr bırakan fırsatlar listelenir.")
    
    if st.button("🚀 Piyasayı Tara (Manuel)", use_container_width=True) or 'df_results' not in st.session_state:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        for i, ticker in enumerate(MEGA_CAP_TICKERS):
            status_text.text(f"Taranıyor: {ticker} ({i+1}/{len(MEGA_CAP_TICKERS)})")
            res = kuantum_analiz(ticker, "1y")
            if res:
                # --- MALİYET HESAPLAMASI ---
                brut_kar_dolares = (res["Beklenen Getiri (%)"] / 100) * sermaye
                net_kar_dolares = brut_kar_dolares - maliyet
                net_getiri_yuzde = (net_kar_dolares / sermaye) * 100
                
                res["Brüt Kâr ($)"] = round(brut_kar_dolares, 2)
                res["Net Kâr ($)"] = round(net_kar_dolares, 2)
                res["Net Getiri (%)"] = round(net_getiri_yuzde, 3)
                
                results.append(res)
            progress_bar.progress((i + 1) / len(MEGA_CAP_TICKERS))
            
        status_text.text("Tarama Tamamlandı!")
        progress_bar.empty()
        
        if results:
            df_final = pd.DataFrame(results)
            df_final = df_final.sort_values(by="Net Getiri (%)", ascending=False).reset_index(drop=True)
            st.session_state['df_results'] = df_final 

    # --- SONUÇLARI EKRANA BASMA ---
    if 'df_results' in st.session_state:
        df_final = st.session_state['df_results']
        
        # --- 1. SNIPER MODU: KUSURSUZ FIRSATLAR KUTUSU ---
        # Filtre: Helal + Net Kâr > 0 + Beklenen Getiri > Eşik + Döngü > Eşik
        sniper_picks = df_final[
            (df_final['Helal'] == True) & 
            (df_final['Net Kâr ($)'] > 0) & 
            (df_final['Beklenen Getiri (%)'] >= min_getiri_esigi) & 
            (df_final['Döngü Skoru (%)'] >= min_dongu_skoru)
        ].head(3)
        
        if not sniper_picks.empty:
            st.markdown("<div class='alpha-box'>", unsafe_allow_html=True)
            st.markdown("### 🏆 Sniper Onaylı Yatırım Fırsatları (Maliyetler Düşülmüş)")
            st.markdown(f"Bu hisseler, {sermaye}$ sermaye ve {maliyet}$ maliyet altında bile **net kâr** bırakan en iyi fırsatlardır.")
            
            cols = st.columns(3)
            for idx, (_, row) in enumerate(sniper_picks.iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                        <div class='metric-card'>
                            <h2 style='color: #60a5fa; margin: 0;'>{row['Hisse']}</h2>
                            <p style='color: #9ca3af; margin: 5px 0;'>{row['Şirket']}</p>
                            <hr style='border-color: #374151;'>
                            <div class='metric-label'>Net Kâr (İşlem Başı)</div>
                            <div class='metric-value'>${row['Net Kâr ($)']}</div>
                            <div class='metric-label'>Net Getiri: %{row['Net Getiri (%)']}</div>
                            <p style='color: #10b981; margin-top: 5px;'>Döngü: %{row['Döngü Skoru (%)']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Sniper modu aktif. {sermaye}$ sermaye ve {maliyet}$ maliyet ile bu filtreleri ({min_getiri_esigi}% Getiri, {min_dongu_skoru}% Döngü) geçen hisse bulunamadı. Yan menüden eşikleri düşürebilirsiniz.")

        # --- 2. TÜM PİYASA TABLOSU (NET KÂR ODAKLI) ---
        st.markdown("### 📊 Tüm Piyasa Verileri (Maliyet Düşülmüş)")
        st.markdown(f"<span class='warning-text'>Kırmızı 'Net Kâr' değerleri, işlem maliyetinin ({maliyet}$) kârdan fazla olduğunu ve o işlemin ZARARLA sonuçlanacağını gösterir.</span>", unsafe_allow_html=True)
        
        # Tabloyu renklendirme fonksiyonu
        def color_net_profit(val):
            color = '#10b981' if val > 0 else '#ef4444'
            return f'color: {color}; font-weight: bold;'

        st.dataframe(
            df_final[["Hisse", "Şirket", "Beklenen Getiri (%)", "Net Kâr ($)", "Net Getiri (%)", "Döngü Skoru (%)", "Z-Skoru"]].style.map(color_net_profit, subset=["Net Kâr ($)", "Net Getiri (%)"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Beklenen Getiri (%)": st.column_config.NumberColumn("Brüt Getiri", format="%.3f %%"),
                "Net Kâr ($)": st.column_config.NumberColumn("Net Kâr (İşlem Başı)", format="$%.2f"),
                "Döngü Skoru (%)": st.column_config.ProgressColumn("Döngü", min_value=0, max_value=100, format="%.1f %%"),
            }
        )
        
        # --- 3. GRAFİK ---
        st.markdown("---")
        secilen = st.selectbox("Grafik İncele:", df_final['Hisse'].tolist())
        secili_veri = df_final[df_final['Hisse'] == secilen].iloc[0]
        
        grafik_df = secili_veri['Grafik_Verisi'].copy()
        grafik_df['Kümülatif Getiri'] = (1 + grafik_df['Gap']/100).cumprod()
        
        fig = px.line(grafik_df, y='Kümülatif Getiri', title=f"{secilen} - Gece İşlemleri Kümülatif Getirisi",
                      labels={'Kümülatif Getiri': 'Bakiye (Kat Sayısı)', 'Date': 'Tarih'})
        fig.update_traces(line_color='#3b82f6', line_width=2)
        fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig, use_container_width=True)
