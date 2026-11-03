import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from google import genai
import pandas as pd
import json
import time
import re
import sqlite3
import hashlib
from datetime import datetime

# Tesseract Yol Ayarı
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# --- VERİTABANI KURULUMU (Mükerrer Kontrol ve Denetim İzi İçin) ---
def init_db():
    conn = sqlite3.connect('lojistik_denetim.db')
    c = conn.cursor()
    # Faturalar Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS faturalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fatura_no TEXT UNIQUE,
                  tedarikci TEXT,
                  tarih TEXT,
                  fatura_tutari REAL,
                  sozlesme_tutari REAL,
                  fark REAL,
                  durum TEXT,
                  onay_durumu TEXT DEFAULT 'Bekliyor',
                  denetim_izi TEXT)''')
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(page_title="Lojistik Fatura Denetim Sistemi", page_icon="📄", layout="wide")

st.title("📄 Kurumsal Lojistik Fatura Denetim ve Mutabakat Sistemi")
st.write("Piyasa standartlarında; mükerrer kontrol, iş akışı ve ERP entegrasyonu içeren tam kapsamlı denetim aracı.")

# --- SOL MENÜ (KONTROL PANELİ) ---
with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    api_key = st.text_input("🔑 Gemini API Anahtarı:", type="password")
    
    st.markdown("---")
    st.subheader("📊 Özet Metrikler")
    
    # Veritabanından metrikleri çek
    try:
        df_gecmis = pd.read_sql_query("SELECT * FROM faturalar", conn)
        toplam_denetlenen = len(df_gecmis)
        engellenen_tutar = df_gecmis[df_gecmis['durum'].str.contains('Anlaşmazlık', na=False)]['fark'].sum()
        
        st.metric("Denetlenen Fatura", toplam_denetlenen)
        st.metric("Engellenen Fazla Ödeme", f"{engellenen_tutar:,.2f} TL", delta_color="inverse")
    except:
        st.write("Henüz veri yok.")

# --- ANA EKRAN SEKMELERİ ---
tab1, tab2, tab3 = st.tabs(["🔍 Fatura Denetle", "📋 İş Akışı ve Onay", "📈 Raporlar ve ERP Aktarımı"])

with tab1:
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
                df_sozlesme = pd.read_csv(sozlesme_file, sep=None, engine='python')
                sozlesme_data = df_sozlesme.to_string(index=False)
            except Exception as e:
                st.error(f"Sözleşme okuma hatası: {e}")

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

        # 3. YAPAY ZEKA ANALİZİ (JSON)
        if len(extracted_text.strip()) > 10:
            with st.spinner("Yapay zeka denetim yapıyor..."):
                prompt = f"""
                Sen uzman bir lojistik finansal denetçisisin. 
                Fatura Metni:
                {extracted_text}
                Sözleşme Listesi:
                {sozlesme_data}
                
                Görevin: Belgenin lojistik faturası olup olmadığını kontrol et. Lojistikse; Tedarikçi, Fatura No, Tutar ve Sözleşme karşılaştırmasını yap.
                Çıktıyı SADECE geçerli bir JSON olarak ver:
                {{
                    "Belge_Turu": "Lojistik" veya "Gecersiz",
                    "Fatura_No": "Faturadaki numara",
                    "Tedarikci": "Firma adı",
                    "Fatura_Tutari": 0.0,
                    "Sozlesme_Tutari": 0.0,
                    "Fark": 0.0,
                    "Durum": "Anlaşmazlık Var" veya "Uyumlu",
                    "Aciklama": "Kısa açıklama"
                }}
                """
                
                client = genai.Client(api_key=api_key)
                response = None
                for model_name in ['gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite']:
                    try:
                        response = client.models.generate_content(model=model_name, contents=prompt)
                        break
                    except Exception as e:
                        if "503" in str(e) or "429" in str(e): time.sleep(1.5); continue
                        else: st.error(f"API Hatası: {e}"); break

                if response:
                    clean_json = re.sub(r'^```json\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)
                    try:
                        data = json.loads(clean_json)
                        
                        if data.get("Belge_Turu") == "Gecersiz":
                            st.error("🚨 Geçersiz Belge! Lütfen lojistik faturası yükleyin.")
                        else:
                            # MÜKERRER FATURA KONTROLÜ
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM faturalar WHERE fatura_no = ?", (data.get("Fatura_No"),))
                            if cursor.fetchone():
                                st.warning(f"⚠️ MÜKERRER FATURA! '{data.get('Fatura_No')}' numaralı fatura daha önce işlenmiş.")
                            else:
                                # VERİTABANINA KAYDET
                                cursor.execute("INSERT INTO faturalar (fatura_no, tedarikci, tarih, fatura_tutari, sozlesme_tutari, fark, durum, denetim_izi) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                               (data.get("Fatura_No"), data.get("Tedarikci"), datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                                data.get("Fatura_Tutari"), data.get("Sozlesme_Tutari"), data.get("Fark"), 
                                                data.get("Durum"), f"YZ tarafından oluşturuldu. Açıklama: {data.get('Aciklama')}"))
                                conn.commit()
                                
                                # SONUÇLARI GÖSTER
                                st.success("Denetim Tamamlandı ve Sisteme Kaydedildi!")
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Fatura Tutarı", f"{data.get('Fatura_Tutari')} TL")
                                m2.metric("Sözleşme Tutarı", f"{data.get('Sozlesme_Tutari')} TL")
                                m3.metric("Fark", f"{data.get('Fark')} TL", delta_color="inverse" if data.get('Fark', 0) > 0 else "normal")
                                
                                if "Anlaşmazlık" in data.get('Durum', ''):
                                    st.error(f"🚨 {data.get('Aciklama')}")
                                else:
                                    st.success(f"✅ {data.get('Aciklama')}")
                    except json.JSONDecodeError:
                        st.error("Yapay zeka format hatası.")

with tab2:
    st.subheader("📋 Fatura Onay ve İş Akışı Yönetimi")
    st.write("Sistemde kayıtlı faturaların durumunu yönetin ve onaylayın.")
    
    df_is_akisi = pd.read_sql_query("SELECT * FROM faturalar ORDER BY id DESC", conn)
    if not df_is_akisi.empty:
        for index, row in df_is_akisi.iterrows():
            with st.expander(f"{row['fatura_no']} - {row['tedarikci']} ({row['durum']})"):
                st.write(f"**Tarih:** {row['tarih']}")
                st.write(f"**Fatura Tutarı:** {row['fatura_tutari']} TL | **Sözleşme:** {row['sozlesme_tutari']} TL")
                st.write(f"**Denetim İzi:** {row['denetim_izi']}")
                
                # İŞ AKIŞI BUTONLARI
                c1, c2, c3 = st.columns(3)
                if c1.button(f"✅ Onayla", key=f"onay_{row['id']}"):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'Onaylandı', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%H:%M')} Onaylandı' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
                if c2.button(f"❌ Reddet", key=f"red_{row['id']}"):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'Reddedildi', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%H:%M')} Reddedildi' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
                if c3.button(f"⚖️ İtiraz Et", key=f"itiraz_{row['id']}"):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'İtiraz Edildi', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%H:%M')} İtiraz Edildi' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
    else:
        st.info("Henüz işlenecek fatura yok.")

with tab3:
    st.subheader("📈 Raporlama ve ERP Entegrasyonu")
    st.write("Denetlenen faturaları raporlayın ve ERP sistemlerine (Logo, Netsis, SAP) aktarılacak formatta indirin.")
    
    df_rapor = pd.read_sql_query("SELECT * FROM faturalar", conn)
    if not df_rapor.empty:
        st.dataframe(df_rapor, use_container_width=True)
        
        # ERP AKTARIMI (CSV)
        csv = df_rapor.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ERP İçin İndir (CSV)",
            data=csv,
            file_name=f"erp_lojistik_fatura_aktarim_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Bu dosyayı Logo, Netsis, SAP veya Mikro sistemlerinize aktarabilirsiniz."
        )
    else:
        st.info("Raporlanacak veri bulunamadı.")

# Veritabanı bağlantısını kapat
conn.close()
