import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="İhale & Fırsat Takip Sistemi", page_icon="📋", layout="wide")

# --- VERİTABANI AYARLARI ---
DB_NAME = "sistem.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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

if not os.path.exists(DB_NAME):
    init_db()

# --- KULLANICI GİRİŞİ ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

def giris_ekrani():
    st.title("🔐 Sisteme Giriş")
    with st.form("login_form"):
        kullanici = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")
        
        if submit:
            # Görünmez boşlukları temizler ve büyük/küçük harf duyarsız yapar
            if kullanici.strip().lower() == "cuma babacan" and sifre.strip() == "784512":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")

if not st.session_state.giris_yapildi:
    giris_ekrani()
    st.stop()

# --- ANA UYGULAMA ---
if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.giris_yapildi = False
    st.rerun()

st.title("📋 İhale & Fırsat Takip Sistemi")
st.markdown("Sistem her gün otomatik olarak güncellenmektedir. Aşağıdan ilanları takip edebilirsiniz.")

tab1, tab2, tab3 = st.tabs(["📌 İlanlar", "📄 Dilekçeler", "ℹ️ Kaynaklar & Belgeler"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Yeni İlan Ekle")
        with st.form("ilan_ekle_form", clear_on_submit=True):
            kurum = st.text_input("Kurum")
            baslik = st.text_input("İlan Başlığı")
            sonTarih = st.date_input("Son Başvuru Tarihi", value=date.today())
            link = st.text_input("İlan Linki (URL)")
            notlar = st.text_area("Notlar")
            
            if st.form_submit_button("İlanı Kaydet", use_container_width=True):
                if kurum and baslik:
                    with get_db() as conn:
                        conn.execute(
                            "INSERT INTO ilanlar (kurum, baslik, sonTarih, link, notlar, durum) VALUES (?, ?, ?, ?, ?, ?)",
                            (kurum, baslik, sonTarih.isoformat(), link, notlar, "İncelenecek")
                        )
                    st.success("İlan eklendi!")
                    st.rerun()
                else:
                    st.warning("Kurum ve Başlık zorunludur.")

    with col2:
        st.subheader("Kayıtlı İlanlar")
        
        # Filtreleme ve Arama Alanı
        arama = st.text_input("🔍 İlanlarda Ara (Örn: Büfe, Çay Bahçesi, Engelli)", "")
        
        with get_db() as conn:
            df = pd.read_sql_query("SELECT * FROM ilanlar ORDER BY id DESC", conn)

        if not df.empty:
            if arama:
                mask = df.apply(lambda row: arama.lower() in str(row['kurum']).lower() or 
                                            arama.lower() in str(row['baslik']).lower() or 
                                            arama.lower() in str(row['notlar']).lower(), axis=1)
                df_filtreli = df[mask]
            else:
                df_filtreli = df

            st.dataframe(
                df_filtreli[["id", "kurum", "baslik", "sonTarih", "kaynak", "durum", "link"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "link": st.column_config.LinkColumn("İlan Linki", display_text="Bağlantıya Git"),
                    "sonTarih": st.column_config.DateColumn("Son Tarih", format="DD/MM/YYYY"),
                    "kaynak": st.column_config.TextColumn("Kaynak")
                }
            )

            st.markdown("---")
            sil_col1, sil_col2 = st.columns([3, 1])
            with sil_col1:
                silinecek_id = st.selectbox(
                    "Silmek istediğiniz ilanı seçin",
                    options=df["id"].tolist(),
                    format_func=lambda x: f"[{x}] {df[df['id']==x]['baslik'].values[0]} - {df[df['id']==x]['kurum'].values[0]}"
                )
            with sil_col2:
                st.write("") 
                st.write("")
                if st.button("İlanı Sil", type="primary", use_container_width=True):
                    with get_db() as conn:
                        conn.execute("DELETE FROM ilanlar WHERE id = ?", (silinecek_id,))
                    st.success("İlan silindi.")
                    st.rerun()
        else:
            st.info("Henüz kayıtlı ilan bulunmamaktadır. Sağ üstteki 'Yönet' > 'Reboot' diyerek sistemi yenileyin.")

with tab2:
    st.subheader("Dilekçe ve Yazışma Takibi")
    with st.form("dilekce_form", clear_on_submit=True):
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            d_kurum = st.text_input("Kurum")
            d_konu = st.text_input("Konu")
        with d_col2:
            d_tarih = st.date_input("Gönderim Tarihi", value=date.today())
            d_durum = st.selectbox("Durum", ["Hazırlanıyor", "Gönderildi", "Cevap Bekleniyor", "Cevap Geldi", "Olumsuz"])
        
        d_not = st.text_area("Not / Cevap Özeti")

        if st.form_submit_button("Dilekçe Kaydı Ekle"):
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

    with get_db() as conn:
        df_dilekce = pd.read_sql_query("SELECT * FROM dilekceler ORDER BY tarih DESC", conn)
    
    if not df_dilekce.empty:
        st.dataframe(df_dilekce, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz kayıtlı dilekçe bulunmamaktadır.")

with tab3:
    st.subheader("Engelli Hakları ve İhale Avantajları")
    st.info("Önemli Bilgi: 2886 Sayılı Kanun'a göre belediyeler, kendi encümen kararlarıyla engelli bireylere özel büfe/çay bahçesi ihaleleri düzenleyebilir. Sisteme düşen ilanların şartnamelerini incelerken 'engelli', 'kontenjan', 'öncelik' kelimelerine dikkat edin.")
    
    st.subheader("Takip Edilecek Linkler")
    st.markdown("- [Gaziantep Büyükşehir Belediyesi](https://www.gaziantep.bel.tr)")
    st.markdown("- [Şahinbey Belediyesi](https://www.sahinbey.bel.tr)")
    st.markdown("- [Şehitkamil Belediyesi](https://www.sehitkamil.bel.tr)")
    st.markdown("- [EKAP İhale Arama](https://ekap.kik.gov.tr)") import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time

DB_NAME = 'sistem.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS ilanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kurum TEXT, baslik TEXT, ilanNo TEXT, kaynak TEXT, link TEXT,
            ilanTarihi TEXT, sonTarih TEXT, notlar TEXT, durum TEXT, sartname TEXT
        )''')

def ilan_ekle(kurum, baslik, link, kaynak="Otomatik"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ilanlar WHERE link = ? OR (baslik = ? AND kurum = ?)", (link, baslik, kurum))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO ilanlar (kurum, baslik, link, kaynak, durum) VALUES (?, ?, ?, ?, ?)",
                        (kurum, baslik, link, kaynak, "İncelenecek"))
            conn.commit()
            print(f"[{datetime.now()}] Yeni İlan Eklendi: {baslik}")
        else:
            print(f"[{datetime.now()}] İlan zaten mevcut: {baslik}")

def tara_gaziantep():
    print("Gaziantep taranıyor...")
    try:
        time.sleep(1)
        test_baslik = f"Otomatik Test Büfe İhalesi - {datetime.now().strftime('%d/%m/%Y')}"
        test_link = "https://www.gaziantep.bel.tr/ornek-ihale-linki"
        ilan_ekle("Gaziantep Büyükşehir Belediyesi", test_baslik, test_link)
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    init_db()
    tara_gaziantep() 
