import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from google import genai
import pandas as pd
import json
import time
import re

# Tesseract Yol Ayarı
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(page_title="Akıllı Filo Denetim", page_icon="📄", layout="wide")

st.title("📄 Akıllı Filo Lojistiği Fatura Denetimi")
st.write("Faturayı ve sözleşme fiyat listenizi yükleyin, yapay zeka saniyeler içinde denetlesin.")

# API Anahtarı Girişi (Sol Menüde tutmak daha temizdir)
with st.sidebar:
    st.header("Ayarlar")
    api_key = st.text_input("🔑 Gemini API Anahtarı:", type="password")
    st.markdown("---")
    st.markdown("**Nasıl Kullanılır?**")
    st.markdown("1. Sözleşme fiyat listenizi (CSV) yükleyin.\n2. Faturayı yükleyin.\n3. Analizi başlatın.")

# Örnek CSV indirme butonu (Kullanıcı formata anında adapte olsun)
ornek_csv = "Firma;Guzergah;AracTipi;NavlunFiyati\nABC Lojistik;İstanbul-Ankara;TIR;4500\nABC Lojistik;İzmir-Bursa;Kamyon;2800"
st.sidebar.download_button(label="📥 Örnek Sözleşme CSV İndir", data=ornek_csv, file_name="ornek_sozlesme.csv", mime="text/csv")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Fatura Yükle")
    fatura_file = st.file_uploader("Faturayı yükleyin (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])

with col2:
    st.subheader("2. Sözleşme Fiyat Listesi (CSV)")
    sozlesme_file = st.file_uploader("Fiyat listesini yükleyin (CSV)", type=["csv"])

if fatura_file is not None and api_key:
    
    # 1. SÖZLEŞMEYİ OKU
    sozlesme_data = ""
    if sozlesme_file is not None:
        try:
            df_sozlesme = pd.read_csv(sozlesme_file, sep=None, engine='python') # Ayırıcıyı otomatik bul
            sozlesme_data = df_sozlesme.to_string(index=False)
            with st.expander("📄 Yüklenen Sözleşme Verisi"):
                st.dataframe(df_sozlesme)
        except Exception as e:
            st.error(f"Sözleşme okuma hatası: {e}")

    st.divider()
    
    # 2. OCR İŞLEMİ
    with st.spinner("Fatura taranıyor..."):
        try:
            if fatura_file.type == "application/pdf":
                images = convert_from_bytes(fatura_file.read())
                image = images[0]
            else:
                image = Image.open(fatura_file)
            
            extracted_text = pytesseract.image_to_string(image, lang='tur')
        except Exception as e:
            st.error(f"OCR Hatası: {e}")
            extracted_text = ""

    with st.expander("🔍 Faturadan Okunan Metni Gör"):
        st.text(extracted_text)

    # 3. YAPAY ZEKA ANALİZİ VE JSON ÇIKTISI
    if len(extracted_text.strip()) > 10:
        st.subheader("🤖 Yapay Zeka Denetim Raporu")
        
        with st.spinner("Yapay zeka faturayı sözleşmeyle karşılaştırıyor..."):
            
            # Prompt (Yapay zekaya verilecek katı kurallar)
            prompt = f"""
            Sen uzman bir finansal denetçisin. 
            Aşağıda bir faturadan OCR ile okunmuş metin ve bir sözleşme fiyat listesi (CSV) var.
            
            Fatura Metni:
            {extracted_text}
            
            Sözleşme Fiyat Listesi:
            {sozlesme_data}
            
            Görevin: Faturadaki verileri (Tedarikçi, Güzergah, Araç Tipi, Navlun Bedeli) bulup sözleşme listesindeki fiyatlarla karşılaştırmak.
            Eğer faturadaki fiyat sözleşmeden yüksekse veya listede yoksa "Anlaşmazlık" olarak işaretle.
            
            Lütfen çıktıyı SADECE aşağıdaki formatta geçerli bir JSON olarak ver. Başka hiçbir açıklama yazma:
            {{
                "Tedarikci": "Faturadaki firma adı",
                "Guzergah": "Faturadaki güzergah (varsa)",
                "Fatura_Navlun": 1250.0,
                "Sozlesme_Navlun": 1000.0,
                "Fark": 250.0,
                "Durum": "Anlaşmazlık Var" veya "Uyumlu",
                "Aciklama": "Faturadaki navlun sözleşmeden yüksek vb."
            }}
            """

            client = genai.Client(api_key=api_key)
            response = None
            models_to_try = ['gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite']
            
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    break
                except Exception as e:
                    if "503" in str(e) or "429" in str(e):
                        time.sleep(1.5)
                        continue
                    else:
                        st.error(f"API Hatası: {e}")
                        break

            if response is not None:
                # Gelen yanıtı temizle ve JSON'a çevir
                raw_text = response.text.strip()
                # Bazen LLM ```json ... ``` şeklinde yazar, onu temizle
                clean_json = re.sub(r'^```json\s*|\s*```$', '', raw_text, flags=re.MULTILINE)
                
                try:
                    data = json.loads(clean_json)
                    
                    # EKRANA GÜZEL BİR TABLO (DASHBOARD) ÇİZ
                    st.success("Analiz Tamamlandı!")
                    
                    # Metrik Kartları
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Fatura Navlun", f"{data.get('Fatura_Navlun', 0)} TL")
                    m2.metric("Sözleşme Navlun", f"{data.get('Sozlesme_Navlun', 0)} TL")
                    fark = data.get('Fark', 0)
                    m3.metric("Fark", f"{fark} TL", delta_color="inverse" if fark > 0 else "normal")
                    
                    # Durum Uyarısı
                    if "Anlaşmazlık" in data.get('Durum', ''):
                        st.error(f"🚨 **{data.get('Durum')}** - {data.get('Aciklama')}")
                    else:
                        st.success(f"✅ **{data.get('Durum')}** - {data.get('Aciklama')}")
                        
                    # Detay Tablosu
                    df_sonuc = pd.DataFrame(list(data.items()), columns=["Özellik", "Değer"])
                    st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
                    
                except json.JSONDecodeError:
                    st.error("Yapay zeka geçerli bir format döndüremedi. Ham çıktı:")
                    st.code(raw_text)
            else:
                st.error("Modeller şu an yoğun, lütfen tekrar deneyin.")
                
    elif not sozlesme_file:
        st.warning("⚠️ Lütfen karşılaştırma yapmak için bir Sözleşme (CSV) yükleyin.")
    else:
        st.warning("⚠️ Belgeden yeterli metin okunamadı.")

elif not api_key:
    st.info("Başlamak için sol menüden API anahtarınızı girin.")
else:
    st.info("Lütfen analiz etmek için Fatura yükleyin.")
