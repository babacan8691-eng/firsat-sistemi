import requests
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
