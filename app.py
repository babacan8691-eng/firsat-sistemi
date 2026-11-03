import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from google import genai
import time

# Tesseract Yol Ayarı
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(page_title="Akıllı Fatura Denetim", page_icon="📄", layout="wide")

st.title("📄 Akıllı Fatura Denetim Prototipi (LLM Aktif)")
st.write("Bu araç, belgeyi okur ve yapay zeka (Gemini) ile anlaşmazlıkları analiz eder.")

# API Anahtarı Girişi
api_key = st.text_input("🔑 Google Gemini API Anahtarınızı Girin:", type="password")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Belge Yükle")
    fatura_file = st.file_uploader("Fatura yükleyin (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])

with col2:
    st.subheader("2. Sözleşme (İsteğe Bağlı)")
    sozlesme_text = st.text_area("Sözleşme/Fiyat Kurallarını Yazın:", "Örnek: Navlun bedeli maksimum 500 TL olmalıdır.")

if fatura_file is not None:
    st.divider()
    
    # 1. OCR İŞLEMİ
    with st.spinner("Belge okunuyor..."):
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

    with st.expander("🔍 Belgeden Okunan Ham Metni Gör"):
        st.text(extracted_text)

    # 2. YAPAY ZEKA (LLM) ANALİZİ
    if len(extracted_text.strip()) > 10 and api_key:
        st.subheader("🤖 Yapay Zeka Denetim Raporu")
        
        with st.spinner("Yapay zeka belgeyi analiz ediyor..."):
            prompt = f"""
            Sen uzman bir finansal denetçisin. Aşağıda bir belgeden OCR ile okunmuş metin var.
            Ekteki sözleşme kurallarını da göz önünde bulundurarak bu belgeyi analiz et.
            
            Belge Metni:
            {extracted_text}
            
            Sözleşme Kuralları:
            {sozlesme_text}
            
            Lütfen şu formatta kısa ve net bir rapor yaz:
            1. Belge Türü (Fatura mı, fiş mi, ne faturası?)
            2. Toplam Ödenecek Tutar
            3. Matematiksel Veya Sözleşmesel Bir Anlaşmazlık (Hata) Var Mı? (Evet/Hayır)
            4. Eğer hata varsa detaylı açıklaması.
            """
            
            client = genai.Client(api_key=api_key)
            response = None
            
            # Birincil Model: gemini-3.8-flash (Otomatik Yeniden Deneme ile)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt
                    )
                    break # Başarılı olursa döngüden çık
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2) # 2 saniye bekle ve tekrar dene
                        continue
                    else:
                        break # Diğer hatalarda veya son denemede döngüden çık

            # Yedek Model: Eğer birincil model başarısız olursa gemini-3.6-flash'e geç
            if response is None:
                try:
                    st.warning("Birincil model şu an yoğun, yedek model deneniyor...")
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt
                    )
                except Exception as e:
                    st.error(f"Yapay Zeka Hatası: Her iki model de yanıt veremedi. Lütfen daha sonra tekrar deneyin. Detay: {e}")

            if response is not None:
                st.info(response.text)

    elif not api_key:
        st.warning("⚠️ Analizi başlatmak için lütfen yukarıya Gemini API Anahtarınızı girin.")
    else:
        st.warning("⚠️ Belgeden yeterli metin okunamadı.")

else:
    st.info("Lütfen analiz etmek için bir belge yükleyin.")
