from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_gaziantep_ihale_784512' # Oturum güvenliği için

# --- VERİTABANI AYARLARI ---
def get_db():
    conn = sqlite3.connect('sistem.db')
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

# Başlangıçta veritabanını oluştur
if not os.path.exists('sistem.db'):
    init_db()

# --- HTML TASARIMI (Önceki panelin sunucuya uyarlanmış hali) ---
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>İhale Takip Paneli</title>
<style>
:root { --bg:#0f1720; --card:#1a2430; --line:#2b3a4a; --txt:#e6edf3; --mut:#9fb0c0; --acc:#3b82f6; --ok:#22c55e; --warn:#f59e0b; --err:#ef4444; }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.5 system-ui, sans-serif; background:var(--bg); color:var(--txt); }
header { padding:14px 20px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; }
h1 { font-size:17px; margin:0; }
main { padding:20px; max-width:1100px; margin:0 auto; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:12px; }
input, select, textarea { background:#0d151d; border:1px solid var(--line); color:var(--txt); border-radius:8px; padding:8px; width:100%; margin-bottom:8px; }
.btn { background:var(--acc); color:#fff; border:0; padding:9px 14px; border-radius:8px; cursor:pointer; }
.btn.err { background:var(--err); }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
table { width:100%; border-collapse:collapse; margin-top:10px; }
th, td { text-align:left; padding:8px; border-bottom:1px solid var(--line); font-size:14px; }
.badge { padding:3px 8px; border-radius:6px; font-size:12px; background:#2b3a4a; }
</style>
</head>
<body>
<header>
  <h1>📋 İhale & Fırsat Takip Sistemi</h1>
  <a href="/logout" class="btn err" style="text-decoration:none;">Çıkış Yap</a>
</header>
<main>
  <div class="card">
    <h3>Yeni İlan Ekle</h3>
    <div class="grid">
      <input id="i-kurum" placeholder="Kurum (Örn: Gaziantep Bşb.)">
      <input id="i-baslik" placeholder="İlan Başlığı (Örn: Büfe Kiralama)">
      <input id="i-tarih" type="date" title="Son Başvuru Tarihi">
      <input id="i-link" placeholder="İlan Linki (URL)">
    </div>
    <textarea id="i-not" placeholder="Notlar"></textarea>
    <button class="btn" onclick="ilanEkle()">Kaydet</button>
  </div>

  <div class="card">
    <h3>Kayıtlı İlanlar</h3>
    <table>
      <thead><tr><th>Kurum</th><th>Başlık</th><th>Son Tarih</th><th>Durum</th><th>İşlem</th></tr></thead>
      <tbody id="ilan-listesi"></tbody>
    </table>
  </div>
</main>

<script>
async function verileriYukle() {
    const res = await fetch('/api/ilanlar');
    const ilanlar = await res.json();
    const tbody = document.getElementById('ilan-listesi');
    tbody.innerHTML = '';
    ilanlar.forEach(i => {
        tbody.innerHTML += `<tr>
            <td>${i.kurum}</td>
            <td><a href="${i.link}" target="_blank" style="color:#7cc4ff">${i.baslik}</a></td>
            <td>${i.sonTarih || '-'}</td>
            <td><span class="badge">${i.durum}</span></td>
            <td><button onclick="ilanSil(${i.id})" style="background:none;border:none;color:red;cursor:pointer">Sil</button></td>
        </tr>`;
    });
}

async function ilanEkle() {
    const data = {
        kurum: document.getElementById('i-kurum').value,
        baslik: document.getElementById('i-baslik').value,
        sonTarih: document.getElementById('i-tarih').value,
        link: document.getElementById('i-link').value,
        notlar: document.getElementById('i-not').value,
        durum: "İncelenecek"
    };
    await fetch('/api/ilanlar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    verileriYukle();
}

async function ilanSil(id) {
    if(confirm('Silinsin mi?')) {
        await fetch('/api/ilanlar/' + id, {method: 'DELETE'});
        verileriYukle();
    }
}
verileriYukle();
</script>
</body>
</html>
"""

# --- GİRİŞ EKRANI TASARIMI ---
GIRIS_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giriş Yap</title>
<style>
body { background:#0f1720; color:#fff; font-family:system-ui; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
.card { background:#1a2430; padding:30px; border-radius:12px; width:300px; border:1px solid #2b3a4a; }
input { width:100%; padding:10px; margin:10px 0; border-radius:6px; border:1px solid #333; background:#0d151d; color:#fff; box-sizing:border-box; }
button { width:100%; padding:10px; background:#3b82f6; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:bold; }
h2 { text-align:center; margin-top:0; }
</style>
</head>
<body>
<div class="card">
    <h2>Sisteme Giriş</h2>
    {% if hata %}<p style="color:red;text-align:center;">{{ hata }}</p>{% endif %}
    <form method="POST">
        <input type="text" name="kullanici" placeholder="Kullanıcı Adı" required>
        <input type="password" name="sifre" placeholder="Şifre" required>
        <button type="submit">Giriş Yap</button>
    </form>
</div>
</body>
</html>
"""

# --- ROTALAR (ROUTES) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        kullanici = request.form.get('kullanici')
        sifre = request.form.get('sifre')
        
        # BELİRLEDİĞİNİZ KULLANICI ADI VE ŞİFRE KONTROLÜ
        if kullanici == "Cuma Babacan" and sifre == "784512":
            session['giris_yapildi'] = True
            return redirect(url_for('panel'))
        else:
            return render_template_string(GIRIS_SABLONU, hata="Kullanıcı adı veya şifre hatalı!")
            
    return render_template_string(GIRIS_SABLONU, hata=None)

@app.route('/logout')
def logout():
    session.pop('giris_yapildi', None)
    return redirect(url_for('login'))

@app.route('/')
def panel():
    if not session.get('giris_yapildi'):
        return redirect(url_for('login'))
    return render_template_string(HTML_SABLONU)

# --- API UÇ NOKTALARI (Veri Alışverişi) ---

@app.route('/api/ilanlar', methods=['GET'])
def ilanlari_getir():
    if not session.get('giris_yapildi'): return jsonify({"hata": "Yetkisiz"}), 401
    with get_db() as conn:
        ilanlar = conn.execute('SELECT * FROM ilanlar ORDER BY sonTarih ASC').fetchall()
        return jsonify([dict(i) for i in ilanlar])

@app.route('/api/ilanlar', methods=['POST'])
def ilan_ekle():
    if not session.get('giris_yapildi'): return jsonify({"hata": "Yetkisiz"}), 401
    data = request.json
    with get_db() as conn:
        conn.execute('INSERT INTO ilanlar (kurum, baslik, sonTarih, link, notlar, durum) VALUES (?, ?, ?, ?, ?, ?)',
                     (data['kurum'], data['baslik'], data['sonTarih'], data['link'], data['notlar'], data['durum']))
    return jsonify({"basarili": True})

@app.route('/api/ilanlar/<int:id>', methods=['DELETE'])
def ilan_sil(id):
    if not session.get('giris_yapildi'): return jsonify({"hata": "Yetkisiz"}), 401
    with get_db() as conn:
        conn.execute('DELETE FROM ilanlar WHERE id = ?', (id,))
    return jsonify({"basarili": True})

if __name__ == '__main__':
    app.run(debug=True)
