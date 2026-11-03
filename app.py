import streamlit as st

# Sayfa Ayarları
st.set_page_config(page_title="Filo Lojistiği Fatura Denetim", page_icon="📄", layout="wide")

st.title("📄 Filo Lojistiği Fatura Denetim Prototipi")
st.write("Bu araç, yüklenen faturaları analiz eder ve matematiksel/sözleşmesel anlaşmazlıkları tespit eder.")

# --- YÜKLEME ALANLARI (Yan Yana İki Sütun) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Fatura Yükle")
    fatura_file = st.file_uploader("Faturayı yükleyin (PDF, JPG, PNG)", type=["pdf", "jpg", "png"], key="fatura")

with col2:
    st.subheader("2. Sözleşme & Ses")
    sozlesme_file = st.file_uploader("Sözleşme/Fiyat Listesi Yükle (İsteğe Bağlı)", type=["pdf", "csv", "xlsx"], key="sozlesme")
    ses_file = st.file_uploader("Sürücü Sesli Notu Yükle (İsteğe Bağlı)", type=["wav", "mp3", "m4a"], key="ses")

# --- ANALİZ BÖLÜMÜ ---
if fatura_file is not None:
    st.divider()
    st.success(f"'{fatura_file.name}' başarıyla yüklendi. Analiz başlatılıyor...")
    
    # 1. VERİ ÇIKARIMI (Şimdilik Simülasyon - İleride OCR ile gerçekleşecek)
    st.subheader("🔍 Faturadan Çıkarılan Veriler (Simülasyon)")
    
    # Senaryo: Fatura matematiksel olarak doğru ama sözleşmeye aykırı
    fatura_no = "FAC-2026-0042"
    navlun_fiyati = 600.0 # Faturada yazan
    ara_toplam = 1000.0
    vergi = 200.0
    toplam_tutar = 1200.0 # 1000 + 200 = 1200 (Matematik doğru)
    
    # Sözleşmeden çıkarılan veri (Simülasyon)
    sozlesme_navlun_fiyati = 500.0 # Sözleşmede anlaşılan fiyat
    
    st.write(f"- **Fatura No:** {fatura_no}")
    st.write(f"- **Navlun Bedeli:** {navlun_fiyati} TL")
    st.write(f"- **Ara Toplam:** {ara_toplam} TL")
    st.write(f"- **Vergi:** {vergi} TL")
    st.write(f"- **Genel Toplam:** {toplam_tutar} TL")

    # 2. DENETİM VE ANLAŞMAZLIK TESPİTİ
    st.subheader("⚖️ Denetim ve Anlaşmazlık Tespiti")
    
    hata_var = False
    
    # Kural 1: Matematiksel Kontrol
    hesaplanan_toplam = ara_toplam + vergi
    if hesaplanan_toplam != toplam_tutar:
        st.error(f"🚨 **Matematiksel Hata:** Faturadaki genel toplam ({toplam_tutar} TL), ara toplam ve vergi toplamına ({hesaplanan_toplam} TL) eşit değil.")
        hata_var = True
    else:
        st.success("✅ Matematiksel tutarlılık sağlandı (Ara Toplam + Vergi = Genel Toplam).")
        
    # Kural 2: Sözleşme Fiyat Kontrolü
    if navlun_fiyati > sozlesme_navlun_fiyati:
        st.error(f"🚨 **Sözleşme İhlali:** Faturadaki navlun bedeli ({navlun_fiyati} TL), sözleşmede anlaşılan bedelden ({sozlesme_navlun_fiyati} TL) yüksek!")
        hata_var = True
    else:
        st.success("✅ Navlun bedeli sözleşme ile uyumlu.")

    # 3. SESLİ NOT ANALİZİ (Simülasyon)
    if ses_file is not None:
        st.warning(f"🎤 **Sesli Not İşlendi:** '{ses_file.name}' dosyası metne döküldü. Özet: Sürücü, navlun bedelinin sözleşmeden farklı olduğunu belirtiyor.")
    
    # 4. YAPAY ZEKA RAPORU (Simülasyon)
    st.divider()
    st.subheader("🤖 Yapay Zeka Anlaşmazlık Raporu")
    if hata_var:
        st.info("**AI Raporu:** Sayın yetkili, bu faturada sözleşme ihlali tespit edilmiştir. Faturadaki navlun bedeli 600 TL iken, anlaşmanız 500 TL'dir. Lütfen tedarikçi ile iletişime geçin. (Not: Bu rapor LLM tarafından yazılmış gibi simüle edilmiştir).")
    else:
        st.info("**AI Raporu:** Fatura üzerinde herhangi bir anlaşmazlık bulunamadı. Ödeme için onaylanabilir.")

else:
    st.info("Lütfen analiz etmek için bir fatura yükleyin.")
