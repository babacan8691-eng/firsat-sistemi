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
st.set_page_config(page_title="Başvuru & Kazanç Takip Paneli", layout="wide")

# --- KİMLİK DOĞRULAMA (GİRİŞ EKRANI) ---
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
            # .strip() boşlukları temizler, .lower() büyük/küçük harf duyarlılığını kaldırır
            if kullanici_adi.strip().lower() == "cuma babacan" and sifre.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı giriş! Lütfen kullanıcı adınızı ve şifrenizi kontrol edin.")
    st.stop() # Giriş yapılmadıysa kodun devamını çalıştırma

# --- E-POSTA AYARLARI ---
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"

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
                    contact_email TEXT,
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

# --- VERİTABANI FONKSİYONLARI ---
def get_platforms():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM platforms", conn)
    conn.close()
    return df

def add_platform(name, website, contact_email, payment, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO platforms (platform_name, website, contact_email, payment_method, application_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (name, website, contact_email, payment, date_str, notes))
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

# --- E-POSTA FONKSİYONLARI ---
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

def fetch_emails(limit=5):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADRESI, GMAIL_SIFRESI)
        mail.select("inbox")
        
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()[-limit:]
        
        emails = []
        for i in reversed(mail_ids):
            typ, data = mail.fetch(i, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg['Subject'] or "Konu Yok"
                    from_ = msg['From'] or "Bilinmeyen Gönderen"
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    emails.append({"from": from_, "subject": subject, "body": body[:500] + "..."})
        mail.logout()
        return emails
    except Exception as e:
        st.error(f"E-postalar okunurken hata oluştu: {e}")
        return []

# --- ARAYÜZ ---
st.title("🎯 Küresel Test Platformları - Yönetim Paneli")
st.sidebar.success(f"Giriş Yapıldı: Cuma Babacan")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Platformlar", "💰 Kazançlar", "📧 E-posta Yönetimi", "📊 Genel Özet"])

# --- TAB 1: PLATFORMLAR ---
with tab1:
    st.header("Başvurulan Platformlar")
    with st.expander("➕ Yeni Platform Ekle"):
        with st.form("add_platform_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("Platform Adı (örn: Testlio)")
            website = col2.text_input("Web Sitesi")
            contact_email = col3.text_input("İletişim E-postası")
            
            col4, col5 = st.columns(2)
            payment = col4.selectbox("Ödeme Yöntemi", ["PayPal", "Payoneer", "Banka Havalesi", "Wise", "Diğer"])
            notes = col5.text_input("Notlar (isteğe bağlı)")
            
            submitted = st.form_submit_button("Platformu Kaydet")
            if submitted and name:
                add_platform(name, website, contact_email, payment, notes)
                st.success(f"✅ {name} başarıyla eklendi!")
                st.rerun()

    df_platforms = get_platforms()
    if not df_platforms.empty:
        for index, row in df_platforms.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.subheader(row['platform_name'])
                    st.caption(f"📧 {row['contact_email']} | 🌐 {row['website']} | 💳 {row['payment_method']} | 📅 {row['application_date']}")
                    if row['notes']:
                        st.info(f"Not: {row['notes']}")
                with col2:
                    status_options = ["Beklemede", "Kabul Edildi", "Reddedildi", "İş Alındı"]
                    current_status = row['status']
                    try:
                        idx = status_options.index(current_status)
                    except ValueError:
                        idx = 0
                    new_status = st.selectbox("Durum", status_options, index=idx, key=f"st_{row['id']}")
                    if new_status != current_status:
                        update_status(row['id'], new_status)
                        st.rerun()
                with col3:
                    if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                        delete_platform(row['id'])
                        st.rerun()
    else:
        st.info("Henüz platform eklenmemiş.")

# --- TAB 2: KAZANÇLAR ---
with tab2:
    st.header("Kazanç Takibi")
    df_platforms = get_platforms()
    if not df_platforms.empty:
        with st.expander("➕ Yeni Kazanç Ekle"):
            with st.form("add_earning_form", clear_on_submit=True):
                platform_options = df_platforms.apply(lambda x: f"{x['id']} - {x['platform_name']}", axis=1).tolist()
                selected_platform = st.selectbox("Platform", platform_options)
                
                col1, col2 = st.columns(2)
                amount = col1.number_input("Miktar", min_value=0.0, step=0.01)
                currency = col2.selectbox("Para Birimi", ["USD", "EUR", "TL", "GBP"])
                notes = st.text_input("Açıklama (örn: Haftalık test ödemesi)")
                
                if st.form_submit_button("Kazancı Kaydet") and amount > 0:
                    platform_id = int(selected_platform.split(" - ")[0])
                    add_earning(platform_id, amount, currency, notes)
                    st.success("✅ Kazanç kaydedildi!")
                    st.rerun()

    df_earnings = get_earnings()
    if not df_earnings.empty:
        st.dataframe(df_earnings, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz kazanç kaydı yok.")

# --- TAB 3: E-POSTA YÖNETİMİ ---
with tab3:
    st.header("📧 E-posta Otomasyon Merkezi")
    
    col_send, col_inbox = st.columns(2)
    
    with col_send:
        st.subheader("📤 Hızlı E-posta Gönder")
        df_platforms = get_platforms()
        
        if not df_platforms.empty:
            platform_options = df_platforms.apply(lambda x: f"{x['platform_name']} ({x['contact_email']})" if x['contact_email'] else x['platform_name'], axis=1).tolist()
            selected_platform_str = st.selectbox("Platform Seç", platform_options)
            
            selected_name = selected_platform_str.split(" (")[0]
            target_email_row = df_platforms[df_platforms['platform_name'] == selected_name]
            target_email = target_email_row['contact_email'].values[0] if not target_email_row.empty and pd.notna(target_email_row['contact_email'].values[0]) else ""
            
            to_email = st.text_input("Alıcı E-posta", value=target_email)
            subject = st.text_input("Konu", value="Application for Tester Panel - Cuma Babacan")
            
            default_body = """Hello Team,

My name is Cuma Babacan. I am a person with disabilities based in Turkey and a daily screen reader user. I would like to join your tester panel to provide honest, lived-experience feedback.

I can receive payments via PayPal or Payoneer and I am fully equipped to participate in remote usability tests.

Could you please let me know how I can register as a tester?

Best regards,
Cuma Babacan
babacan.8691@gmail.com"""
            
            body = st.text_area("Mesaj", value=default_body, height=250)
            
            if st.button("🚀 E-postayı Gönder"):
                if to_email:
                    success, msg = send_email(to_email, subject, body)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Lütfen geçerli bir alıcı e-posta adresi girin.")
        else:
            st.warning("Önce 'Platformlar' sekmesinden bir platform ekleyin.")

    with col_inbox:
        st.subheader("📥 Gelen Kutusu (Son 5 E-posta)")
        if st.button("🔄 E-postaları Yenile"):
            with st.spinner("Gmail'e bağlanılıyor..."):
                emails = fetch_emails(5)
                if emails:
                    for idx, em in enumerate(emails):
                        with st.expander(f"📩 {em['subject'][:35]}..."):
                            st.write(f"**Kimden:** {em['from']}")
                            st.text(em['body'])
                else:
                    st.info("Gelen kutusu boş veya e-postalar okunamadı.")

# --- TAB 4: GENEL ÖZET ---
with tab4:
    st.header("Genel Durum Özeti")
    df_platforms = get_platforms()
    df_earnings = get_earnings()
    
    total_platforms = len(df_platforms)
    approved_platforms = len(df_platforms[df_platforms['status'] == 'Kabul Edildi']) if not df_platforms.empty else 0
    total_earnings = df_earnings['amount'].sum() if not df_earnings.empty else 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Başvurulan Platform", total_platforms)
    col2.metric("Kabul Edilen", approved_platforms)
    col3.metric("Toplam Kazanç", f"{total_earnings:.2f}")
    
    if not df_platforms.empty:
        st.subheader("Başvuru Durumları")
        st.bar_chart(df_platforms['status'].value_counts(), color="#00C853")
