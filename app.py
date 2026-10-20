import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quantum Alpha Terminali", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- KURUMSAL CSS TASARIMI ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .alpha-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #3b82f6;
        margin-bottom: 25px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
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
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ BİLGİLERİ ---
DOGRU_KULLANICI = "Cuma Babacan"
DOGRU_SIFRE = "784512"

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 Quantum Alpha Terminali</h2>", unsafe_allow_html=True)
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
    # 100 Milyar Dolar Üzeri Dev Şirketler (S&P 100 - Yüksek Hacimli)
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

    st.sidebar.markdown(f"### 👤 {DOGRU_KULLANICI}")
    st.sidebar.markdown(f"🕒 `{datetime.now().strftime('%H:%M:%S')}`")
    if st.sidebar.button("🔄 Sistemi ve Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    period = st.sidebar.selectbox("Analiz Periyodu", ["1mo", "3mo", "6mo", "1y"], index=3)
    
    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

    st.title("⚡ Quantum Alpha Terminali (Mega-Cap Tarayıcı)")
    st.markdown("Sistem; **İstatistiksel Olasılık, Döngü (Mean Reversion), Kelly Kriteri ve Z-Skoru** kullanarak piyasa değeri 100 Milyar $ üzerindeki 100 dev hisseyi tarar. Klişe indikatör içermez.")

    # --- ANALİZ FONKSİYONU (KANTİTATİF MATEMATİK) ---
    @st.cache_data(ttl=3600, show_spinner=False) 
    def kuantum_analiz(ticker_symbol, period):
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            df = ticker.history(period=period)
            
            if len(df) < 20: return None
            
            # 1. Gece Getirisi (Overnight Gap)
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
            
            # 3. Beklenen Getiri (Expectancy) ve Kelly Kriteri
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            kelly = win_rate - ((1 - win_rate) / win_loss_ratio) if win_loss_ratio > 0 else 0
            
            # 4. Döngü Analizi (Mean Reversion): Dün düştüyse bugün yükselme olasılığı
            prev_down = df['Gap'].shift(1) < 0
            curr_up = df['Gap'] > 0
            cycle_prob = curr_up[prev_down].mean() * 100 if prev_down.sum() > 0 else 0
            
            # 5. Z-Skoru (Aşırı Sapma): Son günün gap'i ortalamadan ne kadar saptı?
            last_gap = df['Gap'].iloc[-1]
            z_score = (last_gap - mean_gap) / std_gap if std_gap > 0 else 0

            # 6. İslami Filtre (Sektör)
            sektor = str(info.get('sector', '')).lower()
            haram = ['financial services', 'banks', 'alcohol', 'tobacco', 'gambling', 'defense', 'aerospace']
            is_halal = not (any(h in sektor for h in haram))
            
            # 7. Sinyal Üretimi
            if expectancy > 0.05 and cycle_prob > 55 and is_halal:
                signal, s_color = "🟢 GÜÇLÜ AL", "signal-buy"
            elif expectancy > 0 and is_halal:
                signal, s_color = "🟡 İZLE", "signal-hold"
            else:
                signal, s_color = "🔴 RİSKLİ", "signal-sell"

            return {
                "Hisse": ticker_symbol,
                "Şirket": info.get('shortName', ticker_symbol)[:15],
                "Beklenen Getiri (%)": round(expectancy, 3),
                "Döngü Olasılığı (%)": round(cycle_prob, 1),
                "Kelly Oranı": round(kelly, 3),
                "Son Gece Gap (%)": round(last_gap, 2),
                "Z-Skoru": round(z_score, 2),
                "Sinyal": signal,
                "Sinyal_Renk": s_color,
                "Helal": is_halal,
                "Sektor": sektor.title(),
                "Grafik_Verisi": df
            }
        except:
            return None

    # --- TARAMA BAŞLATICI ---
    if st.button("🚀 100 Dev Hissede Kuantum Taraması Başlat", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        # Aynı anda çok istek atmamak için yavaş yavaş tarıyoruz
        for i, ticker in enumerate(MEGA_CAP_TICKERS):
            status_text.text(f"Taranıyor: {ticker} ({i+1}/{len(MEGA_CAP_TICKERS)})")
            res = kuantum_analiz(ticker, period)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(MEGA_CAP_TICKERS))
            
        status_text.text("Tarama Tamamlandı!")
        progress_bar.empty()
        
        if results:
            df_final = pd.DataFrame(results)
            # En yüksek Beklenen Getiriye göre sırala
            df_final = df_final.sort_values(by="Beklenen Getiri (%)", ascending=False).reset_index(drop=True)
            st.session_state['df_results'] = df_final # Hafızaya al

    # --- SONUÇLARI EKRANA BASMA ---
    if 'df_results' in st.session_state:
        df_final = st.session_state['df_results']
        
        # --- 1. EN ÜSTTEKİ ÖZEL KUTUCUK (TOP PICKS) ---
        top_picks = df_final[(df_final['Sinyal'].str.contains("GÜÇLÜ")) & (df_final['Helal'] == True)].head(3)
        
        if not top_picks.empty:
            st.markdown("<div class='alpha-box'>", unsafe_allow_html=True)
            st.markdown("### 🏆 Sistemin En İyi 3 Yatırım Fırsatı (Helal & Yüksek Olasılık)")
            st.markdown("Bu hisseler, matematiksel modellerimizin (Beklenen Getiri + Döngü + Kelly) en yüksek skor verdiği varlıklardır.")
            
            cols = st.columns(3)
            for idx, (_, row) in enumerate(top_picks.iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                        <div class='metric-card'>
                            <h2 style='color: #60a5fa; margin: 0;'>{row['Hisse']}</h2>
                            <p style='color: #9ca3af; margin: 5px 0;'>{row['Şirket']}</p>
                            <hr style='border-color: #374151;'>
                            <div class='metric-value'>%{row['Beklenen Getiri (%)']}</div>
                            <div class='metric-label'>Beklenen Getiri</div>
                            <p style='color: #10b981; margin-top: 5px;'>Döngü: %{row['Döngü Olasılığı (%)']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Şu anki piyasa koşullarında 'Güçlü Al' sinyali veren ve İslami kurallara tam uygun bir hisse bulunamadı.")

        # --- 2. TÜM PİYASA TABLOSU ---
        st.markdown("### 📊 Tüm Taranan Hisseler (Kantitatif Veriler)")
        st.dataframe(
            df_final[["Hisse", "Şirket", "Beklenen Getiri (%)", "Döngü Olasılığı (%)", "Kelly Oranı", "Z-Skoru", "Sinyal"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Hisse": st.column_config.TextColumn("Hisse", width="small"),
                "Beklenen Getiri (%)": st.column_config.NumberColumn("Beklenen Getiri", format="%.3f %%"),
                "Döngü Olasılığı (%)": st.column_config.ProgressColumn("Döngü (Mean Reversion)", min_value=0, max_value=100, format="%.1f %%"),
                "Kelly Oranı": st.column_config.NumberColumn("Kelly Kriteri", format="%.3f"),
            }
        )
        
        # --- 3. HİSSE DETAY VE GRAFİK ---
        st.markdown("---")
        st.markdown("### 🔍 Derinlemesine İnceleme")
        secilen = st.selectbox("Detaylarını ve grafiğini görmek istediğiniz hisseyi seçin:", df_final['Hisse'].tolist())
        secili_veri = df_final[df_final['Hisse'] == secilen].iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Şirket Sektörü", secili_veri['Sektor'])
        
        if secili_veri['Helal']:
            c2.markdown("**İslami Durum:**<br><span class='halal-yes'>✅ Uygun (Sektör Filtresi)</span>", unsafe_allow_html=True)
        else:
            c2.markdown("**İslami Durum:**<br><span class='halal-no'>❌ Şüpheli (Faiz/Alkol vb.)</span>", unsafe_allow_html=True)
            
        c3.metric("Son Gece Gap", f"%{secili_veri['Son Gece Gap (%)']}")
        c4.metric("Z-Skoru (Sapma)", secili_veri['Z-Skoru'])
        
        # Grafik
        grafik_df = secili_veri['Grafik_Verisi']
        # Kümülatif getiri simülasyonu (Sadece geceleri al-sat)
        grafik_df = grafik_df.copy()
        grafik_df['Kümülatif Getiri'] = (1 + grafik_df['Gap']/100).cumprod()
        
        fig = px.line(grafik_df, y='Kümülatif Getiri', title=f"{secilen} - 1$'lık Yatırımın Sadece Gece İşlemleriyle Büyümesi",
                      labels={'Kümülatif Getiri': 'Bakiye (Kat Sayısı)', 'Date': 'Tarih'})
        fig.update_traces(line_color='#3b82f6', line_width=2)
        fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # --- 4. MATEMATİKSEL AÇIKLAMALAR ---
        with st.expander("🧠 Sistemdeki Matematiksel Modeller Ne Anlama Geliyor? (Klişe Değildir)"):
            st.markdown("""
            *   **Beklenen Getiri (Expectancy):** `(Kazanma Oranı x Ortalama Kazanç) - (Kaybetme Oranı x Ortalama Kayıp)`. Eğer sonuç sıfırdan büyükse, bu strateji (akşam al, sabah sat) uzun vadede matematiksel olarak kârlıdır.
            *   **Döngü Olasılığı (Mean Reversion):** Sizin de belirttiğiniz döngü. *"Bir önceki gece düştüyse, bu gece yükselme ihtimali nedir?"* Yüzde 55 ve üzeri, piyasanın o hissede "yay gibi geri tepme" eğiliminde olduğunu gösterir.
            *   **Kelly Kriteri:** Profesyonel fon yöneticilerinin kullandığı formüldür. *"Bu hisseye portföyümün yüzde kaçını yatırmalıyım?"* sorusunun matematiksel cevabıdır. (Pozitif ve yüksek olması iyidir).
            *   **Z-Skoru:** Son günün fiyat hareketinin, geçmiş ortalamaya göre ne kadar anormal olduğunu gösterir. `-2`'nin altındaysa "aşırı düşmüş, tepki alımı gelebilir" anlamına gelir.
            """)
