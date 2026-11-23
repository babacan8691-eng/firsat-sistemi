import sqlite3
import threading
import time
import schedule
from flask import Flask, request, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_cuma_babacan_123'

# --- VERİTABANI İŞLEMLERİ ---
def init_db():
    conn = sqlite3.connect('ihaleler.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ilanlar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  baslik TEXT, 
                  kurum TEXT, 
                  link TEXT, 
                  yayin_tarihi TEXT,
                  yesil_isik INTEGER)''')
    conn.commit()
    conn.close()

# --- TARAYICI (BOT) MANTIĞI ---
def ilani_analiz_et(baslik, icerik):
    """İlanın metnine bakarak engelli birey için uygun olup olmadığını anlar."""
    metin = (baslik + " " + icerik).lower()
    
    # Eğer ilanda engelli şartı varsa direkt yeşil ışık
    if "engelli" in metin and ("%40" in metin or "rapor" in metin):
        return 1
    # Eğer büfe veya çay bahçesi ise ve kiralama ise potansiyel yeşil ışık
    elif ("büfe" in metin or "çay bahçesi" in metin) and "kiralama" in metin:
        return 1
    return 0

def ilanlari_tara_ve_kaydet():
    print("[BOT] İlanlar taranıyor...")
    
    # NOT: Gerçek web kazıma (scraping) kodları buraya gelecek. 
    # Şu an sistemin çalıştığını görmeniz için örnek veriler ekliyoruz.
    ornek_ilanlar = [
        {"baslik": "Şahinbey Merkezde Büfe Kiralama İhalesi", "kurum": "Şahinbey Belediyesi", "link": "https://ornek.com/1", "icerik": "Muhtelif yerlerde büfe kiralama işi"},
        {"baslik": "Engelli Vatandaşlarımıza Özel Çay Bahçesi İhalesi", "kurum": "Gaziantep Büyükşehir", "link": "https://ornek.com/2", "icerik": "%40 ve üzeri engelli raporu sahibi olmak şartıyla çay bahçesi kiralanacaktır."},
        {"baslik": "Şehitkamil'de Dükkan Kiralama İhalesi", "kurum": "Şehitkamil Belediyesi", "link": "https://ornek.com/3", "icerik": "Genel dükkan kiralama işi."}
    ]
    
    conn = sqlite3.connect('ihaleler.db')
    c = conn.cursor()
    
    for ilan in ornek_ilanlar:
        c.execute("SELECT id FROM ilanlar WHERE link=?", (ilan['link'],))
        if not c.fetchone():
            yesil_isik = ilani_analiz_et(ilan['baslik'], ilan['icerik'])
            c.execute("INSERT INTO ilanlar (baslik, kurum, link, yayin_tarihi, yesil_isik) VALUES (?, ?, ?, date('now'), ?)",
                      (ilan['baslik'], ilan['kurum'], ilan['link'], yesil_isik))
            print(f"[BOT] Yeni ilan bulundu: {ilan['baslik']} (Yeşil Işık: {yesil_isik})")
    
    conn.commit()
    conn.close()
    print("[BOT] Tarama tamamlandı. Sıradaki tarama 1 saat sonra.")

def bot_dongusu():
    # Botu 1 saatte bir çalışacak şekilde ayarla
    schedule.every(1).hours.do(ilanlari_tara_ve_kaydet)
    ilanlari_tara_ve_kaydet() # İlk başlatıldığında hemen çalıştır
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- WEB ARAYÜZÜ (PANEL) ---
HTML_TASARIM = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>İhale Takip Paneli</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
        h2 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #007bff; color: white; }
        .yesil { background-color: #d4edda; color: #155724; font-weight: bold; }
        .kirmizi { background-color: #f8d7da; color: #721c24; }
        .logout { float: right; text-decoration: none; color: red; }
    </style>
</head>
<body>
    <a href="/logout" class="logout">Çıkış Yap</a>
    <h2>Sayın Cuma Babacan, İhale Takip Paneline Hoş Geldiniz</h2>
    <p>Aşağıda sistemin otomatik olarak bulduğu ilanlar listelenmektedir. Size uygun olanlar <b>Yeşil Işık</b> ile işaretlenmiştir.</p>
    
    <table>
        <tr>
            <th>Durum</th>
            <th>İlan Başlığı</th>
            <th>Kurum</th>
            <th>İlan Linki</th>
        </tr>
        {% for ilan in ilanlar %}
        <tr class="{{ 'yesil' if ilan[5] == 1 else 'kirmizi' }}">
            <td>{{ '🟢 YEŞİL IŞIK' if ilan[5] == 1 else '🔴 Genel İhale' }}</td>
            <td>{{ ilan[1] }}</td>
            <td>{{ ilan[2] }}</td>
            <td><a href="{{ ilan[3] }}" target="_blank">İlanı Görüntüle</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # İSTEDİĞİNİZ KULLANICI ADI VE ŞİFRE BURADA TANIMLI
        if request.form['username'] == 'Cuma Babacan' and request.form['password'] == '784512':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return "<h3>Hatalı kullanıcı adı veya şifre!</h3><a href='/login'>Geri dön</a>"
    return '''
        <div style="margin: 50px auto; width: 300px; text-align: center; font-family: Arial;">
            <h3>Sisteme Giriş</h3>
            <form method="post">
                <input type="text" name="username" placeholder="Kullanıcı Adı" style="padding: 10px; margin-bottom: 10px; width: 100%;"><br>
                <input type="password" name="password" placeholder="Şifre" style="padding: 10px; margin-bottom: 10px; width: 100%;"><br>
                <input type="submit" value="Giriş Yap" style="padding: 10px; width: 100%; background: #007bff; color: white; border: none; cursor: pointer;">
            </form>
        </div>
    '''

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('ihaleler.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ilanlar ORDER BY yesil_isik DESC, id DESC")
    ilanlar = c.fetchall()
    conn.close()
    
    return render_template_string(HTML_TASARIM, ilanlar=ilanlar)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- SİSTEMİ BAŞLATMA ---
if __name__ == '__main__':
    init_db()
    
    # 1. Arka plan botunu başlat
    bot_thread = threading.Thread(target=bot_dongusu, daemon=True)
    bot_thread.start()
    
    # 2. Web sunucusunu başlat
    print("Panel başlatıldı. Tarayıcınızdan http://127.0.0.1:5000 adresine gidin.")
    app.run(debug=True, port=5000, use_reloader=False)
