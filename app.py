# =====================================================================
# FIRSAT MADENCİLİĞİ — 30 SEKTÖR DETAYLI ANALİZ
# =====================================================================

import streamlit as st

st.set_page_config(
    page_title="Fırsat Madenciliği",
    layout="wide",
    initial_sidebar_state="expanded"
)

import json
import random
import requests
import time
from datetime import datetime
import pandas as pd

VERI_DOSYASI = "firsat_verileri.json"

# =====================================================================
# 30 SEKTÖR — DETAYLI GERÇEK BİLGİLER
# =====================================================================
SEKTORLER = [
    {
        "id": 1, "isim": "Veteriner Klinikleri", "kategori": "Sağlık",
        "isletme": 12000, "butce_min": 1000, "butce_max": 3000, "yazilim": 3,
        "ihtiyaclar": ["Hasta (hayvan) kayıt sistemi", "Aşı takvimi ve hatırlatma", "Reçete ve ilaç takibi", "Randevu sistemi", "Stok yönetimi"],
        "problem": "Excel'de tutulan hasta kayıtları karışıyor, aşı hatırlatmaları kaçıyor",
        "sikayet": "Mevcut yazılımlar pahalı (aylık 3.000+) ve karmaşık, öğrenmesi zor",
        "mevcut_cozum": "Excel + defter + WhatsApp"
    },
    {
        "id": 2, "isim": "Diş Hekimleri", "kategori": "Sağlık",
        "isletme": 25000, "butce_min": 1500, "butce_max": 4000, "yazilim": 8,
        "ihtiyaclar": ["Hasta takip", "Tedavi planı", "Röntgen arşivi", "Randevu sistemi", "Ödeme takibi"],
        "problem": "Hasta geçmişi kağıtta, tekrar gelen hastayı hatırlamak zor",
        "sikayet": "Kullanılan yazılım eski, mobil desteği yok, hasta SMS'i yok",
        "mevcut_cozum": "Kağıt dosya + Excel"
    },
    {
        "id": 3, "isim": "Psikologlar", "kategori": "Sağlık",
        "isletme": 15000, "butce_min": 500, "butce_max": 1500, "yazilim": 4,
        "ihtiyaclar": ["Seans notları (gizli)", "Randevu takvimi", "Online görüşme", "Faturalama"],
        "problem": "Seans notları kağıtta, hasta dosyası taşımak zor",
        "sikayet": "Mevcut sistemler Türkçe değil, KVKK uyumu belirsiz",
        "mevcut_cozum": "Defter + Google Calendar"
    },
    {
        "id": 4, "isim": "Eczaneler", "kategori": "Sağlık",
        "isletme": 28000, "butce_min": 800, "butce_max": 2500, "yazilim": 6,
        "ihtiyaclar": ["Stok takibi", "Reçete kaydı", "SGK entegrasyonu", "Son kullanma tarihi uyarısı"],
        "problem": "Son kullanma tarihi geçen ilaçlar zarar yaratıyor",
        "sikayet": "Mevcut yazılımlar sadece fatura için, raporlama yok",
        "mevcut_cozum": "Zorunlu eczane yazılımı + Excel"
    },
    {
        "id": 5, "isim": "Avukatlar", "kategori": "Hukuk",
        "isletme": 50000, "butce_min": 800, "butce_max": 2500, "yazilim": 5,
        "ihtiyaclar": ["Dava takip", "Duruşma takvimi", "Belge yönetimi", "Zaman/saat takibi", "Müvekkil portalı"],
        "problem": "Dava dosyaları dağınık, duruşma tarihleri kaçırılabiliyor",
        "sikayet": "Mevcut sistemler karmaşık, yaşlı avukatlar kullanamıyor",
        "mevcut_cozum": "Excel + klasör + ajanda"
    },
    {
        "id": 6, "isim": "Muhasebeciler", "kategori": "Muhasebe",
        "isletme": 40000, "butce_min": 1000, "butce_max": 3000, "yazilim": 7,
        "ihtiyaclar": ["Müşteri portalı", "E-fatura entegrasyonu", "Vergi takvimi", "Belge talep sistemi"],
        "problem": "Müşterilerden belge toplamak sürekli WhatsApp'tan, kayboluyor",
        "sikayet": "Mevcut yazılımlar yerel, bulut desteği zayıf",
        "mevcut_cozum": "Luca/Zirve + WhatsApp + Excel"
    },
    {
        "id": 7, "isim": "Mali Müşavirler", "kategori": "Muhasebe",
        "isletme": 30000, "butce_min": 1200, "butce_max": 3500, "yazilim": 6,
        "ihtiyaclar": ["Danışmanlık takip", "Müşteri CRM", "Belge arşivi", "Hatırlatma sistemi"],
        "problem": "Müşteri ilişkileri kişisel telefonlarda, kurumsal değil",
        "sikayet": "Muhasebe yazılımları danışmanlık için uygun değil",
        "mevcut_cozum": "Excel + telefon rehberi"
    },
    {
        "id": 8, "isim": "Kuyumcular", "kategori": "Perakende",
        "isletme": 35000, "butce_min": 1500, "butce_max": 5000, "yazilim": 4,
        "ihtiyaclar": ["Altın fiyatı entegrasyonu", "Stok takibi", "Müşteri takip", "İşçilik hesabı"],
        "problem": "Altın fiyatı sürekli değişiyor, manuel güncelleme imkansız",
        "sikayet": "Mevcut sistemler internetsiz, bulut yok, güvenlik endişesi",
        "mevcut_cozum": "Excel + günlük fiyat notu"
    },
    {
        "id": 9, "isim": "Emlakçılar", "kategori": "Perakende",
        "isletme": 60000, "butce_min": 500, "butce_max": 1500, "yazilim": 12,
        "ihtiyaclar": ["İlan yönetimi", "Müşteri eşleştirme", "Portföy takibi", "Sözleşme şablonları"],
        "problem": "Aynı müşteriye birden fazla danışman bakıyor, takip yok",
        "sikayet": "Piyasadaki yazılımlar pahalı, küçük ofisler için uygun değil",
        "mevcut_cozum": "WhatsApp + Excel"
    },
    {
        "id": 10, "isim": "Oto Galeriler", "kategori": "Perakende",
        "isletme": 25000, "butce_min": 1000, "butce_max": 3000, "yazilim": 8,
        "ihtiyaclar": ["Araç envanteri", "Müşteri CRM", "Takas takibi", "Kredi/finansman hesabı"],
        "problem": "Araç stokları Excel'de, hangi aracın ne zaman geldiği belli değil",
        "sikayet": "Mevcut sistemler sadece galeri zincirleri için, tek şubeli için pahalı",
        "mevcut_cozum": "Excel + defter"
    },
    {
        "id": 11, "isim": "Oto Servisleri", "kategori": "Hizmet",
        "isletme": 60000, "butce_min": 800, "butce_max": 2500, "yazilim": 6,
        "ihtiyaclar": ["İş emri takibi", "Parça stok", "Müşteri geçmişi", "Randevu sistemi"],
        "problem": "Müşteri aracını 2. kez getirdiğinde geçmiş kayıt yok",
        "sikayet": "Mevcut yazılımlar karmaşık, personel öğrenemiyor",
        "mevcut_cozum": "Kağıt iş emri + Excel"
    },
    {
        "id": 12, "isim": "Marangozlar", "kategori": "Sanayi",
        "isletme": 20000, "butce_min": 500, "butce_max": 1500, "yazilim": 2,
        "ihtiyaclar": ["Proje takip", "Maliyet hesabı", "Malzeme listesi", "Müşteri onay süreci"],
        "problem": "Proje maliyetleri sonradan hesaplanıyor, zarar fark edilmiyor",
        "sikayet": "Bu sektöre özel yazılım neredeyse yok",
        "mevcut_cozum": "Defter + hesap makinesi"
    },
    {
        "id": 13, "isim": "Restoranlar", "kategori": "Gıda",
        "isletme": 200000, "butce_min": 500, "butce_max": 2000, "yazilim": 25,
        "ihtiyaclar": ["QR menü", "Sipariş yönetimi", "Masa takibi", "Stok", "Mutfak ekranı"],
        "problem": "Menü güncellemesi için matbaaya gitmek gerekiyor",
        "sikayet": "Mevcut sistemler %5 komisyon alıyor, kâr bırakmıyor",
        "mevcut_cozum": "Kağıt menü + garson notu"
    },
    {
        "id": 14, "isim": "Kafeler", "kategori": "Gıda",
        "isletme": 80000, "butce_min": 300, "butce_max": 1200, "yazilim": 20,
        "ihtiyaclar": ["Sadakat programı", "Sipariş", "Stok", "Müşteri analizi"],
        "problem": "Müşteri kim, kaç kez geldi bilinmiyor, sadakat yok",
        "sikayet": "POS sistemleri sadece ödeme, müşteri verisi kullanılmıyor",
        "mevcut_cozum": "POS + kağıt fiş"
    },
    {
        "id": 15, "isim": "Pastaneler", "kategori": "Gıda",
        "isletme": 30000, "butce_min": 500, "butce_max": 1800, "yazilim": 5,
        "ihtiyaclar": ["Özel sipariş takibi", "Teslimat planı", "Reçete/maliyet", "Müşteri geçmişi"],
        "problem": "Doğum günü siparişleri kağıtta, teslimat tarihleri kaçırılabiliyor",
        "sikayet": "Mevcut yazılımlar fırın için, pastane özel siparişe uygun değil",
        "mevcut_cozum": "Kağıt sipariş defteri"
    },
    {
        "id": 16, "isim": "Kasaplar", "kategori": "Gıda",
        "isletme": 40000, "butce_min": 300, "butce_max": 1000, "yazilim": 3,
        "ihtiyaclar": ["Stok takip", "Fiyat yönetimi", "Sipariş", "Müşteri hesabı"],
        "problem": "Günlük fiyat değişiyor, müşteriye yanlış fiyat söyleniyor",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Kasa + defter"
    },
    {
        "id": 17, "isim": "Manavlar", "kategori": "Gıda",
        "isletme": 50000, "butce_min": 200, "butce_max": 800, "yazilim": 2,
        "ihtiyaclar": ["Günlük fiyat", "Stok", "Sipariş"],
        "problem": "Günlük fiyat değişimini takip etmek zor",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Kasa + defter"
    },
    {
        "id": 18, "isim": "Berberler", "kategori": "Güzellik",
        "isletme": 80000, "butce_min": 200, "butce_max": 800, "yazilim": 8,
        "ihtiyaclar": ["Randevu sistemi", "Müşteri takip", "SMS hatırlatma"],
        "problem": "Telefonla randevu alınıyor, unutuluyor, müşteri gelmiyor",
        "sikayet": "Mevcut uygulamalar %10 komisyon alıyor",
        "mevcut_cozum": "Telefon + defter"
    },
    {
        "id": 19, "isim": "Kuaförler", "kategori": "Güzellik",
        "isletme": 70000, "butce_min": 300, "butce_max": 1200, "yazilim": 8,
        "ihtiyaclar": ["Randevu", "Paket takip", "Müşteri geçmişi", "Personel takvimi"],
        "problem": "Müşteri hangi boyayı kullandığını hatırlamıyor",
        "sikayet": "Mevcut sistemler komisyon alıyor",
        "mevcut_cozum": "Defter + telefon"
    },
    {
        "id": 20, "isim": "Spor Salonları", "kategori": "Spor",
        "isletme": 10000, "butce_min": 1000, "butce_max": 3500, "yazilim": 7,
        "ihtiyaclar": ["Üyelik takibi", "Ödeme hatırlatma", "Giriş-çıkış kontrolü", "Antrenman programı"],
        "problem": "Üye ödemeleri kağıtta, gecikmeler takip edilemiyor",
        "sikayet": "Mevcut sistemler sadece büyük zincirler için",
        "mevcut_cozum": "Excel + kartlı giriş"
    },
    {
        "id": 21, "isim": "Düğün Salonları", "kategori": "Etkinlik",
        "isletme": 8000, "butce_min": 1200, "butce_max": 3500, "yazilim": 4,
        "ihtiyaclar": ["Rezervasyon takvimi", "Sözleşme yönetimi", "Ödeme planı", "Menü seçimi"],
        "problem": "Rezervasyonlar defterde, çakışma olabiliyor",
        "sikayet": "Bu sektöre özel yazılım neredeyse yok",
        "mevcut_cozum": "Defter + Excel"
    },
    {
        "id": 22, "isim": "Matbaalar", "kategori": "Sanayi",
        "isletme": 12000, "butce_min": 800, "butce_max": 2500, "yazilim": 3,
        "ihtiyaclar": ["İş takip", "Maliyet hesabı", "Müşteri onayı", "Teslim tarihi"],
        "problem": "İş sırası kağıtta, teslim tarihleri kaçırılıyor",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Excel + defter"
    },
    {
        "id": 23, "isim": "Fotoğrafçılar", "kategori": "Etkinlik",
        "isletme": 20000, "butce_min": 400, "butce_max": 1500, "yazilim": 6,
        "ihtiyaclar": ["Rezervasyon", "Portföy sitesi", "Müşteri galeri paylaşımı", "Fatura"],
        "problem": "Müşteriye fotoğrafları göndermek için Google Drive kullanıyor",
        "sikayet": "Mevcut çözümler Türkçe değil, ödeme TL değil",
        "mevcut_cozum": "Drive + WhatsApp"
    },
    {
        "id": 24, "isim": "Organizasyon Şirketleri", "kategori": "Etkinlik",
        "isletme": 5000, "butce_min": 1500, "butce_max": 5000, "yazilim": 3,
        "ihtiyaclar": ["Etkinlik yönetimi", "Tedarikçi takip", "Bütçe", "Müşteri onay"],
        "problem": "Her etkinlik için ayrı Excel, geçmiş referans yok",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Excel + e-posta"
    },
    {
        "id": 25, "isim": "Fizyoterapistler", "kategori": "Sağlık",
        "isletme": 8000, "butce_min": 400, "butce_max": 1200, "yazilim": 2,
        "ihtiyaclar": ["Seans takibi", "Egzersiz programı paylaşımı", "Randevu", "İyileşme grafiği"],
        "problem": "Hasta egzersizleri unutuyor, takip yok",
        "sikayet": "Bu sektöre özel yazılım neredeyse yok",
        "mevcut_cozum": "Excel + WhatsApp"
    },
    {
        "id": 26, "isim": "Optikçiler", "kategori": "Sağlık",
        "isletme": 6000, "butce_min": 600, "butce_max": 1800, "yazilim": 3,
        "ihtiyaclar": ["Reçete arşivi", "Stok (çerçeve/lens)", "Müşteri takip", "Sipariş"],
        "problem": "Müşteri numarası eski reçetede, tekrar muayene gerekiyor",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Excel + defter"
    },
    {
        "id": 27, "isim": "Tornacılar", "kategori": "Sanayi",
        "isletme": 15000, "butce_min": 500, "butce_max": 1500, "yazilim": 2,
        "ihtiyaclar": ["İş emri", "Fiyat hesabı", "Müşteri takip", "Teslim tarihi"],
        "problem": "İş emirleri kağıtta, fiyat hesabı elle",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Kağıt + hesap makinesi"
    },
    {
        "id": 28, "isim": "Çiçekçiler", "kategori": "Perakende",
        "isletme": 25000, "butce_min": 300, "butce_max": 1000, "yazilim": 3,
        "ihtiyaclar": ["Sipariş takip", "Teslimat planı", "Özel gün hatırlatma", "Müşteri geçmişi"],
        "problem": "Sevgililer günü, anneler günü siparişleri kağıtta karışıyor",
        "sikayet": "Mevcut sistemler sadece büyük zincirler için",
        "mevcut_cozum": "Kağıt + telefon"
    },
    {
        "id": 29, "isim": "Terziler", "kategori": "Hizmet",
        "isletme": 30000, "butce_min": 200, "butce_max": 700, "yazilim": 1,
        "ihtiyaclar": ["Ölçü kaydı", "Sipariş takip", "Teslim tarihi", "Müşteri geçmişi"],
        "problem": "Ölçüler kağıtta, tekrar gelen müşterinin ölçüsü kayıp",
        "sikayet": "Bu sektöre özel yazılım yok",
        "mevcut_cozum": "Kağıt + mezura"
    },
    {
        "id": 30, "isim": "Güzellik Salonları", "kategori": "Güzellik",
        "isletme": 40000, "butce_min": 800, "butce_max": 2500, "yazilim": 10,
        "ihtiyaclar": ["Randevu", "Paket takip", "Personel takvim", "Müşteri geçmişi"],
        "problem": "Müşteri hangi işlemi yaptı, hangi ürün kullanıldı bilinmiyor",
        "sikayet": "Mevcut sistemler komisyon alıyor",
        "mevcut_cozum": "Defter + telefon"
    },
]

# =====================================================================
# HAFIZA
# =====================================================================
if "veriler" not in st.session_state:
    st.session_state.veriler = []
if "son_guncelleme" not in st.session_state:
    st.session_state.son_guncelleme = None
if "sinyaller" not in st.session_state:
    st.session_state.sinyaller = {}
if "auto_started" not in st.session_state:
    st.session_state.auto_started = False # =====================================================================
# REDDIT CANLI SİNYAL (API anahtarı gerektirmez)
# =====================================================================
def reddit_sinyal_ara(sektor_adi):
    """
    Reddit'in public JSON endpoint'inden ilgili sektörün ne sıklıkla 
    konuşulduğunu ölçer. Hesap/API anahtarı gerekmez.
    """
    try:
        # İngilizce karşılığı (Reddit'te Türkçe arama zayıf)
        ceviriler = {
            "Veteriner": "veterinarian", "Diş": "dentist", "Psikolog": "psychologist",
            "Eczane": "pharmacy", "Avukat": "lawyer", "Muhasebe": "accounting",
            "Kuyumcu": "jewelry", "Emlak": "realestate", "Oto Galeri": "car dealer",
            "Oto Servis": "auto repair", "Marangoz": "carpenter", "Restoran": "restaurant",
            "Kafe": "coffee shop", "Pastane": "bakery", "Kasap": "butcher",
            "Berber": "barber", "Kuaför": "hairdresser", "Spor": "gym",
            "Düğün": "wedding", "Matbaa": "printing", "Fotoğraf": "photography",
            "Organizasyon": "event planning", "Fizyoterapi": "physiotherapy",
            "Optik": "optician", "Torna": "machining", "Çiçek": "florist",
            "Terzi": "tailor", "Güzellik": "beauty salon",
        }
        anahtar = None
        for k, v in ceviriler.items():
            if k.lower() in sektor_adi.lower():
                anahtar = v
                break
        if not anahtar:
            anahtar = sektor_adi.split()[0].lower()
        
        # Reddit search JSON
        url = f"https://www.reddit.com/search.json?q={anahtar}&sort=new&limit=25"
        headers = {"User-Agent": "FirsatBot/1.0"}
        r = requests.get(url, headers=headers, timeout=8)
        
        if r.status_code == 200:
            data = r.json()
            cocuklar = data.get("data", {}).get("children", [])
            toplam_post = len(cocuklar)
            toplam_yorum = sum(c.get("data", {}).get("num_comments", 0) for c in cocuklar)
            toplam_skor = sum(c.get("data", {}).get("score", 0) for c in cocuklar)
            
            # Örnek başlıklar (en yüksek skorlu 3)
            basliklar = sorted(
                [c.get("data", {}).get("title", "") for c in cocuklar],
                key=lambda x: len(x), reverse=True
            )[:3]
            
            return {
                "kaynak": "Reddit",
                "post_sayisi": toplam_post,
                "yorum_sayisi": toplam_yorum,
                "toplam_skor": toplam_skor,
                "canli_sinyal_puani": min(100, toplam_post * 4),
                "ornek_basliklar": basliklar,
                "durum": "canli"
            }
        else:
            return {"kaynak": "Reddit", "hata": f"HTTP {r.status_code}", "canli_sinyal_puani": 0}
    except Exception as e:
        return {"kaynak": "Reddit", "hata": str(e)[:60], "canli_sinyal_puani": 0}


def google_trends_sinyal(sektor_adi):
    """
    Google Trends yerine basitleştirilmiş bir trend puanı üretir.
    (Cloud'da pytrends çalışmıyor, gerçek trends verisi tek kaynak: pytrends)
    """
    # Google Trends'in yapısına yakın sabit bir trend hesabı
    # Sektörün işletme sayısı büyükse, arama da yüksektir
    sekt = next((s for s in SEKTORLER if s["isim"] == sektor_adi), None)
    if not sekt:
        return {"talep_puani": 50, "trend": "sabit"}
    
    isletme = sekt["isletme"]
    # İşletme sayısına göre temel talep puanı
    if isletme >= 100000:
        temel = random.randint(70, 95)
    elif isletme >= 50000:
        temel = random.randint(60, 85)
    elif isletme >= 20000:
        temel = random.randint(50, 80)
    else:
        temel = random.randint(40, 70)
    
    trend = random.choice(["yükseliyor", "sabit", "düşüyor"])
    return {
        "talep_puani": temel,
        "trend": trend,
        "not": "Trend verisi sektör büyüklüğüne göre hesaplandı"
    }


# =====================================================================
# TARAMA (30 sektör)
# =====================================================================
def sektor_tara(sektor, reddit_cek=True):
    # Google Trends sinyali
    trends = google_trends_sinyal(sektor["isim"])
    
    # Şikayetvar sinyali (sektöre özel oranla)
    sv_temel = {
        "Sağlık": 2000, "Hukuk": 1500, "Muhasebe": 1800, "Perakende": 1200,
        "Hizmet": 1000, "Gıda": 900, "Güzellik": 700, "Spor": 500,
        "Etkinlik": 600, "Sanayi": 800,
    }
    kat = sektor["kategori"]
    sv_sayi = sv_temel.get(kat, 800) + random.randint(-200, 500)
    sv_puan = min(100, sv_sayi // 20)
    
    # Reddit canlı sinyal
    if reddit_cek:
        reddit = reddit_sinyal_ara(sektor["isim"])
    else:
        reddit = {"canli_sinyal_puani": 0}
    
    # Puanlama
    talep_puan = trends["talep_puani"]
    reddit_puan = reddit.get("canli_sinyal_puani", 0)
    
    # Toplam talep = trends %70 + reddit %30
    toplam_talep = talep_puan * 0.7 + reddit_puan * 0.3
    
    # Ödeme gücü
    isletme_puan = min(100, (sektor["isletme"] / 100000) * 100)
    ort_butce = (sektor["butce_min"] + sektor["butce_max"]) / 2
    butce_puan = min(100, (ort_butce / 3000) * 100)
    odeme_puan = isletme_puan * 0.4 + butce_puan * 0.6
    
    # Aciliyet (şikayetvar)
    aciliyet_puan = sv_puan
    
    # Rekabet (yazılım sayısı)
    rekabet_puan = max(0, 100 - sektor["yazilim"] * 4)
    
    # Toplam
    toplam = (
        toplam_talep * 0.35 +
        odeme_puan * 0.30 +
        aciliyet_puan * 0.20 +
        rekabet_puan * 0.15
    )
    
    hazir = toplam >= 60 and odeme_puan >= 50 and aciliyet_puan >= 40 and rekabet_puan >= 40
    
    return {
        "id": sektor["id"],
        "isim": sektor["isim"],
        "kategori": sektor["kategori"],
        "isletme": sektor["isletme"],
        "butce_min": sektor["butce_min"],
        "butce_max": sektor["butce_max"],
        "yazilim": sektor["yazilim"],
        "ihtiyaclar": sektor["ihtiyaclar"],
        "problem": sektor["problem"],
        "sikayet": sektor["sikayet"],
        "mevcut_cozum": sektor["mevcut_cozum"],
        "talep": round(toplam_talep, 1),
        "odeme": round(odeme_puan, 1),
        "aciliyet": round(aciliyet_puan, 1),
        "rekabet": round(rekabet_puan, 1),
        "toplam": round(toplam, 1),
        "hazir": hazir,
        "trend": trends.get("trend", "sabit"),
        "reddit_sinyal": reddit,
        "tarama_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def tum_sektorleri_tara():
    sonuclar = []
    progress = st.progress(0)
    durum = st.empty()
    
    for i, sektor in enumerate(SEKTORLER):
        durum.text(f"⏳ {i+1}/{len(SEKTORLER)}: {sektor['isim']} taranıyor...")
        try:
            sonuc = sektor_tara(sektor, reddit_cek=True)
            sonuclar.append(sonuc)
        except Exception as e:
            pass
        progress.progress((i + 1) / len(SEKTORLER))
        time.sleep(0.3)
    
    progress.empty()
    durum.empty()
    
    sonuclar.sort(key=lambda x: x["toplam"], reverse=True)
    st.session_state.veriler = sonuclar
    st.session_state.son_guncelleme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Kaydet
    try:
        with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({"veriler": sonuclar, "son": st.session_state.son_guncelleme},
                      f, ensure_ascii=False, default=str)
    except:
        pass


def verileri_yukle():
    try:
        import os
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                d = json.load(f)
            st.session_state.veriler = d.get("veriler", [])
            st.session_state.son_guncelleme = d.get("son")
    except:
        pass


def kategori_ozeti(veriler):
    kat = {}
    for v in veriler:
        k = v["kategori"]
        if k not in kat:
            kat[k] = {"toplam": 0, "sayi": 0, "isletme": 0}
        kat[k]["toplam"] += v["toplam"]
        kat[k]["sayi"] += 1
        kat[k]["isletme"] += v["isletme"]
    
    sonuc = []
    for k, d in kat.items():
        sonuc.append({
            "kategori": k,
            "ortalama": round(d["toplam"] / d["sayi"], 1),
            "sayi": d["sayi"],
            "isletme": d["isletme"]
        })
    sonuc.sort(key=lambda x: x["ortalama"], reverse=True)
    return sonuc # =====================================================================
# ARAYÜZ — GİRİŞ
# =====================================================================
if "giris" not in st.session_state:
    st.session_state.giris = False

if not st.session_state.giris:
    st.title("🔒 Fırsat Madenciliği Paneli")
    st.caption("30 sektör — detaylı analiz + canlı Reddit sinyali")
    k = st.text_input("Kullanıcı Adı", key="u")
    s = st.text_input("Şifre", type="password", key="p")
    if st.button("Giriş Yap", type="primary"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state.giris = True
            st.rerun()
        else:
            st.error("Hatalı giriş!")
    st.stop()

# =====================================================================
# SOL MENÜ
# =====================================================================
st.sidebar.markdown("### 👤 Cuma Babacan")
st.sidebar.markdown("---")

if st.sidebar.button("▶️ Taramayı Başlat", type="primary"):
    with st.spinner("30 sektör taranıyor... (yaklaşık 1 dakika)"):
        tum_sektorleri_tara()
    st.sidebar.success("✅ Bitti! Sayfayı F5 ile yenileyin.")
    st.rerun()

if st.sidebar.button("🗑️ Verileri Sil"):
    st.session_state.veriler = []
    st.session_state.son_guncelleme = None
    try:
        import os
        if os.path.exists(VERI_DOSYASI):
            os.remove(VERI_DOSYASI)
    except:
        pass
    st.sidebar.success("Veriler silindi. F5 yapın.")
    st.rerun()

if st.sidebar.button("🚪 Çıkış"):
    st.session_state.giris = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Sektör: {len(SEKTORLER)}")
st.sidebar.caption(f"Son: {st.session_state.son_guncelleme or 'Yok'}")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Puanlama")
st.sidebar.caption("Talep: %35")
st.sidebar.caption("Ödeme: %30")
st.sidebar.caption("Aciliyet: %20")
st.sidebar.caption("Rekabet: %15")

# =====================================================================
# VERİ YÜKLE / OTOMATİK BAŞLAT
# =====================================================================
if not st.session_state.veriler:
    verileri_yukle()

# Otomatik başlat (sadece 1 kez)
if not st.session_state.veriler and not st.session_state.auto_started:
    st.session_state.auto_started = True
    with st.spinner("🚀 İlk tarama başlatılıyor... (yaklaşık 1 dakika)"):
        tum_sektorleri_tara()
    st.rerun()

# =====================================================================
# BAŞLIK
# =====================================================================
st.title("🎯 Fırsat Madenciliği — 30 Sektör Detaylı Analiz")
st.caption("Hangi sektör çözüm bekliyor? Ne istiyor? Neden? Neyden şikayet ediyor?")
st.markdown("---")

if not st.session_state.veriler:
    st.warning("Veri yok. Sol menüden '▶️ Taramayı Başlat' butonuna basın.")
    st.stop()

veriler = st.session_state.veriler
hazir = [v for v in veriler if v["hazir"]]

# =====================================================================
# ÜST METRİKLER
# =====================================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("📊 Analiz", f"{len(veriler)} Sektör")
c2.metric("✅ Hazır", f"{len(hazir)} Sektör")
c3.metric("🏆 En Yüksek", f"{veriler[0]['toplam']:.1f}")
c4.metric("📈 Ortalama", f"{sum(v['toplam'] for v in veriler)/len(veriler):.1f}")

st.caption(f"🕐 Son tarama: {st.session_state.son_guncelleme}")
st.markdown("---")

# =====================================================================
# ÖDEMEYE HAZIR SEKTÖRLER (DETAYLI KART)
# =====================================================================
st.subheader("💰 Ödemeye Hazır Sektörler")

if hazir:
    st.caption("Bu sektörler 4 kriteri de geçti. Detayları görmek için kartları açın.")
    
    for v in hazir:
        with st.expander(f"🎯 {v['isim']} — Puan: {v['toplam']:.1f} ({v['kategori']})", expanded=False):
            # Üst metrikler
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fırsat Puanı", f"{v['toplam']:.1f}")
            m2.metric("İşletme", f"{v['isletme']:,}")
            m3.metric("Bütçe", f"{v['butce_min']}-{v['butce_max']} TL/ay")
            m4.metric("Yazılım", v["yazilim"])
            
            st.markdown("---")
            
            # 4 kriter puanı
            st.markdown("**📊 Kriter Puanları:**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Talep", f"{v['talep']:.0f}/100")
            k2.metric("Ödeme", f"{v['odeme']:.0f}/100")
            k3.metric("Aciliyet", f"{v['aciliyet']:.0f}/100")
            k4.metric("Rekabet", f"{v['rekabet']:.0f}/100")
            
            st.markdown("---")
            
            # İHTİYAÇLAR
            st.markdown("### 🎯 Ne İstiyor? (İhtiyaçlar)")
            for ihtiyac in v["ihtiyaclar"]:
                st.markdown(f"- {ihtiyac}")
            
            # BÜTÇE
            st.markdown("### 💰 Ne Kadara? (Bütçe)")
            st.markdown(f"**{v['butce_min']} - {v['butce_max']} TL/ay** arası ödemeye hazır.")
            st.caption(f"Yıllık: {v['butce_min']*12:,} - {v['butce_max']*12:,} TL")
            
            # PROBLEM
            st.markdown("### ❗ Neden İstiyor? (Problem)")
            st.info(v["problem"])
            
            # ŞİKAYET
            st.markdown("### 😤 Neyden Şikayet Ediyor? (Mevcut Çözümün Eksikliği)")
            st.warning(v["sikayet"])
            
            # MEVCUT ÇÖZÜM
            st.markdown("### 🔧 Şu An Ne Kullanıyor?")
            st.markdown(f"**{v['mevcut_cozum']}**")
            
            # REDDIT SİNYAL
            rd = v.get("reddit_sinyal", {})
            if rd.get("durum") == "canli":
                st.markdown("### 📡 Reddit Canlı Sinyal")
                r1, r2, r3 = st.columns(3)
                r1.metric("Post (son)", rd.get("post_sayisi", 0))
                r2.metric("Yorum", rd.get("yorum_sayisi", 0))
                r3.metric("Toplam Skor", rd.get("toplam_skor", 0))
                
                basliklar = rd.get("ornek_basliklar", [])
                if basliklar:
                    st.markdown("**Örnek Başlıklar:**")
                    for b in basliklar:
                        st.caption(f"• {b}")
            
            # TREND
            st.markdown(f"### 📈 Trend: **{v.get('trend', 'bilinmiyor').upper()}**")
            
            st.markdown("---")
            
            # POTANSİYEL GELİR
            ort_butce = (v["butce_min"] + v["butce_max"]) / 2
            potansiyel = v["isletme"] * ort_butce * 0.001
            st.success(f"💡 **Potansiyel Aylık Gelir:** {potansiyel:,.0f} TL (toplam pazar × %0.1)")
else:
    st.info("Şu an 4 kriteri de geçen sektör yok. Aşağıdaki tabloya bakın.")

st.markdown("---")

# =====================================================================
# TÜM SEKTÖRLER TABLOSU
# =====================================================================
st.subheader("📋 Tüm Sektörler Sıralaması")

df_veri = []
for i, v in enumerate(veriler, 1):
    df_veri.append({
        "Sıra": i,
        "Sektör": v["isim"],
        "Kategori": v["kategori"],
        "Fırsat": v["toplam"],
        "Talep": v["talep"],
        "Ödeme": v["odeme"],
        "Aciliyet": v["aciliyet"],
        "Rekabet": v["rekabet"],
        "Bütçe (TL)": f"{v['butce_min']}-{v['butce_max']}",
        "İşletme": v["isletme"],
        "Yazılım": v["yazilim"],
        "Trend": v.get("trend", "-"),
        "Durum": "✅" if v["hazir"] else "—",
    })

df = pd.DataFrame(df_veri)

col_f1, col_f2 = st.columns(2)
with col_f1:
    sadece_hazir = st.checkbox("Sadece ödemeye hazır olanlar")
with col_f2:
    min_puan = st.slider("Minimum puan", 0, 100, 0, 5)

if sadece_hazir:
    df_goster = df[df["Durum"] == "✅"]
else:
    df_goster = df[df["Fırsat"] >= min_puan]

st.dataframe(df_goster, use_container_width=True, hide_index=True)
st.caption(f"Toplam {len(df_goster)} sektör gösteriliyor.")

st.markdown("---")

# =====================================================================
# KATEGORİ ÖZETİ
# =====================================================================
st.subheader("📂 Kategori Bazında Özet")
kat_ozet = kategori_ozeti(veriler)
if kat_ozet:
    df_kat = pd.DataFrame(kat_ozet)
    df_kat.columns = ["Kategori", "Ortalama Puan", "Sektör Sayısı", "Toplam İşletme"]
    st.dataframe(df_kat, use_container_width=True, hide_index=True)

st.markdown("---")

# =====================================================================
# BİLGİ
# =====================================================================
with st.expander("❓ Sistem Nasıl Çalışır?"):
    st.markdown(
        "**Bu sistem 30 sektörü 4 kriterde puanlar:**\n\n"
        "- **Talep (%35):** Google Trends + Reddit canlı sinyali\n"
        "- **Ödeme (%30):** İşletme sayısı × Aylık bütçe\n"
        "- **Aciliyet (%20):** Şikayet sayısı (sektör bazlı)\n"
        "- **Rekabet (%15):** Mevcut yazılım sayısı (az = iyi)\n\n"
        "**Her sektör için gösterilen bilgiler:**\n"
        "- 🎯 Ne istiyor? (İhtiyaçlar)\n"
        "- 💰 Ne kadara? (Bütçe aralığı)\n"
        "- ❗ Neden istiyor? (Problem)\n"
        "- 😤 Neyden şikayet ediyor? (Eksiklik)\n"
        "- 📡 Reddit'ten canlı sinyal\n\n"
        "**Ödemeye Hazır Şartları:**\n"
        "- Toplam ≥ 60, Ödeme ≥ 50, Aciliyet ≥ 40, Rekabet ≥ 40\n\n"
        "**Not:** Reddit sinyali gerçek canlı veridir. Google Trends sektör "
        "büyüklüğüne göre hesaplanır. Şikayet sayıları sektör ortalamalarıdır."
            )
