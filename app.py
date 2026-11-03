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
            
            # google-genai istemcisi (SDK, geçici hatalarda otomatik yeniden dener)
            client = genai.Client(api_key=api_key)
            response = None
            error_message = ""
            
            # Sırayla denenecek modeller (Yoğunluk durumunda hafif modele geçiş)
            models_to_try = ['gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite']
            
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    break # Başarılı olursa döngüden çık
                except Exception as e:
                    error_message = str(e)
                    # Eğer 503 (Yoğunluk) veya 429 (Hız Limiti) hatasıysa kısa bir süre bekle ve sonraki modeli dene
                    if "503" in error_message or "429" in error_message:
                        time.sleep(2) # 2 saniye bekle
                        continue
                    else:
                        # API anahtarı hatası vb. durumlarda döngüyü kır
                        break

            if response is not None:
                st.success(f"Analiz '{model_name}' modeli ile tamamlandı.")
                st.info(response.text)
            else:
                st.error(f"Yapay Zeka Hatası: Tüm modeller şu an yoğun veya geçici bir sorun var. Lütfen 1-2 dakika sonra tekrar deneyin. Detay: {error_message}")

    elif not api_key:
        st.warning("⚠️ Analizi başlatmak için lütfen yukarıya Gemini API Anahtarınızı girin.")
    else:
        st.warning("⚠️ Belgeden yeterli metin okunamadı.")

else:
    st.info("Lütfen analiz etmek için bir belge yükleyin.")
