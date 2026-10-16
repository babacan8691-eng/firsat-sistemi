# =====================================================================
# LEAD YÖNETİM SİSTEMİ — 5 SEKTÖR ODAKLI
# =====================================================================

import streamlit as st

st.set_page_config(
    page_title="Lead Yönetim Sistemi",
    layout="wide",
    initial_sidebar_state="expanded"
)

import json
import os
import csv
import io
import random
from datetime import datetime, timedelta
import pandas as pd

# =====================================================================
# AYARLAR
# =====================================================================
LEAD_DOSYASI = "leadlar.json"
MESAJ_DOSYASI = "mesajlar.json"

# =====================================================================
# 5 HEDEF SEKTÖR (Detaylı Bilgi)
# =====================================================================
SEKTORLER = {
    "Mali Müşavirler": {
        "id": 1,
        "kategori": "Muhasebe",
        "isletme_sayisi": 30000,
        "butce_min": 1200,
        "butce_max": 3500,
        "mevcut_cozum": "Excel + telefon rehberi + WhatsApp",
        "problem": "Müşteri ilişkileri kişisel telefonlarda, kurumsal değil",
        "sikayet": "Muhasebe yazılımları danışmanlık için uygun değil",
        "ihtiyaclar": [
            "Danışmanlık takip sistemi",
            "Müşteri CRM",
            "Belge arşivi",
            "Otomatik hatırlatma"
        ],
        "linkedin_arama": "mali müşavir",
        "hedef_kitle": "Serbest çalışan mali müşavirler (5-50 müşteri)"
    },
    "Avukatlar": {
        "id": 2,
        "kategori": "Hukuk",
        "isletme_sayisi": 50000,
        "butce_min": 800,
        "butce_max": 2500,
        "mevcut_cozum": "Excel + klasör + ajanda",
        "problem": "Dava dosyaları dağınık, duruşma tarihleri kaçırılabiliyor",
        "sikayet": "Mevcut sistemler karmaşık, yaşlı avukatlar kullanamıyor",
        "ihtiyaclar": [
            "Dava takip sistemi",
            "Duruşma takvimi",
            "Belge yönetimi",
            "Müvekkil portalı"
        ],
        "linkedin_arama": "avukat",
        "hedef_kitle": "Serbest avukatlar + küçük bürolar (1-10 kişi)"
    },
    "Diş Hekimleri": {
        "id": 3,
        "kategori": "Sağlık",
        "isletme_sayisi": 25000,
        "butce_min": 1500,
        "butce_max": 4000,
        "mevcut_cozum": "Kağıt dosya + Excel",
        "problem": "Hasta geçmişi kağıtta, tekrar gelen hastayı hatırlamak zor",
        "sikayet": "Kullanılan yazılım eski, mobil desteği yok",
        "ihtiyaclar": [
            "Randevu sistemi",
            "Hasta takibi",
            "Tedavi planı",
            "Otomatik SMS hatırlatma"
        ],
        "linkedin_arama": "diş hekimi",
        "hedef_kitle": "Özel muayenehane sahibi diş hekimleri"
    },
    "Muhasebeciler": {
        "id": 4,
        "kategori": "Muhasebe",
        "isletme_sayisi": 40000,
        "butce_min": 1000,
        "butce_max": 3000,
        "mevcut_cozum": "Luca/Zirve + WhatsApp + Excel",
        "problem": "Müşterilerden belge toplamak sürekli WhatsApp'tan, kayboluyor",
        "sikayet": "Mevcut yazılımlar yerel, bulut desteği zayıf",
        "ihtiyaclar": [
            "Müşteri belge portalı",
            "E-fatura entegrasyonu",
            "Vergi takvimi hatırlatma",
            "Belge talep sistemi"
        ],
        "linkedin_arama": "muhasebeci",
        "hedef_kitle": "Küçük ve orta ölçekli muhasebe büroları"
    },
    "Oto Servisleri": {
        "id": 5,
        "kategori": "Hizmet",
        "isletme_sayisi": 60000,
        "butce_min": 800,
        "butce_max": 2500,
        "mevcut_cozum": "Kağıt iş emri + Excel",
        "problem": "Müşteri aracını 2. kez getirdiğinde geçmiş kayıt yok",
        "sikayet": "Mevcut yazılımlar karmaşık, personel öğrenemiyor",
        "ihtiyaclar": [
            "İş emri takibi",
            "Parça stok",
            "Müşteri geçmişi",
            "Randevu sistemi"
        ],
        "linkedin_arama": "oto servis",
        "hedef_kitle": "Tek şubeli oto tamir servisleri"
    },
}

# =====================================================================
# HAFIZA YAPISI
# =====================================================================
@st.cache_resource
def get_hafiza():
    return {
        "leadlar": [],       # Tüm potansiyel müşteriler
        "mesajlar": [],      # Gönderilen mesajlar
        "yanitlar": [],      # Alınan yanıtlar
        "notlar": [],        # Sektör notları
    }

# =====================================================================
# DOSYA İŞLEMLERİ
# =====================================================================
def leadlari_kaydet(hafiza):
    try:
        with open(LEAD_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(hafiza["leadlar"], f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        st.warning(f"Kayıt hatası: {e}")

def leadlari_yukle(hafiza):
    try:
        if os.path.exists(LEAD_DOSYASI):
            with open(LEAD_DOSYASI, "r", encoding="utf-8") as f:
                hafiza["leadlar"] = json.load(f)
    except:
        pass

def mesajlari_kaydet(hafiza):
    try:
        with open(MESAJ_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({
                "mesajlar": hafiza["mesajlar"],
                "yanitlar": hafiza["yanitlar"]
            }, f, ensure_ascii=False, indent=2, default=str)
    except:
        pass

def mesajlari_yukle(hafiza):
    try:
        if os.path.exists(MESAJ_DOSYASI):
            with open(MESAJ_DOSYASI, "r", encoding="utf-8") as f:
                d = json.load(f)
                hafiza["mesajlar"] = d.get("mesajlar", [])
                hafiza["yanitlar"] = d.get("yanitlar", [])
    except:
        pass # =====================================================================
# MESAJ ŞABLONLARI (Her Sektör İçin Özel)
# =====================================================================
MESAJ_SABLONLARI = {
    "Mali Müşavirler": {
        "linkedin": """Merhaba {isim} Bey/Hanım,

Ben Gaziantep'te yaşayan bir yazılım geliştiricisiyim. Mali müşavirlerin müşteri ilişkileri ve belge takibi konusunda yaşadığı zorluğu çözen bir sistem geliştirdim.

Kısaca:
- Müşteri bilgileri ve görüşme geçmişi tek yerde
- Belge talepleri otomatik hatırlatılır
- Müşteri portalı ile belge toplama kolaylaşır

10 dakikalık kısa bir demo görebilir miyiz? Ücretsiz.

Saygılarımla,
{ad_soyad}""",
        "email": """Sayın {isim},

Ben {ad_soyad}, Gaziantep'te yaşayan bir yazılım geliştiricisiyim.

Mali müşavirlerin karşılaştığı en büyük zorluk: müşteri bilgilerinin dağınık olması ve belge toplamanın WhatsApp üzerinden yapılması. Bu sorunu çözmek için basit bir sistem geliştirdim.

Demo göstermek ister misiniz? 10 dakika yeter.

Saygılarımla,
{ad_soyad}
{telefon}"""
    },
    "Avukatlar": {
        "linkedin": """Merhaba {isim} Bey/Hanım,

Avukatların dava dosyalarını ve duruşma takvimini tek yerden yönetmesini sağlayan bir sistem geliştirdim.

Özellikle küçük bürolar için:
- Dava takibi ve duruşma takvimi
- Müvekkil bilgileri tek yerde
- Belge arşivi
- Otomatik hatırlatmalar

Ücretsiz 10 dakikalık bir demo gösterebilir miyim?

Saygılarımla,
{ad_soyad}""",
        "email": """Sayın {isim},

Ben {ad_soyad}. Avukatlar için geliştirdiğim dava ve müvekkil takip sistemini tanıtmak istiyorum.

Küçük büroların en büyük problemi: dava dosyalarının dağınık olması ve duruşma tarihlerinin kaçırılması. Bu sorunu çözen basit bir çözüm geliştirdim.

Demo göstermek ister misiniz?

Saygılarımla,
{ad_soyad}
{telefon}"""
    },
    "Diş Hekimleri": {
        "linkedin": """Merhaba {isim} Bey/Hanım,

Diş hekimlerinin hasta takibi ve randevu konusunda yaşadığı zorluğu çözen bir sistem geliştirdim.

Özellikle:
- Hasta geçmişi (tedavi, röntgen) tek yerde
- Randevu sistemi ve otomatik SMS hatırlatma
- Tedavi planı takibi
- Ödeme takibi

Kısa bir demo gösterebilir miyim? Ücretsiz.

Saygılarımla,
{ad_soyad}""",
        "email": """Sayın {isim},

Ben {ad_soyad}. Diş hekimleri için hasta ve randevu takip sistemi geliştirdim.

Hasta geçmişini hatırlamak, randevu kaçırmak, tedavi planını takip etmek — bunların hepsini tek yerden yönetmek mümkün.

10 dakikalık demo göstermek ister misiniz?

Saygılarımla,
{ad_soyad}
{telefon}"""
    },
    "Muhasebeciler": {
        "linkedin": """Merhaba {isim} Bey/Hanım,

Muhasebe bürolarının müşterilerden belge toplama sürecini kolaylaştıran bir sistem geliştirdim.

Şu an çoğu büro WhatsApp üzerinden belge topluyor, kaybolabiliyor. Sistem şunu yapıyor:
- Müşteriye otomatik belge talebi gider
- Belge portalı üzerinden yüklenir
- Arşiv otomatik tutulur

Ücretsiz demo gösterebilir miyim?

Saygılarımla,
{ad_soyad}""",
        "email": """Sayın {isim},

Ben {ad_soyad}. Muhasebe büroları için müşteri belge toplama sistemi geliştirdim.

En büyük sorun: müşterilerden belge toplamak WhatsApp üzerinden yapılıyor ve kayboluyor. Bu sistemi kuran bürolar %60 daha az zaman harcıyor.

Demo göstermek ister misiniz?

Saygılarımla,
{ad_soyad}
{telefon}"""
    },
    "Oto Servisleri": {
        "linkedin": """Merhaba {isim} Bey/Hanım,

Oto servislerinin iş emri ve müşteri takibini kolaylaştıran bir sistem geliştirdim.

Özellikle:
- İş emri dijital takip
- Müşteri aracının geçmiş servis kaydı
- Parça stok takibi
- Randevu sistemi

Ücretsiz 10 dakikalık demo gösterebilir miyim?

Saygılarımla,
{ad_soyad}""",
        "email": """Sayın {isim},

Ben {ad_soyad}. Oto servisleri için iş emri ve müşteri takip sistemi geliştirdim.

Müşteri aracını 2. kez getirdiğinde geçmiş kaydı görmek, iş emrini kağıt yerine dijitalde tutmak, parça stokunu takip etmek — hepsi mümkün.

Demo göstermek ister misiniz?

Saygılarımla,
{ad_soyad}
{telefon}"""
    },
}

# =====================================================================
# KİŞİSELLEŞTİRİLMİŞ MESAJ ÜRET
# =====================================================================
def mesaj_uret(sektor, lead, kanal="linkedin"):
    """
    Belirtilen sektör ve lead için kişiselleştirilmiş mesaj üretir.
    """
    if sektor not in MESAJ_SABLONLARI:
        return "Şablon bulunamadı."
    
    sablon = MESAJ_SABLONLARI[sektor].get(kanal, "")
    
    # Kişiselleştirme değişkenleri
    isim = lead.get("isim", "").strip() or "Değerli"
    ad_soyad = "Cuma Babacan"
    telefon = lead.get("telefon", "") or "[telefon]"
    
    mesaj = sablon.format(
        isim=isim,
        ad_soyad=ad_soyad,
        telefon=telefon
    )
    
    return mesaj

# =====================================================================
# LEAD PUANLAMA (Hangi Lead Daha Sıcak?)
# =====================================================================
def lead_puani(lead):
    """
    Lead'in sıcaklığını hesaplar (0-100).
    Yüksek puan = yüksek ihtimal satış.
    """
    puan = 50  # Temel puan
    
    # Sektör puanı (yüksek puanlı sektörler = yüksek puan)
    sektor_puanlari = {
        "Mali Müşavirler": 20,
        "Avukatlar": 18,
        "Diş Hekimleri": 16,
        "Muhasebeciler": 14,
        "Oto Servisleri": 12,
    }
    puan += sektor_puanlari.get(lead.get("sektor", ""), 0)
    
    # Firma büyüklüğü
    calisan = lead.get("calisan_sayisi", 0)
    if calisan and calisan >= 5:
        puan += 10
    elif calisan and calisan >= 2:
        puan += 5
    
    # Bütçe
    butce = lead.get("butce", 0)
    if butce >= 2500:
        puan += 15
    elif butce >= 1500:
        puan += 10
    elif butce >= 1000:
        puan += 5
    
    # Yanıt durumu
    durum = lead.get("durum", "yeni")
    if durum == "gorusme":
        puan += 20
    elif durum == "yanit_verdi":
        puan += 10
    elif durum == "ilgilenmiyor":
        puan -= 30
    elif durum == "mesaj_gonderildi":
        puan += 2
    
    return max(0, min(100, puan))

# =====================================================================
# ANALİZ FONKSİYONLARI
# =====================================================================
def sektor_istatistik(hafiza):
    """Her sektör için lead ve yanıt sayısını hesaplar."""
    istatistik = {}
    
    for sektor_adi in SEKTORLER.keys():
        leadlar = [l for l in hafiza["leadlar"] if l.get("sektor") == sektor_adi]
        
        toplam = len(leadlar)
        mesaj_gonderilen = len([l for l in leadlar if l.get("durum") in ["mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor"]])
        yanit_veren = len([l for l in leadlar if l.get("durum") in ["yanit_verdi", "gorusme"]])
        gorusme = len([l for l in leadlar if l.get("durum") == "gorusme"])
        ilgilenmeyen = len([l for l in leadlar if l.get("durum") == "ilgilenmiyor"])
        
        yanit_orani = (yanit_veren / mesaj_gonderilen * 100) if mesaj_gonderilen > 0 else 0
        
        istatistik[sektor_adi] = {
            "toplam": toplam,
            "mesaj_gonderilen": mesaj_gonderilen,
            "yanit_veren": yanit_veren,
            "gorusme": gorusme,
            "ilgilenmeyen": ilgilenmeyen,
            "yanit_orani": round(yanit_orani, 1),
        }
    
    return istatistik

def genel_istatistik(hafiza):
    """Toplam istatistikleri hesaplar."""
    toplam = len(hafiza["leadlar"])
    if toplam == 0:
        return {
            "toplam_lead": 0, "gonderilen": 0, "yanit": 0,
            "gorusme": 0, "yanit_orani": 0, "gorusme_orani": 0
        }
    
    gonderilen = len([l for l in hafiza["leadlar"] if l.get("durum") in ["mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor"]])
    yanit = len([l for l in hafiza["leadlar"] if l.get("durum") in ["yanit_verdi", "gorusme"]])
    gorusme = len([l for l in hafiza["leadlar"] if l.get("durum") == "gorusme"])
    
    return {
        "toplam_lead": toplam,
        "gonderilen": gonderilen,
        "yanit": yanit,
        "gorusme": gorusme,
        "yanit_orani": round((yanit / gonderilen * 100) if gonderilen > 0 else 0, 1),
        "gorusme_orani": round((gorusme / gonderilen * 100) if gonderilen > 0 else 0, 1),
    }

# =====================================================================
# CSV İÇE / DIŞA AKTARMA
# =====================================================================
def leadlari_csv_olarak_indir(hafiza):
    """Lead'leri CSV olarak döndürür (indirme için)."""
    if not hafiza["leadlar"]:
        return None
    
    df = pd.DataFrame(hafiza["leadlar"])
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

def csv_yukle_isle(dosya_icerigi):
    """Yüklenen CSV dosyasını işler."""
    try:
        df = pd.read_csv(io.BytesIO(dosya_icerigi))
        leadlar = df.to_dict("records")
        return leadlar
    except Exception as e:
        st.error(f"CSV okuma hatası: {e}")
        return [] # =====================================================================
# ARAYÜZ — GİRİŞ
# =====================================================================
if "giris" not in st.session_state:
    st.session_state.giris = False

if not st.session_state.giris:
    st.title("🔒 Lead Yönetim Sistemi")
    st.caption("5 sektör — potansiyel müşteri yönetimi ve mesaj üretimi")
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
# HAFIZA
# =====================================================================
hafiza = get_hafiza()

if not hafiza["leadlar"]:
    leadlari_yukle(hafiza)
if not hafiza["mesajlar"]:
    mesajlari_yukle(hafiza)

# =====================================================================
# SOL MENÜ
# =====================================================================
st.sidebar.markdown("### 👤 Cuma Babacan")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menü",
    [
        "📊 Panel",
        "➕ Lead Ekle",
        "📋 Lead Listesi",
        "✉️ Mesaj Üret",
        "📈 İstatistikler",
        "📁 CSV İçe/Dışa",
        "📝 Sektör Bilgileri"
    ]
)

if st.sidebar.button("🚪 Çıkış"):
    st.session_state.giris = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Toplam lead: {len(hafiza['leadlar'])}")

# =====================================================================
# 1. PANEL
# =====================================================================
if menu == "📊 Panel":
    st.title("📊 Lead Yönetim Paneli")
    st.caption("5 sektör odaklı potansiyel müşteri yönetimi")
    st.markdown("---")
    
    # Genel istatistik
    genel = genel_istatistik(hafiza)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Toplam Lead", genel["toplam_lead"])
    c2.metric("✉️ Mesaj Gönderilen", genel["gonderilen"])
    c3.metric("💬 Yanıt Veren", genel["yanit"])
    c4.metric("🤝 Görüşme", genel["gorusme"])
    
    st.markdown("---")
    
    st.subheader("📈 Genel Durum")
    c1, c2 = st.columns(2)
    c1.metric("Yanıt Oranı", f"{genel['yanit_orani']}%")
    c2.metric("Görüşme Oranı", f"{genel['gorusme_orani']}%")
    
    st.markdown("---")
    
    st.subheader("🎯 Sektör Bazında Durum")
    sektor_ist = sektor_istatistik(hafiza)
    
    df_sektor = pd.DataFrame([
        {
            "Sektör": sektor,
            "Toplam": v["toplam"],
            "Mesaj": v["mesaj_gonderilen"],
            "Yanıt": v["yanit_veren"],
            "Görüşme": v["gorusme"],
            "Yanıt %": f"{v['yanit_orani']}%",
        }
        for sektor, v in sektor_ist.items()
    ])
    st.dataframe(df_sektor, use_container_width=True, hide_index=True)

# =====================================================================
# 2. LEAD EKLE
# =====================================================================
elif menu == "➕ Lead Ekle":
    st.title("➕ Yeni Lead Ekle")
    st.markdown("---")
    
    with st.form("lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            isim = st.text_input("Ad Soyad *")
            firma = st.text_input("Firma Adı")
            telefon = st.text_input("Telefon")
        with col2:
            email = st.text_input("E-posta")
            linkedin = st.text_input("LinkedIn Profil URL")
            sehir = st.text_input("Şehir")
        
        col3, col4 = st.columns(2)
        with col3:
            sektor = st.selectbox("Sektör *", list(SEKTORLER.keys()))
            calisan = st.number_input("Çalışan Sayısı", 0, 500, 1)
        with col4:
            butce = st.number_input("Tahmini Bütçe (TL/ay)", 0, 10000, 1500)
            durum = st.selectbox("Durum", ["yeni", "mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor", "müşteri"])
        
        notlar = st.text_area("Notlar", height=100)
        
        submitted = st.form_submit_button("💾 Lead Ekle", type="primary")
        
        if submitted:
            if not isim.strip():
                st.error("İsim zorunlu!")
            else:
                yeni_lead = {
                    "id": len(hafiza["leadlar"]) + 1,
                    "isim": isim.strip(),
                    "firma": firma.strip(),
                    "telefon": telefon.strip(),
                    "email": email.strip(),
                    "linkedin": linkedin.strip(),
                    "sehir": sehir.strip(),
                    "sektor": sektor,
                    "calisan_sayisi": calisan,
                    "butce": butce,
                    "durum": durum,
                    "notlar": notlar.strip(),
                    "eklenme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                hafiza["leadlar"].append(yeni_lead)
                leadlari_kaydet(hafiza)
                st.success(f"✅ {isim} eklendi!")
                st.rerun()
    
    st.markdown("---")
    st.info("💡 İpucu: LinkedIn'de profil bulduğunuzda ismi, firmayı ve profil URL'sini buraya ekleyin.")

# =====================================================================
# 3. LEAD LİSTESİ
# =====================================================================
elif menu == "📋 Lead Listesi":
    st.title("📋 Lead Listesi")
    st.markdown("---")
    
    if not hafiza["leadlar"]:
        st.info("Henüz lead yok. Sol menüden '➕ Lead Ekle' ile başlayın.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            sektor_filtre = st.selectbox("Sektör", ["Tümü"] + list(SEKTORLER.keys()))
        with col_f2:
            durum_filtre = st.selectbox("Durum", ["Tümü", "yeni", "mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor", "müşteri"])
        with col_f3:
            sirala = st.selectbox("Sırala", ["Yeni → Eski", "Eski → Yeni", "Puan (Yüksek)"])
        
        # Filtrele
        filtreli = hafiza["leadlar"].copy()
        if sektor_filtre != "Tümü":
            filtreli = [l for l in filtreli if l.get("sektor") == sektor_filtre]
        if durum_filtre != "Tümü":
            filtreli = [l for l in filtreli if l.get("durum") == durum_filtre]
        
        if sirala == "Puan (Yüksek)":
            filtreli.sort(key=lambda x: lead_puani(x), reverse=True)
        elif sirala == "Yeni → Eski":
            filtreli.reverse()
        
        st.caption(f"Toplam {len(filtreli)} lead gösteriliyor.")
        
        for lead in filtreli:
            puan = lead_puani(lead)
            renk = "🟢" if puan >= 70 else "🟡" if puan >= 50 else "🔴"
            
            with st.expander(f"{renk} {lead['isim']} — {lead.get('sektor', '-')} (Puan: {puan})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Firma:** {lead.get('firma', '-') or '-'}")
                    st.markdown(f"**Telefon:** {lead.get('telefon', '-') or '-'}")
                    st.markdown(f"**E-posta:** {lead.get('email', '-') or '-'}")
                    st.markdown(f"**LinkedIn:** {lead.get('linkedin', '-') or '-'}")
                with col2:
                    st.markdown(f"**Şehir:** {lead.get('sehir', '-') or '-'}")
                    st.markdown(f"**Çalışan:** {lead.get('calisan_sayisi', 0)}")
                    st.markdown(f"**Bütçe:** {lead.get('butce', 0)} TL/ay")
                    st.markdown(f"**Durum:** `{lead.get('durum', 'yeni')}`")
                
                if lead.get("notlar"):
                    st.markdown(f"**Notlar:** {lead['notlar']}")
                
                st.caption(f"Eklendi: {lead.get('eklenme_tarihi', '-')}")
                
                st.markdown("---")
                
                # Durum güncelle
                col_d1, col_d2 = st.columns([3, 1])
                with col_d1:
                    yeni_durum = st.selectbox(
                        "Durumu Güncelle",
                        ["yeni", "mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor", "müşteri"],
                        index=["yeni", "mesaj_gonderildi", "yanit_verdi", "gorusme", "ilgilenmiyor", "müşteri"].index(lead.get("durum", "yeni")),
                        key=f"durum_{lead['id']}"
                    )
                with col_d2:
                    st.write("")
                    st.write("")
                    if st.button("💾 Kaydet", key=f"kaydet_{lead['id']}"):
                        for i, l in enumerate(hafiza["leadlar"]):
                            if l["id"] == lead["id"]:
                                hafiza["leadlar"][i]["durum"] = yeni_durum
                                break
                        leadlari_kaydet(hafiza)
                        st.success("Güncellendi!")
                        st.rerun()
                
                # Sil
                if st.button(f"🗑️ Sil", key=f"sil_{lead['id']}"):
                    hafiza["leadlar"] = [l for l in hafiza["leadlar"] if l["id"] != lead["id"]]
                    leadlari_kaydet(hafiza)
                    st.success("Silindi!")
                    st.rerun()

# =====================================================================
# 4. MESAJ ÜRET
# =====================================================================
elif menu == "✉️ Mesaj Üret":
    st.title("✉️ Kişiselleştirilmiş Mesaj Üret")
    st.caption("Lead seç, kanal seç, mesajı kopyala, gönder.")
    st.markdown("---")
    
    if not hafiza["leadlar"]:
        st.warning("Önce lead ekleyin.")
    else:
        lead_secenekleri = {f"{l['isim']} ({l.get('sektor', '-')})": l for l in hafiza["leadlar"]}
        secili = st.selectbox("Lead Seç", list(lead_secenekleri.keys()))
        lead = lead_secenekleri[secili]
        
        kanal = st.radio("Kanal", ["linkedin", "email"], horizontal=True)
        
        sektor = lead.get("sektor", "")
        
        if sektor in MESAJ_SABLONLARI:
            mesaj = mesaj_uret(sektor, lead, kanal)
            
            st.markdown("### 📝 Üretilen Mesaj")
            st.text_area("Mesajı kopyalayın:", mesaj, height=300, key="mesaj_uret")
            
            st.markdown("---")
            st.info(f"""
            **Nasıl Göndereceksiniz?**
            
            1. Yukarıdaki mesajı **tamamen seçin ve kopyalayın**
            2. LinkedIn'de {lead['isim']} profilini açın
            3. **"Mesaj"** butonuna tıklayın
            4. Kopyaladığınız mesajı **yapıştırın ve gönderin**
            5. Geri gelin, durumu **"mesaj_gonderildi"** olarak güncelleyin
            
            ⚠️ Aynı anda 20+ kişiye mesaj atmayın. LinkedIn hesabınız kısıtlanır.
            Günde **10-15 mesaj** ideal.
            """)
            
            # Mesajı kaydet
            if st.button("✅ Bu Mesajı Gönderdim (Kaydet)"):
                hafiza["mesajlar"].append({
                    "lead_id": lead["id"],
                    "isim": lead["isim"],
                    "sektor": sektor,
                    "kanal": kanal,
                    "mesaj": mesaj,
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                # Durumu güncelle
                for i, l in enumerate(hafiza["leadlar"]):
                    if l["id"] == lead["id"]:
                        hafiza["leadlar"][i]["durum"] = "mesaj_gonderildi"
                        break
                leadlari_kaydet(hafiza)
                mesajlari_kaydet(hafiza)
                st.success(f"✅ {lead['isim']} için mesaj kaydedildi.")
                st.rerun()
        else:
            st.warning(f"{sektor} için şablon bulunamadı.")

# =====================================================================
# 5. İSTATİSTİKLER
# =====================================================================
elif menu == "📈 İstatistikler":
    st.title("📈 Detaylı İstatistikler")
    st.markdown("---")
    
    if not hafiza["leadlar"]:
        st.info("Henüz veri yok.")
    else:
        sektor_ist = sektor_istatistik(hafiza)
        
        st.subheader("🎯 Sektör Bazında Performans")
        
        for sektor, v in sektor_ist.items():
            with st.expander(f"**{sektor}** — {v['toplam']} lead, {v['yanit_veren']} yanıt ({v['yanit_orani']}%)"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Toplam Lead", v["toplam"])
                c2.metric("Mesaj Gönderilen", v["mesaj_gonderilen"])
                c3.metric("Yanıt Veren", v["yanit_veren"])
                c4.metric("Görüşme", v["gorusme"])
                
                if v["mesaj_gonderilen"] > 0:
                    yanit_bar = v["yanit_veren"] / v["mesaj_gonderilen"]
                    st.progress(min(1.0, yanit_bar), text=f"Yanıt oranı: {v['yanit_orani']}%")
        
        st.markdown("---")
        st.subheader("📊 Grafik")
        
        df_grafik = pd.DataFrame([
            {"Sektör": sektor, "Yanıt Oranı": v["yanit_orani"]}
            for sektor, v in sektor_ist.items()
        ])
        st.bar_chart(df_grafik.set_index("Sektör"))

# =====================================================================
# 6. CSV İÇE / DIŞA
# =====================================================================
elif menu == "📁 CSV İçe/Dışa":
    st.title("📁 CSV İçe / Dışa Aktarma")
    st.markdown("---")
    
    st.subheader("📤 Dışa Aktar")
    st.caption("Lead listesini CSV olarak indirin. Excel'de açabilirsiniz.")
    
    if hafiza["leadlar"]:
        csv_data = leadlari_csv_olarak_indir(hafiza)
        if csv_data:
            st.download_button(
                "⬇️ Lead Listesini İndir (CSV)",
                data=csv_data,
                file_name=f"leadlar_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("İndirilecek lead yok.")
    
    st.markdown("---")
    st.subheader("📥 İçe Aktar")
    st.caption("CSV dosyası yükleyin. Sütun başlıkları: isim, firma, telefon, email, linkedin, sehir, sektor, calisan_sayisi, butce, durum, notlar")
    
    yuklenen = st.file_uploader("CSV Dosyası Seç", type=["csv"])
    
    if yuklenen:
        st.success(f"✅ {yuklenen.name} yüklendi.")
        leadlar_yeni = csv_yukle_isle(yuklenen.read())
        
        if leadlar_yeni:
            st.write(f"**{len(leadlar_yeni)} lead bulundu.**")
            st.dataframe(pd.DataFrame(leadlar_yeni).head(), use_container_width=True)
            
            if st.button("✅ Hepsini Ekle", type="primary"):
                for l in leadlar_yeni:
                    l["id"] = len(hafiza["leadlar"]) + 1
                    l.setdefault("eklenme_tarihi", datetime.now().strftime("%Y-%m-%d %H:%M"))
                    hafiza["leadlar"].append(l)
                leadlari_kaydet(hafiza)
                st.success(f"✅ {len(leadlar_yeni)} lead eklendi.")
                st.rerun()
    
    st.markdown("---")
    st.subheader("📋 Şablon İndir")
    st.caption("Boş şablon indirin, Excel'de doldurun, buradan yükleyin.")
    
    sablon_df = pd.DataFrame(columns=[
        "isim", "firma", "telefon", "email", "linkedin",
        "sehir", "sektor", "calisan_sayisi", "butce", "durum", "notlar"
    ])
    sablon_csv = sablon_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    
    st.download_button(
        "⬇️ Boş Şablon İndir",
        data=sablon_csv,
        file_name="lead_sablonu.csv",
        mime="text/csv"
    )

# =====================================================================
# 7. SEKTÖR BİLGİLERİ
# =====================================================================
elif menu == "📝 Sektör Bilgileri":
    st.title("📝 Hedef Sektör Bilgileri")
    st.caption("5 sektör — detaylı ihtiyaç, bütçe, problem analizi")
    st.markdown("---")
    
    for sektor_adi, s in SEKTORLER.items():
        with st.expander(f"🎯 **{sektor_adi}** — Bütçe: {s['butce_min']}-{s['butce_max']} TL/ay"):
            c1, c2, c3 = st.columns(3)
            c1.metric("İşletme Sayısı", f"{s['isletme_sayisi']:,}")
            c2.metric("Bütçe (min-max)", f"{s['butce_min']}-{s['butce_max']} TL")
            c3.metric("Kategori", s["kategori"])
            
            st.markdown("---")
            st.markdown(f"**🔍 LinkedIn Arama Kelimesi:** `{s['linkedin_arama']}`")
            st.markdown(f"**🎯 Hedef Kitle:** {s['hedef_kitle']}")
            
            st.markdown("**🎯 Ne İstiyor?**")
            for i in s["ihtiyaclar"]:
                st.markdown(f"- {i}")
            
            st.markdown(f"**❗ Problem:** {s['problem']}")
            st.markdown(f"**😤 Şikayet:** {s['sikayet']}")
            st.markdown(f"**🔧 Mevcut Çözüm:** {s['mevcut_cozum']}")
    
    st.markdown("---")
    st.info("""
    ### 🎯 Nasıl Kullanılır?
    
    1. **LinkedIn'de arama yapın:** Yukarıdaki `linkedin_arama` kelimesini kullanın
    2. **Profilleri inceleyin:** Hedef kitleye uyan kişileri bulun
    3. **Lead ekleyin:** "➕ Lead Ekle" menüsünden bilgileri girin
    4. **Mesaj üretin:** "✉️ Mesaj Üret" menüsünden kişiselleştirilmiş mesaj alın
    5. **LinkedIn'den gönderin:** Kopyala-yapıştır, gönder
    6. **Durumu güncelleyin:** Yanıt verirse güncelleyin
    7. **İstatistikleri takip edin:** Hangi sektör daha iyi yanıt veriyor
    """)
