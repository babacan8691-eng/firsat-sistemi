import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Erişilebilirlik İşletim Sistemi", layout="wide")

# --- GİRİŞ SİSTEMİ ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Sisteme Giriş")
    st.info("Lütfen devam etmek için kullanıcı bilgilerinizi girin.")
    with st.form("login_form"):
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")
        if submit:
            if kullanici_adi.strip() == "Cuma Babacan" and sifre.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı giriş!")
    st.stop()

# --- API AYARI ---
API_KEY = "AIzaSyDPC11iFGbI6ifnbV6pAgsYNjpJgkAMKw4"
DB_FILE = "cuma_ajans.db"

# --- HATA ÇEVİRİ SÖZLÜĞÜ ---
hata_sozlugu = {
    "Image elements do not have [alt] attributes": "Görsellerde alt metni eksik.",
    "Background and foreground colors do not have a sufficient contrast ratio": "Renk kontrastı yetersiz.",
    "Buttons do not have an accessible name": "Butonların erişilebilir adı yok.",
    "Links do not have a discernible name": "Linklerin anlaşılır adı yok.",
    "Document does not have a main landmark": "Ana içerik (main) etiketi eksik.",
    "<html> element does not have a [lang] attribute": "HTML dil özelliği (lang) eksik.",
    "Heading elements are not in a sequentially-descending order": "Başlık etiketleri (H1, H2) sıralı değil."
}

def hatayi_cevir(hata_ingilizce):
    for key, val in hata_sozlugu.items():
        if key.lower() in hata_ingilizce.lower(): return val
    return f"{hata_ingilizce} (Manuel incelenmeli)"

# --- VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    firma_adi TEXT, sektor TEXT, eposta TEXT, 
                    durum TEXT DEFAULT 'Yeni Eklendi', notlar TEXT, tarih TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri TEXT, domain TEXT, anlasilan_ucret REAL, 
                    durum TEXT DEFAULT 'Devam Ediyor', baslangic_tarihi TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri TEXT, miktar REAL, tarih TEXT, aciklama TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- VERİTABANI FONKSİYONLARI ---
def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_data(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- ARAYÜZ ---
st.title("🎯 Erişilebilirlik Danışmanlığı İşletim Sistemi")
st.sidebar.success("Giriş Yapıldı: Cuma Babacan")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Özet Paneli", 
    "👥 Müşteri Adayları (CRM)", 
    "💼 Aktif Projeler", 
    "🔍 Erişilebilirlik Tarayıcı",
    "💰 Kazançlar"
])

# --- TAB 1: ÖZET PANELİ ---
with tab1:
    st.header("Genel Durum")
    df_projects = fetch_data("SELECT * FROM projects")
    df_leads = fetch_data("SELECT * FROM leads")
    df_earnings = fetch_data("SELECT * FROM earnings")
    
    aktif_projeler = len(df_projects[df_projects['durum'] == 'Devam Ediyor']) if not df_projects.empty else 0
    tamamlanan_projeler = len(df_projects[df_projects['durum'] == 'Tamamlandı']) if not df_projects.empty else 0
    toplam_kazanc = df_earnings['miktar'].sum() if not df_earnings.empty else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Müşteri Adayı", len(df_leads))
    c2.metric("Aktif Projeler", aktif_projeler)
    c3.metric("Tamamlanan Projeler", tamamlanan_projeler)
    c4.metric("Toplam Kazanç", f"{toplam_kazanc:,.2f} TL")

    if not df_leads.empty:
        st.subheader("Müşteri Adayı Hunisi (CRM)")
        st.bar_chart(df_leads['durum'].value_counts(), color="#00C853")

# --- TAB 2: MÜŞTERİ ADAYLARI (CRM) ---
with tab2:
    st.header("Müşteri Adayları ve İletişim Takibi")
    with st.expander("➕ Yeni Aday Ekle"):
        with st.form("add_lead", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            firma = c1.text_input("Firma Adı")
            sektor = c2.selectbox("Sektör", ["Otel", "Klinik", "E-Ticaret", "Restoran", "Ajans", "Diğer"])
            eposta = c3.text_input("E-posta")
            notlar = st.text_input("Notlar (Örn: E-posta gönderildi)")
            if st.form_submit_button("Kaydet") and firma:
                execute_query("INSERT INTO leads (firma_adi, sektor, eposta, notlar, tarih) VALUES (?, ?, ?, ?, ?)", 
                              (firma, sektor, eposta, notlar, datetime.now().strftime("%Y-%m-%d")))
                st.success("Aday eklendi!")
                st.rerun()

    df_leads = fetch_data("SELECT * FROM leads ORDER BY id DESC")
    if not df_leads.empty:
        for _, row in df_leads.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.subheader(row['firma_adi'])
                    st.caption(f"📧 {row['eposta']} | 🏢 {row['sektor']} | 📅 {row['tarih']}")
                    if row['notlar']: st.info(f"Not: {row['notlar']}")
                with c2:
                    durumlar = ["Yeni Eklendi", "E-posta Gönderildi", "Görüşme Yapıldı", "Müşteri Oldu", "Reddedildi"]
                    idx = durumlar.index(row['durum']) if row['durum'] in durumlar else 0
                    yeni_durum = st.selectbox("Durum", durumlar, index=idx, key=f"lead_{row['id']}")
                    if yeni_durum != row['durum']:
                        execute_query("UPDATE leads SET durum = ? WHERE id = ?", (yeni_durum, row['id']))
                        st.rerun()
                with c3:
                    if st.button("🗑️ Sil", key=f"del_lead_{row['id']}"):
                        execute_query("DELETE FROM leads WHERE id = ?", (row['id'],))
                        st.rerun()

# --- TAB 3: AKTİF PROJELER ---
with tab3:
    st.header("Aktif İşler ve Projeler")
    with st.expander("➕ Yeni Proje Ekle"):
        with st.form("add_proj", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            m = c1.text_input("Müşteri Adı")
            d = c2.text_input("Domain (ornek.com)")
            u = c3.number_input("Anlaşılan Ücret (TL)", min_value=0.0)
            if st.form_submit_button("Projeyi Başlat") and m and d:
                execute_query("INSERT INTO projects (musteri, domain, anlasilan_ucret, baslangic_tarihi) VALUES (?, ?, ?, ?)", 
                              (m, d, u, datetime.now().strftime("%Y-%m-%d")))
                st.success("Proje eklendi!")
                st.rerun()

    df_proj = fetch_data("SELECT * FROM projects ORDER BY id DESC")
    if not df_proj.empty:
        for _, row in df_proj.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.subheader(f"{row['musteri']} - {row['domain']}")
                    st.caption(f"💰 {row['anlasilan_ucret']} TL | 📅 {row['baslangic_tarihi']}")
                with c2:
                    durumlar = ["Devam Ediyor", "Rapor Teslim Edildi", "Tamamlandı", "İptal"]
                    idx = durumlar.index(row['durum']) if row['durum'] in durumlar else 0
                    yd = st.selectbox("Durum", durumlar, index=idx, key=f"proj_{row['id']}")
                    if yd != row['durum']:
                        execute_query("UPDATE projects SET durum = ? WHERE id = ?", (yd, row['id']))
                        st.rerun()
                with c3:
                    if st.button("🗑️ Sil", key=f"del_proj_{row['id']}"):
                        execute_query("DELETE FROM projects WHERE id = ?", (row['id'],))
                        st.rerun()

# --- TAB 4: ERİŞİLEBİLİRLİK TARAYICI (GERÇEK API) ---
with tab4:
    st.header("Gerçek Zamanlı Erişilebilirlik Taraması")
    st.write("Bu araç, Google PageSpeed API kullanarak sitenin **gerçek** erişilebilirlik hatalarını bulur.")
    
    with st.form("scan_form"):
        url = st.text_input("Taranacak Site (örn: ornek.com)")
        if st.form_submit_button("Siteyi Tara"):
            if url:
                if not url.startswith("http"): url = "https://" + url
                with st.spinner("Google API üzerinden taranıyor..."):
                    try:
                        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&category=accessibility&key={API_KEY}"
                        r = requests.get(api_url, timeout=30)
                        if r.status_code == 200:
                            data = r.json()
                            # API bazen boş skor döndürebilir, kontrol ediyoruz
                            score_raw = data.get('lighthouseResult', {}).get('categories', {}).get('accessibility', {}).get('score')
                            
                            if score_raw is not None:
                                score = score_raw * 100
                                audits = data['lighthouseResult']['audits']
                                failures = [d['title'] for a, d in audits.items() if d.get('score') == 0]
                                
                                st.metric("Erişilebilirlik Skoru", f"{score:.0f}/100")
                                st.metric("Kritik Hata Sayısı", len(failures))
                                
                                st.write("### Tespit Edilen Hatalar ve Çözümleri (Müşteriye Gönderilecek Rapor)")
                                rapor_metni = f"**{url}** adresinin erişilebilirlik taraması tamamlandı. Skor: **{score:.0f}/100**\n\n"
                                rapor_metni += "**Tespit Edilen Hatalar:**\n"
                                
                                if failures:
                                    for f in failures:
                                        ceviri = hatayi_cevir(f)
                                        st.warning(ceviri)
                                        rapor_metni += f"- {ceviri}\n"
                                else:
                                    st.success("Harika! Bu sayfada kritik bir erişilebilirlik hatası bulunamadı.")
                                    rapor_metni += "- Kritik hata bulunamadı.\n"
                                
                                st.write("---")
                                st.write("📋 **Raporu Kopyala (Müşteriye göndermek için):**")
                                st.code(rapor_metni, language="text")
                            else:
                                st.error("Google API bu site için bir skor döndüremedi. Lütfen URL'yi kontrol edin veya siteyi manuel test edin.")
                        else:
                            st.error(f"Site taranamadı. HTTP Kodu: {r.status_code}")
                    except Exception as e:
                        st.error(f"Bağlantı Hatası: {e}")

# --- TAB 5: KAZANÇLAR ---
with tab5:
    st.header("Finansal Takip")
    with st.expander("➕ Tahsilat / Kazanç Ekle"):
        with st.form("add_money", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            m = c1.text_input("Kimden Alındı?")
            miktar = c2.number_input("Miktar (TL)", min_value=0.0)
            aciklama = c3.text_input("Açıklama")
            if st.form_submit_button("Kaydet") and m and miktar > 0:
                execute_query("INSERT INTO earnings (musteri, miktar, aciklama, tarih) VALUES (?, ?, ?, ?)", 
                              (m, miktar, aciklama, datetime.now().strftime("%Y-%m-%d")))
                st.success("Kazanç eklendi!")
                st.rerun()

    df_money = fetch_data("SELECT * FROM earnings ORDER BY id DESC")
    if not df_money.empty:
        st.dataframe(df_money[['tarih', 'musteri', 'miktar', 'aciklama']], use_container_width=True, hide_index=True)
        st.metric("Toplam Tahsil Edilen", f"{df_money['miktar'].sum():,.2f} TL")
    else:
        st.info("Henüz kazanç kaydı yok.")
