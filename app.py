import streamlit as st
import pandas as pd
import sqlite3
import os
import imaplib
import email
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

# --- E-POSTA AYARLARI (Sadece Gelen Kutusu İçin) ---
GMAIL_ADRESI = "babacan.8691@gmail.com"
GMAIL_SIFRESI = "kuog wnba kcqu qgub"
DB_FILE = "tracker.db"

# --- VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Eski tabloları DROP ETMİYORUZ ki verilerimiz kaybolmasın
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
        # Web siteleri doğrudan başvuru sayfalarına yönlendirecek şekilde güncellendi
        platforms = [
            ("AccessWorks (Knowbility)", "https://knowbility.org/programs/accessworks", "aw-services@knowbility.org", "PayPal"),
            ("Testlio", "https://testlio.com/apply", "hello@testlio.com", "Payoneer"),
            ("Applause (uTest)", "https://applause.com/tester-signup/", "support@applause.com", "PayPal"),
            ("Respondent.io", "https://respondent.io/participants", "support@respondent.io", "PayPal"),
            ("Fable", "https://makeitfable.com/tester-signup/", "hello@makeitfable.com", "PayPal"),
            ("User Interviews", "https://userinterviews.com/signup", "support@userinterviews.com", "PayPal"),
            ("Userlytics", "https://userlytics.com/tester-sign-up/", "support@userlytics.com", "PayPal"),
            ("Userbrain", "https://userbrain.net/testers", "hello@userbrain.net", "PayPal"),
            ("TestingTime", "https://testingtime.com/en/become-a-tester/", "hello@testingtime.com", "PayPal"),
        ]
        for name, web, mail, pay in platforms:
            c.execute("INSERT INTO platforms (platform_name, website, contact_email, payment_method, application_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, web, mail, pay, datetime.now().strftime("%Y-%m-%d"), "Beklemede"))
        conn.commit()
    conn.close()

seed_platforms()

# --- VERİTABANI FONKSİYONLARI ---
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
st.sidebar.success("Giriş Yapıldı: Cuma Babacan")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Platformlar", "💰 Kazançlar", "🚀 Başvuru & Gelen Kutusu", "📊 Genel Özet"])

with tab1:
    st.header("Platform Listesi & Başvuru Durumları")
    with st.expander("➕ Yeni Platform Ekle"):
        with st.form("add_platform_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("Platform Adı")
            website = col2.text_input("Başvuru Sayfası Linki")
            contact_email = col3.text_input("İletişim E-postası (Varsa)")
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
                    st.caption(f"🌐 Link: {row['website']} | 💳 {row['payment_method']}")
                    if row['notes']:
                        st.info(f"Not: {row['notes']}")
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
    st.header("🚀 Başvuru Merkezi ve Gelen Yanıtlar")
    col_apply, col_inbox = st.columns(2)
    
    with col_apply:
        st.subheader("1. Platforma Git ve Başvur")
        df_platforms = get_platforms()
        if not df_platforms.empty:
            platform_dict = {row['id']: row['platform_name'] for _, row in df_platforms.iterrows()}
            selected_id = st.selectbox("Başvuru Yapılacak Platformu Seç", options=list(platform_dict.keys()), format_func=lambda x: platform_dict[x])
            
            target_row = df_platforms[df_platforms['id'] == selected_id]
            if not target_row.empty:
                target_url = target_row['website'].values[0]
                
                # Platformun web sitesine gitmek için buton
                st.link_button("🌐 Başvuru Sayfasına Git", target_url, use_container_width=True)
                
                st.write("---")
                st.write("📋 **Formlara Yapıştıracağın İngilizce Metin:**")
                english_text = """Hello Team,

My name is Cuma Babacan. I am a person with disabilities based in Turkey and a daily screen reader user. I would like to join your tester panel to provide honest, lived-experience feedback.

I can receive payments via PayPal or Payoneer and I am fully equipped to participate in remote usability tests.

Thank you."""
                
                # Metni kopyalaması için kutu
                st.code(english_text, language="text")
                st.caption("Yukarıdaki kutunun sağ üstündeki 'kopyala' ikonuna tıklayarak metni kopyalayıp, gittiğin sayfadaki forma yapıştırabilirsin.")
        else:
            st.warning("Önce platform ekleyin.")
            
    with col_inbox:
        st.subheader("2. Gelen Yanıtları Kontrol Et")
        st.write("Başvurularına gelen cevapları (kabul/ret) buradan görebilirsin.")
        if st.button("🔄 Gmail'i Kontrol Et (Son 5 E-posta)", use_container_width=True):
            with st.spinner("Gmail'e bağlanılıyor..."):
                emails = fetch_emails(5)
                if emails:
                    for idx, em in enumerate(emails):
                        with st.expander(f"📩 {em['subject'][:35]}..."):
                            st.write(f"**Kimden:** {em['from']}")
                            st.text(em['body'])
                else:
                    st.info("Gelen kutusu boş veya e-postalar okunamadı.")

with tab4:
    st.header("Genel Özet")
    df_p = get_platforms()
    df_e = get_earnings()
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Platform", len(df_p))
    c2.metric("Kabul Edilen", len(df_p[df_p['status'] == 'Kabul Edildi']) if not df_p.empty else 0)
    c3.metric("Toplam Kazanç", f"{df_e['amount'].sum():.2f}" if not df_e.empty else "0.00")
    if not df_p.empty:
        st.bar_chart(df_p['status'].value_counts(), color="#00C853")
