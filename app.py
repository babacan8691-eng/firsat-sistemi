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
                    firma_adi TEXT, sektor TEXT, eposta TEXT, website TEXT,
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
            c1, c2 = st.columns(2)
            firma = c1.text_input("Firma Adı")
            sektor = c2.selectbox("Sektör", ["Otel", "Klinik", "E-Ticaret", "Restoran", "Ajans", "Diğer"])
            c3, c4 = st.columns(2)
            eposta = c3.text_input("E-posta")
            website = c4.text_input("Website (örn: ornek.com)") # Website alanı eklendi
            notlar = st.text_input("Notlar")
            if st.form_submit_button("Kaydet") and firma:
                execute_query("INSERT INTO leads (firma_adi, sektor, eposta, website, notlar, tarih) VALUES (?, ?, ?, ?, ?, ?)", 
                              (firma, sektor, eposta, website, notlar, datetime.now().strftime("%Y-%m-%d")))
                st.success("Aday eklendi!")
                st.rerun()

    df_leads = fetch_data("SELECT * FROM leads ORDER BY id DESC")
    if not df_leads.empty:
        for _, row in df_leads.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.subheader(row['firma_adi'])
                    web_goster = row['website'] if row['website'] else "Web sitesi girilmemiş"
                    st.caption(f"📧 {row['eposta']} | 🌐 {web_goster} | 🏢 {row['sektor']}")
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

# --- TAB 4: ERİŞİLEBİLİRLİK TARAYICI (LİSTEDEN SEÇMELİ) ---
with tab4:
    st.header("Gerçek Zamanlı Erişilebilirlik Taraması")
    st.write("Google PageSpeed API kullanarak sitenin **gerçek** erişilebilirlik hatalarını bulur.")
    
    # Tarama kaynağını seçme
    kaynak = st.radio("Neyi taramak istiyorsun?", ["Kayıtlı Projelerden Seç", "Müşteri Adaylarından Seç", "Manuel URL Gir"], horizontal=True)
    
    taranacak_url = ""
    
    if kaynak == "Kayıtlı Projelerden Seç":
        df_proj = fetch_data("SELECT id, musteri, domain FROM projects")
        if not df_proj.empty:
            proj_secenekleri = df_proj.apply(lambda x: f"{x['id']} - {x['musteri']} ({x['domain']})", axis=1).tolist()
            secim = st.selectbox("Proje Seç", proj_secenekleri)
            secilen_id = int(secim.split(" - ")[0])
            taranacak_url = df_proj[df_proj['id'] == secilen_id]['domain'].values[0]
        else:
            st.warning("Sistemde kayıtlı proje yok.")
            
    elif kaynak == "Müşteri Adaylarından Seç":
        df_leads = fetch_data("SELECT id, firma_adi, website FROM leads")
        # Sadece website girilmiş olanları filtrele
        df_leads_valid = df_leads[df_leads['website'].notna() & (df_leads['website'] != "")]
        if not df_leads_valid.empty:
            lead_secenekleri = df_leads_valid.apply(lambda x: f"{x['id']} - {x['firma_adi']} ({x['website']})", axis=1).tolist()
            secim = st.selectbox("Aday Seç", lead_secenekleri)
            secilen_id = int(secim.split(" - ")[0])
            taranacak_url = df_leads_valid[df_leads_valid['id'] == secilen_id]['website'].values[0]
        else:
            st.warning("Web sitesi girilmiş müşteri adayı bulunamadı. (Lütfen CRM sekmesinden ekleyin).")

    else: # Manuel URL Gir
        taranacak_url = st.text_input("Taranacak Site (örn: ornek.com)")

    st.divider()

    if st.button("Siteyi Tara", type="primary"):
        if taranacak_url:
            # URL formatını düzelt
            if not taranacak_url.startswith("http"): 
                taranacak_url = "https://" + taranacak_url
                
            with st.spinner(f"{taranacak_url} taranıyor..."):
                try:
                    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={taranacak_url}&category=accessibility&key={API_KEY}"
                    r = requests.get(api_url, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        score_raw = data.get('lighthouseResult', {}).get('categories', {}).get('accessibility', {}).get('score')
                        
                        if score_raw is not None:
                            score = score_raw * 100
                            audits = data['lighthouseResult']['audits']
                            failures = [d['title'] for a, d in audits.items() if d.get('score') == 0]
                            
                            col1, col2 = st.columns(2)
                            col1.metric("Erişilebilirlik Skoru", f"{score:.0f}/100")
                            col2.metric("Kritik Hata Sayısı", len(failures))
                            
                            st.write(f"### {taranacak_url} için Tespit Edilen Hatalar")
                            
                            rapor_metni = f"**{taranacak_url}** adresinin erişilebilirlik taraması tamamlandı. Skor: **{score:.0f}/100**\n\n"
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
                            st.error("Google API bu site için bir skor döndüremedi. URL'yi kontrol edin.")
                    else:
                        st.error(f"Site taranamadı. HTTP Kodu: {r.status_code}")
                except Exception as e:
                    st.error(f"Bağlantı Hatası: {e}")
        else:
            st.warning("Lütfen geçerli bir site adresi girin veya listeden seçim yapın.")

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
