import streamlit as st

# Sayfa Ayarları
st.set_page_config(page_title="Fatura Denetim Sistemi", page_icon="📄")

st.title("📄 Filo Lojistiği Fatura Denetim Prototipi")
st.write("Bu araç, yüklenen faturaları analiz eder ve matematiksel/sözleşmesel anlaşmazlıkları tespit eder.")

# Dosya Yükleme Alanı
uploaded_file = st.file_uploader("Lütfen bir fatura yükleyin (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])

if uploaded_file is not None:
    st.success(f"'{uploaded_file.name}' başarıyla yüklendi.")
    
    # Prototipin ilk aşaması olduğu için şimdilik OCR (Görüntü İşleme) 
    # yerine simüle edilmiş verilerle kural motorunu test ediyoruz.
    st.subheader("1. Faturadan Çıkarılan Veriler (Simülasyon)")
    
    # Örnek veriler (Gerçekte OCR aracılığıyla faturadan okunacak)
    fatura_no = "FAC-2026-0042"
    ara_toplam = 1000.0
    vergi = 200.0
    toplam_tutar = 1300.0 # Bilerek hatalı toplanmış bir senaryo
    
    st.write(f"- **Fatura No:** {fatura_no}")
    st.write(f"- **Ara Toplam:** {ara_toplam} TL")
    st.write(f"- **Vergi:** {vergi} TL")
    st.write(f"- **Genel Toplam:** {toplam_tutar} TL")

    st.subheader("2. Denetim ve Anlaşmazlık Tespiti")
    
    # Kural Tabanlı (Deterministik) Kontrol
    hesaplanan_toplam = ara_toplam + vergi
    
    if hesaplanan_toplam != toplam_tutar:
        st.error(f"🚨 ANLAŞMAZLIK TESPİT EDİLDİ!")
        st.warning(f"Faturadaki genel toplam ({toplam_tutar} TL), ara toplam ve vergi toplamına ({hesaplanan_toplam} TL) eşit değil. Fark: {toplam_tutar - hesaplanan_toplam} TL")
    else:
        st.success("✅ Faturada matematiksel bir anlaşmazlık bulunamadı.")
        
    # Buraya LLM (Dil Modeli) entegrasyonu eklenecek
    st.info("Not: Sonraki adımlarda yapay zeka (LLM) bu hatayı okuyup size resmi bir anlaşmazlık raporu yazacak.")
