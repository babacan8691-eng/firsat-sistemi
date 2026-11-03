import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import google.generativeai as genai

# Tesseract Yol Ayarı
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(page_title="Akıllı Fatura Denetim", page_icon="📄", layout="wide")

st.title("📄 Akıllı Fatura Denetim Prototipi (LLM Aktif)")
st.write("Bu araç, belgeyi okur ve yapay zeka (Gemini) ile anlaşmazlıkları analiz eder.")

# API Anahtarı Girişi (Güvenlik nedeniyle kodun içine gömülmedi, arayüzden girilecek)
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
            try:
                # Gemini'yi yapılandır
                genai.configure(api_key=api_key)
                
                # Model güncellemesi: 'gemini-1.5-flash-latest' hatayı çözecektir.
                # Eğer yine sorun yaşarsanız 'gemini-pro' yazabilirsiniz.
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                # Prompt (Yapay Zekaya Verilecek Görev)
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
                
                response = model.generate_content(prompt)
                
                # Raporu ekrana yazdır
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Yapay Zeka Hatası: Lütfen API anahtarınızı kontrol edin veya sistem yöneticinize başvurun. Hata Detayı: {e}")
    elif not api_key:
        st.warning("⚠️ Analizi başlatmak için lütfen yukarıya Gemini API Anahtarınızı girin.")
    else:
        st.warning("⚠️ Belgeden yeterli metin okunamadı.")

else:
    st.info("Lütfen analiz etmek için bir belge yükleyin.")
