import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import re

# Tesseract Yol Ayarı (Streamlit Cloud için hayati önem taşır)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Sayfa Ayarları
st.set_page_config(page_title="Filo Lojistiği Fatura Denetim", page_icon="📄", layout="wide")

st.title("📄 Filo Lojistiği Fatura Denetim Prototipi (Gerçek OCR Aktif)")
st.write("Bu araç, yüklenen faturaları tarar, metni okur ve matematiksel/sözleşmesel anlaşmazlıkları tespit eder.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Fatura Yükle")
    fatura_file = st.file_uploader("Faturayı yükleyin (PDF, JPG, PNG)", type=["pdf", "jpg", "png"], key="fatura")

with col2:
    st.subheader("2. Sözleşme & Ses")
    sozlesme_file = st.file_uploader("Sözleşme/Fiyat Listesi Yükle (İsteğe Bağlı)", type=["pdf", "csv", "xlsx"], key="sozlesme")
    ses_file = st.file_uploader("Sürücü Sesli Notu Yükle (İsteğe Bağlı)", type=["wav", "mp3", "m4a"], key="ses")

if fatura_file is not None:
    st.divider()
    
    # 1. OCR İŞLEMİ (Gerçek Okuma)
    with st.spinner("Yapay zeka faturayı okuyor, lütfen bekleyin..."):
        try:
            if fatura_file.type == "application/pdf":
                # PDF'i resme çevir ve ilk sayfayı oku
                images = convert_from_bytes(fatura_file.read())
                image = images[0]
            else:
                # Direkt resim olarak aç
                image = Image.open(fatura_file)
            
            # Tesseract ile metni çıkar (Türkçe dil desteğiyle)
            extracted_text = pytesseract.image_to_string(image, lang='tur')
            
        except Exception as e:
            st.error(f"OCR Hatası: Belge okunamadı. Hata detayı: {e}")
            extracted_text = ""

    # Okunan metni göster
    with st.expander("🔍 Faturadan Okunan Ham Metni Gör"):
        st.text(extracted_text)

    st.subheader("⚖️ Denetim ve Anlaşmazlık Tespiti")
    
    # Rakamları bul
    tutarlar = re.findall(r'\b\d{1,3}(?:\.\d{3})*(?:,\d{2})?\b', extracted_text)
    
    if len(extracted_text.strip()) < 10:
        st.warning("⚠️ Belgeden yeterli metin okunamadı. Lütfen daha net bir görsel yükleyin veya sistem dosyalarını (packages.txt) kontrol edin.")
    else:
        st.success("✅ Fatura taranıp metne döküldü.")
        
        st.info("💡 **Bilgi:** Şu an metin okuma aktif. Aşağıdaki tutarlar, kural motorunu test etmek için simüle edilmiştir.")
        
        # Hata senaryosu simülasyonu
        ara_toplam = 1000.0
        vergi = 200.0
        toplam_tutar = 1300.0
        navlun_fiyati = 600.0
        sozlesme_navlun_fiyati = 500.0
        
        st.write("### 📊 Sistemin Çıkardığı Veriler (Test Verisi)")
        st.write(f"- **Ara Toplam:** {ara_toplam} TL")
        st.write(f"- **Vergi:** {vergi} TL")
        st.write(f"- **Genel Toplam:** {toplam_tutar} TL")
        st.write(f"- **Navlun Bedeli:** {navlun_fiyati} TL")

        # Kural Motoru
        hata_var = False
        hesaplanan_toplam = ara_toplam + vergi
        
        if hesaplanan_toplam != toplam_tutar:
            st.error(f"🚨 **Matematiksel Hata:** Genel toplam ({toplam_tutar} TL), ara toplam ve vergi toplamına ({hesaplanan_toplam} TL) eşit değil.")
            hata_var = True
        else:
            st.success("✅ Matematiksel tutarlılık sağlandı.")
            
        if navlun_fiyati > sozlesme_navlun_fiyati:
            st.error(f"🚨 **Sözleşme İhlali:** Faturadaki navlun bedeli ({navlun_fiyati} TL), sözleşmeden ({sozlesme_navlun_fiyati} TL) yüksek!")
            hata_var = True
        else:
            st.success("✅ Navlun bedeli sözleşme ile uyumlu.")

        st.divider()
        st.subheader("🤖 Yapay Zeka Anlaşmazlık Raporu")
        if hata_var:
            st.info("**AI Raporu:** Faturada tespit edilen tutarsızlıklar bulunmaktadır. Lütfen yukarıdaki uyarıları inceleyin.")
        else:
            st.info("**AI Raporu:** Fatura temiz görünüyor.")

else:
    st.info("Lütfen analiz etmek için bir fatura yükleyin.")
