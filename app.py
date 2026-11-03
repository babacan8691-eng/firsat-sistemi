import streamlit as st
from google import genai
import pandas as pd
import json
import time
import re
import sqlite3
from datetime import datetime
import io

# --- VERİTABANI KURULUMU (Gerçek Piyasa Şeması) ---
def init_db():
    conn = sqlite3.connect('lojistik_denetim_v2.db')
    c = conn.cursor()
    # Gelişmiş Fatura Tablosu (VKN, İrsaliye, Plaka, Güven Skoru vb. eklendi)
    c.execute('''CREATE TABLE IF NOT EXISTS faturalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fatura_no TEXT,
                  tedarikci_vkn TEXT,
                  tedarikci_adi TEXT,
                  fatura_tarihi TEXT,
                  irsaliye_no TEXT,
                  plaka TEXT,
                  fatura_tutari REAL,
                  sozlesme_tutari REAL,
                  fark REAL,
                  tolerans_dahilinde_mi TEXT,
                  durum TEXT,
                  onay_durumu TEXT DEFAULT 'Bekliyor',
                  ai_guven_skoru REAL,
                  denetim_izi TEXT,
                  UNIQUE(fatura_no, tedarikci_vkn))''') # Gerçek mükerrer kontrolü
    conn.commit()
    return conn

conn = init_db()

st.set_page_config(page_title="Lojistik Fatura Denetim Sistemi", page_icon="📄", layout="wide")

st.title("📄 Kurumsal Lojistik Fatura Denetim ve Mutabakat Sistemi")
st.write("Piyasa standartlarında; lojistik odaklı veri çıkarımı, akıllı mükerrer kontrolü ve tolerans yönetimi içeren denetim aracı.")

# --- SOL MENÜ (KONTROL PANELİ) ---
with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    api_key = st.text_input("🔑 Gemini API Anahtarı:", type="password")
    
    # Piyasa Gerçeği: Tolerans Oranı Ayarı
    tolerans_orani = st.slider("Kabul Edilebilir Fark Toleransı (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.5, help="Sözleşme ile fatura arasındaki bu orandaki farklar otomatik onaylanır.")
    
    st.markdown("---")
    st.subheader("📊 Özet Metrikler")
    
    try:
        df_gecmis = pd.read_sql_query("SELECT * FROM faturalar", conn)
        toplam_denetlenen = len(df_gecmis)
        engellenen_tutar = df_gecmis[(df_gecmis['durum'].str.contains('Anlaşmazlık', na=False)) & (df_gecmis['tolerans_dahilinde_mi'] == 'Hayır')]['fark'].sum()
        
        st.metric("Denetlenen Fatura", toplam_denetlenen)
        st.metric("Engellenen Fazla Ödeme", f"{engellenen_tutar:,.2f} TL", delta_color="inverse")
    except Exception as e:
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
        sozlesme_data = "Sözleşme yüklenmedi."
        if sozlesme_file is not None:
            try:
                df_sozlesme = pd.read_csv(sozlesme_file, sep=None, engine='python')
                sozlesme_data = df_sozlesme.to_string(index=False)
            except Exception as e:
                st.error(f"Sözleşme okuma hatası: {e}")

        # 2. GEMINI VISION İLE DOĞRUDAN ANALİZ (OCR Hatasını Sıfıra İndirir)
        if st.button("🚀 Denetimi Başlat", type="primary"):
            with st.spinner("Yapay zeka belgeyi inceliyor ve lojistik verilerini çıkarıyor..."):
                
                # Dosyayı Gemini'nin anlayacağı formata çevir
                file_bytes = fatura_file.read()
                mime_type = fatura_file.type
                
                prompt = f"""
                Sen uzman bir kurumsal lojistik finansal denetçisisin. 
                Ekteki belgeyi incele. Belgenin geçerli bir lojistik/taşıma faturası olup olmadığını kontrol et.
                
                Sözleşme Fiyat Listesi:
                {sozlesme_data}
                
                Görevin: Faturadaki verileri çıkar, sözleşme ile karşılaştır ve farkları bul.
                Çıktıyı SADECE aşağıdaki formatta geçerli bir JSON olarak ver. Başka hiçbir metin yazma:
                {{
                    "Belge_Turu": "Lojistik" veya "Gecersiz",
                    "Fatura_No": "Faturadaki numara",
                    "Tedarikci_VKN": "Tedarikçinin Vergi No'su (Bulamazsan 'YOK' yaz)",
                    "Tedarikci_Adi": "Firma adı",
                    "Fatura_Tarihi": "YYYY-MM-DD",
                    "Irsaliye_No": "İrsaliye/Sevk irsaliyesi numarası (Yoksa 'YOK')",
                    "Plaka": "Araç plakası (Yoksa 'YOK')",
                    "Fatura_Tutari": 0.0,
                    "Sozlesme_Tutari": 0.0,
                    "Fark": 0.0,
                    "Durum": "Anlaşmazlık Var" veya "Uyumlu",
                    "Aciklama": "Fark varsa nedenleri (örn: Birim fiyat farkı, mesafe farkı vb.)",
                    "AI_Guven_Skoru": 0.0 ila 1.0 arası (Belgenin netliğine göre)
                }}
                """
                
                client = genai.Client(api_key=api_key)
                response = None
                
                # Kararlı model fallback mekanizması
                for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro']:
                    try:
                        # Direkt dosyayı gönderiyoruz (Vision)
                        response = client.models.generate_content(
                            model=model_name, 
                            contents=[prompt, genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
                        )
                        break
                    except Exception as e:
                        if "503" in str(e) or "429" in str(e): 
                            time.sleep(2)
                            continue
                        else: 
                            st.error(f"API Hatası: {e}")
                            break

                if response:
                    clean_json = re.sub(r'^```json\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)
                    try:
                        data = json.loads(clean_json)
                        
                        if data.get("Belge_Turu") == "Gecersiz":
                            st.error("🚨 Geçersiz Belge! Lütfen geçerli bir lojistik faturası yükleyin.")
                        else:
                            # --- PİYASA GERÇEĞİ: MÜKERRER KONTROLÜ (Fatura No + VKN) ---
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM faturalar WHERE fatura_no = ? AND tedarikci_vkn = ?", 
                                           (data.get("Fatura_No"), data.get("Tedarikci_VKN")))
                            
                            if cursor.fetchone():
                                st.warning(f"⚠️ MÜKERRER FATURA! '{data.get('Tedarikci_Adi')}' firmasına ait '{data.get('Fatura_No')}' numaralı fatura daha önce işlenmiş.")
                            else:
                                # --- PİYASA GERÇEĞİ: TOLERANS HESABI ---
                                fark = data.get("Fark", 0.0)
                                sozlesme_tutari = data.get("Sozlesme_Tutari", 1.0)
                                tolerans_dahilinde = "Hayır"
                                
                                if sozlesme_tutari > 0:
                                    fark_yuzdesi = (fark / sozlesme_tutari) * 100
                                    if fark_yuzdesi <= tolerans_orani:
                                        tolerans_dahilinde = "Evet"
                                        data["Durum"] = "Uyumlu (Tolerans İçinde)"
                                        data["Aciklama"] += f" (Fark %{fark_yuzdesi:.2f}, tolerans sınırı içinde kabul edildi.)"

                                # VERİTABANINA KAYDET
                                cursor.execute("""INSERT INTO faturalar 
                                    (fatura_no, tedarikci_vkn, tedarikci_adi, fatura_tarihi, irsaliye_no, plaka, 
                                     fatura_tutari, sozlesme_tutari, fark, tolerans_dahilinde_mi, durum, ai_guven_skoru, denetim_izi) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (data.get("Fatura_No"), data.get("Tedarikci_VKN"), data.get("Tedarikci_Adi"), 
                                     data.get("Fatura_Tarihi"), data.get("Irsaliye_No"), data.get("Plaka"),
                                     data.get("Fatura_Tutari"), sozlesme_tutari, fark, tolerans_dahilinde, 
                                     data.get("Durum"), data.get("AI_Guven_Skoru"),
                                     f"YZ tarafından oluşturuldu. Açıklama: {data.get('Aciklama')}"))
                                conn.commit()
                                
                                # SONUÇLARI GÖSTER
                                st.success("Denetim Tamamlandı ve Sisteme Kaydedildi!")
                                m1, m2, m3, m4 = st.columns(4)
                                m1.metric("Fatura Tutarı", f"{data.get('Fatura_Tutari')} TL")
                                m2.metric("Sözleşme Tutarı", f"{sozlesme_tutari} TL")
                                m3.metric("Fark", f"{fark} TL", delta_color="inverse" if fark > 0 else "normal")
                                m4.metric("YZ Güven Skoru", f"%{data.get('AI_Guven_Skoru', 0)*100:.0f}")
                                
                                if data.get("Irsaliye_No") != "YOK" or data.get("Plaka") != "YOK":
                                    st.info(f"🚛 **Lojistik Detay:** İrsaliye: {data.get('Irsaliye_No')} | Plaka: {data.get('Plaka')}")
                                
                                if "Anlaşmazlık" in data.get('Durum', ''):
                                    st.error(f"🚨 {data.get('Aciklama')}")
                                else:
                                    st.success(f"✅ {data.get('Aciklama')}")
                                    
                    except json.JSONDecodeError:
                        st.error("Yapay zeka format hatası. Lütfen tekrar deneyin.")

with tab2:
    st.subheader("📋 Fatura Onay ve İş Akışı Yönetimi")
    st.write("Sistemde kayıtlı faturaların durumunu yönetin ve onaylayın.")
    
    df_is_akisi = pd.read_sql_query("SELECT * FROM faturalar ORDER BY id DESC", conn)
    if not df_is_akisi.empty:
        for index, row in df_is_akisi.iterrows():
            # Durum ikonları
            durum_ikon = "🟢" if "Uyumlu" in str(row['durum']) else "🔴"
            
            with st.expander(f"{durum_ikon} {row['fatura_no']} - {row['tedarikci_adi']} ({row['durum']})"):
                c_info1, c_info2 = st.columns(2)
                c_info1.write(f"**Tarih:** {row['fatura_tarihi']} | **VKN:** {row['tedarikci_vkn']}")
                c_info2.write(f"**İrsaliye:** {row['irsaliye_no']} | **Plaka:** {row['plaka']}")
                
                st.write(f"**Tutarlar:** Fatura: {row['fatura_tutari']} TL | Sözleşme: {row['sozlesme_tutari']} TL | **Fark: {row['fark']} TL**")
                st.write(f"**Denetim İzi:** {row['denetim_izi']}")
                
                # İŞ AKIŞI BUTONLARI
                c1, c2, c3 = st.columns(3)
                if c1.button(f"✅ Onayla", key=f"onay_{row['id']}", disabled=(row['onay_durumu']=="Onaylandı")):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'Onaylandı', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%d-%m %H:%M')} Finans Onayladı' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
                if c2.button(f"❌ Reddet", key=f"red_{row['id']}", disabled=(row['onay_durumu']=="Reddedildi")):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'Reddedildi', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%d-%m %H:%M')} Finans Reddetti' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
                if c3.button(f"⚖️ İtiraz Et (Tedarikçiye)", key=f"itiraz_{row['id']}"):
                    conn.execute(f"UPDATE faturalar SET onay_durumu = 'İtiraz Edildi', denetim_izi = denetim_izi || ' | {datetime.now().strftime('%d-%m %H:%M')} Tedarikçiye İtiraz Edildi' WHERE id = {row['id']}")
                    conn.commit()
                    st.rerun()
    else:
        st.info("Henüz işlenecek fatura yok.")

with tab3:
    st.subheader("📈 Raporlama ve ERP Entegrasyonu")
    st.write("Denetlenen faturaları raporlayın ve ERP sistemlerine (Logo, Netsis, SAP) aktarılacak formatta indirin.")
    
    df_rapor = pd.read_sql_query("SELECT * FROM faturalar", conn)
    if not df_rapor.empty:
        # ERP'nin seveceği temiz format
        df_erp = df_rapor[['fatura_no', 'tedarikci_vkn', 'tedarikci_adi', 'fatura_tarihi', 'fatura_tutari', 'onay_durumu']].copy()
        df_erp.rename(columns={'fatura_no': 'FATURA_NO', 'tedarikci_vkn': 'VERGI_NO', 'tedarikci_adi': 'UNVAN', 'fatura_tarihi': 'TARIH', 'fatura_tutari': 'TUTAR', 'onay_durumu': 'DURUM'}, inplace=True)
        
        st.dataframe(df_erp, use_container_width=True)
        
        # ERP AKTARIMI (CSV)
        csv = df_erp.to_csv(index=False).encode('utf-8-sig') # utf-8-sig Excel ve ERP uyumu içindir
        st.download_button(
            label="📥 ERP İçin İndir (CSV)",
            data=csv,
            file_name=f"erp_lojistik_aktarim_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Logo, Netsis, SAP ve Mikro formatlarına uyumludur."
        )
    else:
        st.info("Raporlanacak veri bulunamadı.")

# Veritabanı bağlantısını kapat
conn.close()
