import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import date

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="İhale Takip Paneli", page_icon="📋", layout="wide")

# --- VERİTABANI AYARLARI ---
DB_NAME = "sistem.db"

def get_db():
    """Veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Gerekli tabloları oluşturur."""
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS ilanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kurum TEXT, baslik TEXT, ilanNo TEXT, kaynak TEXT, link TEXT,
            ilanTarihi TEXT, sonTarih TEXT, notlar TEXT, durum TEXT, sartname TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS dilekceler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kurum TEXT, konu TEXT, tarih TEXT, durum TEXT, notlar TEXT
        )''')

# Uygulama ilk çalıştığında veritabanını hazırla
if not os.path.exists(DB_NAME):
    init_db()

# --- KULLANICI GİRİŞİ (AUTHENTICATION) ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

def giris_ekrani():
    """Kullanıcı adı ve şifre ile giriş ekranı."""
    st.title("🔐 Sisteme Giriş")
    with st.form("login_form"):
        kullanici = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")

        if submit:
            # BELİRLEDİĞİNİZ KULLANICI ADI VE ŞİFRE
            if kullanici == "Cuma Babacan" and sifre == "784512":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")

# Giriş yapılmamışsa giriş ekranını göster ve uygulamayı durdur
if not st.session_state.giris_yapildi:
    giris_ekrani()
    st.stop()

# --- ANA UYGULAMA (Giriş yapıldıktan sonra) ---

# Çıkış butonu
if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.title("📋 İhale & Fırsat Takip Sistemi")

# Sekmeler
tab1, tab2, tab3 = st.tabs(["📌 İlanlar", "📄 Dilekçeler", "ℹ️ Kaynaklar"])

with tab1:
    st.subheader("Yeni İlan Ekle")
    with st.form("ilan_ekle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            kurum = st.text_input("Kurum")
            baslik = st.text_input("İlan Başlığı")
            sonTarih = st.date_input("Son Başvuru Tarihi", value=date.today())
        with col2:
            link = st.text_input("İlan Linki (URL)")
            notlar = st.text_area("Notlar")
        
        if st.form_submit_button("İlanı Kaydet"):
            if kurum and baslik:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO ilanlar (kurum, baslik, sonTarih, link, notlar, durum) VALUES (?, ?, ?, ?, ?, ?)",
                        (kurum, baslik, sonTarih.isoformat(), link, notlar, "İncelenecek")
                    )
                st.success("İlan başarıyla eklendi!")
                st.rerun()
            else:
                st.warning("Kurum ve Başlık alanları zorunludur.")

    st.subheader("Kayıtlı İlanlar")
    
    # Veritabanından ilanları çek
    with get_db() as conn:
        df = pd.read_sql_query("SELECT * FROM ilanlar ORDER BY sonTarih ASC", conn)

    if not df.empty:
        # Tabloyu göster
        st.dataframe(
            df[["id", "kurum", "baslik", "sonTarih", "durum", "link"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "link": st.column_config.LinkColumn("İlan Linki"),
                "sonTarih": st.column_config.DateColumn("Son Tarih", format="DD/MM/YYYY")
            }
        )

        # Silme işlemi
        st.subheader("İlan Sil")
        silinecek_id = st.selectbox(
            "Silmek istediğiniz ilanı seçin",
            options=df["id"].tolist(),
            format_func=lambda x: f"ID {x} - {df[df['id']==x]['baslik'].values[0]}"
        )
        if st.button("Seçili İlanı Sil", type="primary"):
            with get_db() as conn:
                conn.execute("DELETE FROM ilanlar WHERE id = ?", (silinecek_id,))
            st.success("İlan silindi.")
            st.rerun()
    else:
        st.info("Henüz kayıtlı ilan bulunmamaktadır.")

with tab2:
    st.subheader("Yeni Dilekçe / Yazışma Kaydı")
    with st.form("dilekce_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_kurum = st.text_input("Kurum")
            d_konu = st.text_input("Konu")
        with col2:
            d_tarih = st.date_input("Gönderim Tarihi", value=date.today())
            d_durum = st.selectbox("Durum", ["Hazırlanıyor", "Gönderildi", "Cevap Bekleniyor", "Cevap Geldi", "Olumsuz"])
        
        d_not = st.text_area("Not / Cevap Özeti")

        if st.form_submit_button("Kaydet"):
            if d_kurum and d_konu:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO dilekceler (kurum, konu, tarih, durum, notlar) VALUES (?, ?, ?, ?, ?)",
                        (d_kurum, d_konu, d_tarih.isoformat(), d_durum, d_not)
                    )
                st.success("Dilekçe kaydı eklendi!")
                st.rerun()
            else:
                st.warning("Kurum ve Konu alanları zorunludur.")

    # Dilekçeleri listele
    with get_db() as conn:
        df_dilekce = pd.read_sql_query("SELECT * FROM dilekceler ORDER BY tarih DESC", conn)
    
    if not df_dilekce.empty:
        st.dataframe(df_dilekce, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz kayıtlı dilekçe bulunmamaktadır.")

with tab3:
    st.subheader("Takip Edilecek Kaynaklar")
    st.markdown("""
    - [Gaziantep Büyükşehir Belediyesi İhale İlanları](https://www.gaziantep.bel.tr/ihale-ilanlari)
    - [Şahinbey Belediyesi İhale İlanları](https://www.sahinbey.bel.tr/ihale-ilanlari)
    - [Şehitkamil Belediyesi İhale İlanları](https://www.sehitkamil.bel.tr/ihale-ilanlari)
    - [EKAP (Elektronik Kamu Alımları Platformu)](https://ekap.kik.gov.tr)
    - [Kamu İlanları (ilan.gov.tr)](https://www.ilan.gov.tr)
    """)

    st.subheader("Başvuruda İstenebilecek Belgeler")
    st.info("""
    - Engelli sağlık kurulu raporu (%40 ve üzeri)
    - Vergi indirimi / engellilik indirimi yazısı
    - SGK emeklilik belgesi
    - Nüfus kayıt örneği, yerleşim yeri belgesi, kimlik fotokopisi
    - Vergi levhası / ticaret sicil (şartnamede istenirse)
    - Geçici teminat (şartnamede belirtilen tutar)
    - Şartname alındı makbuzu
    """)
