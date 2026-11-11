import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Küresel Test Platformları Yönetim Paneli", layout="wide")

# --- KİMLİK DOĞRULAMA ---
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
                st.error("Hatalı giriş! Lütfen kullanıcı adınızı ve şifrenizi kontrol edin.")
    st.stop()

# --- E-POSTA AYARLARI ---
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"
DB_FILE = "tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS platforms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT NOT NULL,
                    website TEXT,
                    contact_email TEXT,
                    payment_method TEXT,
                    application_date TEXT,
                    status TEXT DEFAULT 'Beklemede',
                    notes TEXT
                )''')
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

def seed_platforms():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM platforms")
    if c.fetchone()[0] == 0:
        platforms = [
            ("AccessWorks (Knowbility)", "https://knowbility.org", "aw-services@knowbility.org", "PayPal"),
            ("Testlio", "https://testlio.com", "hello@testlio.com", "Payoneer"),
            ("Applause (uTest)", "https://applause.com", "support@applause.com", "PayPal"),
            ("Respondent.io", "https://respondent.io", "support@respondent.io", "PayPal"),
            ("Fable", "https://makeitfable.com", "hello@makeitfable.com", "PayPal"),
            ("User Interviews", "https://userinterviews.com", "support@userinterviews.com", "PayPal"),
            ("See Me Please", "https://seemeplease.com", "hello@seemeplease.com", "PayPal"),
            ("Userlytics", "https://userlytics.com", "support@userlytics.com", "PayPal"),
            ("Userbrain", "https://userbrain.net", "hello@userbrain.net", "PayPal"),
            ("TestingTime", "https://testingtime.com", "hello@testingtime.com", "PayPal"),
        ]
        for name, web, mail, pay in platforms:
            c.execute("INSERT INTO platforms (platform_name, website, contact_email, payment_method, application_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, web, mail, pay, datetime.now().strftime("%Y-%m-%d"), "Beklemede"))
        conn.commit()
    conn.close()

seed_platforms()

def get_platforms():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM platforms", conn)
    conn.close()
    return df

def add_platform(name, website, contact_email, payment, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO platforms (platform_name, website, contact_email, payment_method, application_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (name, website, contact_email, payment, datetime.now().strftime("%Y-%m-%d"), notes))
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
    c.execute("INSERT INTO earnings (platform_id, amount, currency, date, notes) VALUES (?, ?, ?, ?, ?)",
              (platform_id, amount, currency, datetime.now().strftime("%Y-%m-%d"), notes))
    conn.commit()
    conn.close()

def get_earnings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT e.id, p.platform_name, e.amount, e.currency, e.date, e.notes
        FROM earnings e JOIN platforms p ON e.platform_id = p.id ORDER BY e.date DESC
    """, conn)
    conn.close()
    return df

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADRESI
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_ADRESI, GMAIL_SIFRESI)
        server.send_message(msg)
        server.quit()
        return True, "✅ E-posta başarıyla gönderildi."
    except Exception as e:
        return False, f"❌ Gönderim hatası: {str(e)}"

# --- ARAYÜZ ---
st.title("🎯 Küresel Test Platformları - Yönetim Paneli")
st.sidebar.success("Giriş Yapıldı: Cuma Babacan")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Platformlar", "💰 Kazançlar", "📧 Başvuru & E-posta", "📊 Genel Özet"])

with tab1:
    st.header("Platform Listesi & Başvuru Durumları")
    with st.expander("➕ Yeni Platform Ekle"):
        with st.form("add_platform_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("Platform Adı")
            website = col2.text_input("Web Sitesi")
            contact_email = col3.text_input("İletişim E-postası")
            col4, col5 = st.columns(2)
            payment = col4.selectbox("Ödeme Yöntemi", ["PayPal", "Payoneer", "Banka Havalesi", "Wise", "Diğer"])
            notes = col5.text_input("Notlar")
            if st.form_submit_button("Platformu Kaydet") and name:
                add_platform(name, website, contact_email, payment, notes)
                st.success("✅ Eklendi!")
                st.rerun()

    df_platforms = get_platforms()
    if not df_platforms.empty:
        for _, row in df_platforms.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.subheader(row['platform_name'])
                    st.caption(f"📧 {row['contact_email']} | 🌐 {row['website']} | 💳 {row['payment_method']}")
                with c2:
                    opts = ["Beklemede", "Kabul Edildi", "Reddedildi", "İş Alındı"]
                    idx = opts.index(row['status']) if row['status'] in opts else 0
                    new_stat = st.selectbox("Durum", opts, index=idx, key=f"s_{row['id']}")
                    if new_stat != row['status']:
                        update_status(row['id'], new_stat)
                        st.rerun()
                with c3:
                    if st.button("🗑️ Sil", key=f"d_{row['id']}"):
                        delete_platform(row['id'])
                        st.rerun()
    else:
        st.info("Henüz platform eklenmemiş.")

with tab2:
    st.header("Kazanç Takibi")
    df_platforms = get_platforms()
    if not df_platforms.empty:
        with st.expander("➕ Yeni Kazanç Ekle"):
            with st.form("add_earning_form", clear_on_submit=True):
                opts = df_platforms.apply(lambda x: f"{x['id']} - {x['platform_name']}", axis=1).tolist()
                sel = st.selectbox("Platform", opts)
                col1, col2 = st.columns(2)
                amount = col1.number_input("Miktar", min_value=0.0, step=0.01)
                currency = col2.selectbox("Para Birimi", ["USD", "EUR", "TL", "GBP"])
                notes = st.text_input("Açıklama")
                if st.form_submit_button("Kaydet") and amount > 0:
                    add_earning(int(sel.split(" - ")[0]), amount, currency, notes)
                    st.success("✅ Kazanç eklendi!")
                    st.rerun()
    df_earnings = get_earnings()
    if not df_earnings.empty:
        st.dataframe(df_earnings, use_container_width=True, hide_index=True)
    else:
        st.info("Kayıt yok.")

with tab3:
    st.header("📧 E-posta Gönderimi")
    df_platforms = get_platforms()
    if not df_platforms.empty:
        opts = df_platforms.apply(lambda x: f"{x['platform_name']} ({x['contact_email']})" if x['contact_email'] else x['platform_name'], axis=1).tolist()
        sel = st.selectbox("Platform Seç", opts)
        sel_name = sel.split(" (")[0]
        target = df_platforms[df_platforms['platform_name'] == sel_name]
        to_email = st.text_input("Alıcı E-posta", value=target['contact_email'].values[0] if not target.empty and pd.notna(target['contact_email'].values[0]) else "")
        subject = st.text_input("Konu", value="Application for Tester Panel - Cuma Babacan")
        body = st.text_area("Mesaj", value="Hello Team,\n\nMy name is Cuma Babacan. I am a person with disabilities based in Turkey and a daily screen reader user...", height=250)
        if st.button("🚀 Gönder"):
            if to_email:
                success, msg = send_email(to_email, subject, body)
                st.success(msg) if success else st.error(msg)
    else:
        st.warning("Önce platform ekleyin.")

with tab4:
    st.header("Genel Özet")
    df_p = get_platforms()
    df_e = get_earnings()
    c1, c2, c3 = st.columns(3)
    c1.metric("Başvurulan", len(df_p))
    c2.metric("Kabul Edilen", len(df_p[df_p['status'] == 'Kabul Edildi']) if not df_p.empty else 0)
    c3.metric("Toplam Kazanç", f"{df_e['amount'].sum():.2f}" if not df_e.empty else "0.00")
    if not df_p.empty:
        st.bar_chart(df_p['status'].value_counts())
