import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Başvuru & Kazanç Takip Paneli", layout="wide")

# --- VERİTABANI KURULUMU ---
DB_FILE = "tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Platformlar Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS platforms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT NOT NULL,
                    website TEXT,
                    payment_method TEXT,
                    application_date TEXT,
                    status TEXT DEFAULT 'Beklemede',
                    notes TEXT
                )''')
    # Kazançlar Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_id INTEGER,
                    amount REAL,
                    currency TEXT,
                    date TEXT,
                    notes TEXT,
                    FOREIGN KEY(platform_id) REFERENCES platforms(id)
                )''')
    conn.commit()
    conn.close()

init_db()

# --- VERİTABANI YARDIMCI FONKSİYONLARI ---
def get_platforms():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM platforms", conn)
    conn.close()
    return df

def add_platform(name, website, payment, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO platforms (platform_name, website, payment_method, application_date, notes) VALUES (?, ?, ?, ?, ?)",
              (name, website, payment, date_str, notes))
    conn.commit()
    conn.close()

def update_status(platform_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE platforms SET status = ? WHERE id = ?", (new_status, platform_id))
    conn.commit()
    conn.close()

def delete_platform(platform_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
    conn.commit()
    conn.close()

def add_earning(platform_id, amount, currency, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO earnings (platform_id, amount, currency, date, notes) VALUES (?, ?, ?, ?, ?)",
              (platform_id, amount, currency, date_str, notes))
    conn.commit()
    conn.close()

def get_earnings():
    conn = sqlite3.connect(DB_FILE)
    query = """
    SELECT e.id, p.platform_name, e.amount, e.currency, e.date, e.notes
    FROM earnings e
    JOIN platforms p ON e.platform_id = p.id
    ORDER BY e.date DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- ARAYÜZ ---
st.title("🎯 Küresel Test Platformları - Başvuru & Kazanç Takip Sistemi")
st.markdown("Bu panel, engelli bir birey olarak başvurduğunuz küresel test platformlarını, başvuru durumlarınızı ve kazançlarınızı tek bir yerden yönetmenizi sağlar.")

tab1, tab2, tab3 = st.tabs(["📋 Platformlar & Başvurular", "💰 Kazançlar", "📊 Genel Özet"])

# --- TAB 1: PLATFORMLAR ---
with tab1:
    st.header("Platform Listesi")
    
    # Yeni platform ekleme formu
    with st.expander("➕ Yeni Platform Ekle"):
        with st.form("add_platform_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Platform Adı (örn: Testlio, uTest)")
            website = col2.text_input("Web Sitesi (örn: testlio.com)")
            
            col3, col4 = st.columns(2)
            payment = col3.selectbox("Ödeme Yöntemi", ["PayPal", "Payoneer", "Banka Havalesi", "Wise", "Diğer"])
            notes = col4.text_input("Notlar (isteğe bağlı)")
            
            submitted = st.form_submit_button("Platformu Kaydet")
            if submitted:
                if name:
                    add_platform(name, website, payment, notes)
                    st.success(f"✅ {name} başarıyla eklendi!")
                    st.rerun()
                else:
                    st.error("Platform adı zorunludur.")

    # Mevcut platformları listeleme
    df_platforms = get_platforms()
    if not df_platforms.empty:
        for index, row in df_platforms.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.subheader(f"{row['platform_name']}")
                    st.caption(f"🌐 {row['website']} | 💳 {row['payment_method']} | 📅 Başvuru: {row['application_date']}")
                    if row['notes']:
                        st.info(f"Not: {row['notes']}")
                
                with col2:
                    # Durum güncelleme
                    status_options = ["Beklemede", "Kabul Edildi", "Reddedildi", "İş Alındı"]
                    current_status = row['status']
                    try:
                        status_idx = status_options.index(current_status)
                    except ValueError:
                        status_idx = 0
                    
                    new_status = st.selectbox(
                        "Durum", 
                        status_options, 
                        index=status_idx, 
                        key=f"status_{row['id']}"
                    )
                    if new_status != current_status:
                        update_status(row['id'], new_status)
                        st.rerun()

                with col3:
                    if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                        delete_platform(row['id'])
                        st.rerun()
    else:
        st.info("Henüz platform eklenmemiş. Yukarıdaki formu kullanarak ilk platformunuzu ekleyin.")

# --- TAB 2: KAZANÇLAR ---
with tab2:
    st.header("Kazanç Takibi")
    
    df_platforms = get_platforms()
    if not df_platforms.empty:
        with st.expander("➕ Yeni Kazanç Ekle"):
            with st.form("add_earning_form"):
                platform_options = df_platforms[['id', 'platform_name']].apply(lambda x: f"{x['id']} - {x['platform_name']}", axis=1).tolist()
                selected_platform = st.selectbox("Hangi Platformdan Kazanç Sağlandı?", platform_options)
                
                col1, col2 = st.columns(2)
                amount = col1.number_input("Miktar", min_value=0.0, step=0.01, format="%.2f")
                currency = col2.selectbox("Para Birimi", ["USD", "EUR", "TL", "GBP"])
                
                notes = st.text_input("Açıklama (örn: Haftalık test görevi)")
                
                submitted = st.form_submit_button("Kazancı Kaydet")
                if submitted:
                    if amount > 0:
                        platform_id = int(selected_platform.split(" - ")[0])
                        add_earning(platform_id, amount, currency, notes)
                        st.success("✅ Kazanç başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.error("Miktar 0'dan büyük olmalıdır.")
    else:
        st.warning("Kazanç ekleyebilmek için önce Platformlar sekmesinden en az bir platform eklemelisiniz.")

    # Kazanç geçmişi
    df_earnings = get_earnings()
    if not df_earnings.empty:
        st.subheader("Kazanç Geçmişi")
        st.dataframe(
            df_earnings,
            column_config={
                "platform_name": "Platform",
                "amount": st.column_config.NumberColumn("Miktar", format="%.2f"),
                "currency": "Para Birimi",
                "date": "Tarih",
                "notes": "Açıklama"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Henüz kazanç kaydı bulunmamaktadır.")

# --- TAB 3: GENEL ÖZET ---
with tab3:
    st.header("Genel Durum Özeti")
    
    df_platforms = get_platforms()
    df_earnings = get_earnings()
    
    total_platforms = len(df_platforms)
    approved_platforms = len(df_platforms[df_platforms['status'] == 'Kabul Edildi']) if not df_platforms.empty else 0
    total_earnings = df_earnings['amount'].sum() if not df_earnings.empty else 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Başvurulan Platform", total_platforms)
    col2.metric("Kabul Edilen Platform Sayısı", approved_platforms)
    col3.metric("Toplam Kazanç (Tüm Para Birimleri)", f"{total_earnings:.2f}")
    
    if not df_platforms.empty:
        st.subheader("Başvuru Durumları")
        status_counts = df_platforms['status'].value_counts()
        st.bar_chart(status_counts, color="#00C853")

st.sidebar.markdown("---")
st.sidebar.info("💡 **İpucu:** Her yeni platform başvurusu yaptığınızda buraya ekleyin. Durumunu 'Beklemede' olarak işaretleyin ve yanıt geldikçe güncelleyin. Kazanç elde ettikçe 'Kazançlar' sekmesine kaydedin.")
