import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Gece İşlemi (Overnight) Tarayıcı", page_icon="🌙", layout="wide")

st.title("🌙 Borsa Gece İşlemi (Overnight Gap) Sinyal Tarayıcı")
st.markdown("""
Bu sistem, belirli hisselerin **kapanış fiyatından bir sonraki günün açılış fiyatına** kadar olan tarihsel getirisini analiz eder. 
*Amacı: Akşam alıp sabah satma stratejisinin geçmişte ne kadar kârlı olduğunu görmek.*
""")

# Kullanıcıdan hisse listesi al
varsayilan_hisseler = "AAPL, MSFT, TSLA, NVDA, AMZN"
hisse_input = st.text_input("Analiz edilecek hisseleri virgülle ayırarak girin:", varsayilan_hisseler)
hisseler = [h.strip().upper() for h in hisse_input.split(",") if h.strip()]

if st.button("Analiz Et"):
    if not hisseler:
        st.warning("Lütfen en az bir hisse kodu girin.")
    else:
        sonuclar = []
        
        with st.spinner("Veriler çekiliyor ve analiz ediliyor..."):
            for hisse in hisseler:
                try:
                    # Son 1 yıllık günlük veriyi çek
                    ticker = yf.Ticker(hisse)
                    df = ticker.history(period="1y")
                    
                    if len(df) > 5:
                        # Overnight Getiri (Gece Getirisi) = (Bugünün Açılışı / Dünün Kapanışı) - 1
                        df['Onceki_Kapanis'] = df['Close'].shift(1)
                        df['Gece_Getirisi_%'] = ((df['Open'] / df['Onceki_Kapanis']) - 1) * 100
                        
                        # Sadece geçerli satırları al
                        gecerli_veri = df.dropna()
                        
                        if len(gecerli_veri) > 0:
                            ort_gece_getirisi = gecerli_veri['Gece_Getirisi_%'].mean()
                            pozitif_gun_orani = (gecerli_veri['Gece_Getirisi_%'] > 0).mean() * 100
                            max_getiri = gecerli_veri['Gece_Getirisi_%'].max()
                            min_getiri = gecerli_veri['Gece_Getirisi_%'].min()
                            
                            sonuclar.append({
                                "Hisse": hisse,
                                "Ortalama Gece Getirisi (%)": round(ort_gece_getirisi, 3),
                                "Pozitif Açılış Oranı (%)": round(pozitif_gun_orani, 2),
                                "En Yüksek Gece Getirisi (%)": round(max_getiri, 2),
                                "En Düşük Gece Getirisi (%)": round(min_getiri, 2)
                            })
                except Exception as e:
                    st.error(f"{hisse} verisi çekilemedi: {e}")
                    
        if sonuclar:
            df_sonuc = pd.DataFrame(sonuclar)
            # Pozitif açılış oranına göre sırala (En yüksekten en düşüğe)
            df_sonuc = df_sonuc.sort_values(by="Pozitif Açılış Oranı (%)", ascending=False)
            
            st.success("Analiz Tamamlandı!")
            st.dataframe(df_sonuc, use_container_width=True)
            
            st.info("""
            **Nasıl Yorumlanmalı?**
            *   **Pozitif Açılış Oranı:** Bu hisse, geçtiğimiz 1 yılda yüzde kaç oranında sabahtan artıda açılmış? (Örneğin %55 ise, 100 günün 55'inde sabah kârlı açılmış).
            *   **Ortalama Gece Getirisi:** Akşam alıp sabah satsaydınız ortalama yüzde kaç kâr ederdiniz?
            *   *Dikkat:* En düşük gece getirisine bakın! Bir günde ne kadar çok düşebileceğini (riskini) orada göreceksiniz.
            """)
        else:
            st.error("Hiçbir hisse için veri bulunamadı.")
