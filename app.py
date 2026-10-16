import streamlit as st
import random
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Firsat Madencigi", layout="wide")

SEKTORLER = [
    {"isim": "Veteriner Klinikleri", "kategori": "Saglik",    "isletme": 12000,  "butce": 1500, "yazilim": 3},
    {"isim": "Dis Hekimleri",        "kategori": "Saglik",    "isletme": 25000,  "butce": 2000, "yazilim": 8},
    {"isim": "Psikologlar",          "kategori": "Saglik",    "isletme": 15000,  "butce": 800,  "yazilim": 4},
    {"isim": "Eczaneler",            "kategori": "Saglik",    "isletme": 28000,  "butce": 1200, "yazilim": 6},
    {"isim": "Avukatlar",            "kategori": "Hukuk",     "isletme": 50000,  "butce": 1500, "yazilim": 5},
    {"isim": "Muhasebeciler",        "kategori": "Muhasebe",  "isletme": 40000,  "butce": 1200, "yazilim": 7},
    {"isim": "Kuyumcular",           "kategori": "Perakende", "isletme": 35000,  "butce": 2500, "yazilim": 4},
    {"isim": "Emlakcilar",           "kategori": "Perakende", "isletme": 60000,  "butce": 800,  "yazilim": 12},
    {"isim": "Oto Galeriler",        "kategori": "Perakende", "isletme": 25000,  "butce": 1800, "yazilim": 8},
    {"isim": "Oto Servisleri",       "kategori": "Hizmet",    "isletme": 60000,  "butce": 1000, "yazilim": 6},
    {"isim": "Marangozlar",          "kategori": "Sanayi",    "isletme": 20000,  "butce": 800,  "yazilim": 2},
    {"isim": "Restoranlar",          "kategori": "Gida",      "isletme": 200000, "butce": 1500, "yazilim": 25},
    {"isim": "Kafeler",              "kategori": "Gida",      "isletme": 80000,  "butce": 800,  "yazilim": 20},
    {"isim": "Pastaneler",           "kategori": "Gida",      "isletme": 30000,  "butce": 1000, "yazilim": 5},
    {"isim": "Kasaplar",             "kategori": "Gida",      "isletme": 40000,  "butce": 700,  "yazilim": 3},
    {"isim": "Berberler",            "kategori": "Guzellik",  "isletme": 80000,  "butce": 500,  "yazilim": 8},
    {"isim": "Kuaforler",            "kategori": "Guzellik",  "isletme": 70000,  "butce": 700,  "yazilim": 8},
    {"isim": "Spor Salonlari",       "kategori": "Spor",      "isletme": 10000,  "butce": 2000, "yazilim": 7},
    {"isim": "Dugun Salonlari",      "kategori": "Etkinlik",  "isletme": 8000,   "butce": 1800, "yazilim": 4},
    {"isim": "Matbaalar",            "kategori": "Sanayi",    "isletme": 12000,  "butce": 1500, "yazilim": 3},
]

if "veriler" not in st.session_state:
    st.session_state.veriler = []
if "son_guncelleme" not in st.session_state:
    st.session_state.son_guncelleme = None


def tara():
    veriler = []
    for s in SEKTORLER:
        talep = random.randint(30, 95)
        eks = random.randint(20, 90)
        dh = random.randint(30, 90)
        talep_puan = min(100, talep * 0.5 + eks * 0.3 + dh * 0.2)
        sv = random.randint(50, 3000)
        aciliyet = min(100, sv // 10)
        isletme_puan = min(100, (s["isletme"] / 100000) * 100)
        butce_puan = min(100, (s["butce"] / 3000) * 100)
        odeme = isletme_puan * 0.4 + butce_puan * 0.6
        rekabet = max(0, 100 - s["yazilim"] * 4)
        toplam = talep_puan * 0.35 + odeme * 0.30 + aciliyet * 0.20 + rekabet * 0.15
        hazir = toplam >= 60 and odeme >= 50 and aciliyet >= 40 and rekabet >= 40
        veriler.append({
            "isim": s["isim"],
            "kategori": s["kategori"],
            "isletme": s["isletme"],
            "butce": s["butce"],
            "yazilim": s["yazilim"],
            "talep": round(talep_puan, 1),
            "odeme": round(odeme, 1),
            "aciliyet": aciliyet,
            "rekabet": rekabet,
            "toplam": round(toplam, 1),
            "hazir": hazir,
            "trend": random.choice(["yukseliyor", "sabit", "dusuyor"])
        })
    veriler.sort(key=lambda x: x["toplam"], reverse=True)
    st.session_state.veriler = veriler
    st.session_state.son_guncelleme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if "giris" not in st.session_state:
    st.session_state.giris = False

if not st.session_state.giris:
    st.title("Firsat Madenciligi Paneli")
    st.caption("20 sektor analizi - hangi sektor odemeye hazir?")
    k = st.text_input("Kullanici Adi")
    s = st.text_input("Sifre", type="password")
    if st.button("Giris Yap"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state.giris = True
            st.rerun()
        else:
            st.error("Hatali giris!")
    st.stop()

st.sidebar.markdown("### Cuma Babacan")
st.sidebar.markdown("---")

if st.sidebar.button("Taramayi Baslat", type="primary"):
    with st.spinner("20 sektor taraniyor..."):
        tara()
    st.sidebar.success("Bitti!")
    st.rerun()

if st.sidebar.button("Cikis"):
    st.session_state.giris = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Son: {st.session_state.son_guncelleme or 'Yok'}")

st.title("Firsat Madenciligi - 20 Sektor")
st.caption("Hangi sektor cozum bekliyor? Hangi sektor odemeye hazir?")
st.markdown("---")

if not st.session_state.veriler:
    st.info("Sol menuden Taramayi Baslat butonuna tiklayin.")
    st.stop()

veriler = st.session_state.veriler
hazir = [v for v in veriler if v["hazir"]]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Analiz", f"{len(veriler)} Sektor")
col2.metric("Hazir", f"{len(hazir)} Sektor")
col3.metric("En Yuksek", f"{veriler[0]['toplam']:.1f}")
col4.metric("Ortalama", f"{sum(v['toplam'] for v in veriler)/len(veriler):.1f}")

st.markdown("---")
st.subheader("Odemeye Hazir Sektorler")

if hazir:
    for v in hazir:
        with st.container(border=True):
            st.markdown(f"### {v['isim']}")
            st.caption(f"{v['kategori']} | Trend: {v['trend']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Puan", f"{v['toplam']:.1f}")
            c2.metric("Isletme", f"{v['isletme']:,}")
            c3.metric("Butce", f"{v['butce']} TL")
            c4.metric("Yazilim", v["yazilim"])
            st.caption(f"Talep: {v['talep']:.0f} | Odeme: {v['odeme']:.0f} | Aciliyet: {v['aciliyet']:.0f} | Rekabet: {v['rekabet']:.0f}")
else:
    st.info("Su an 4 kriteri de gecen sektor yok.")

st.markdown("---")
st.subheader("Tum Sektorler")

df = pd.DataFrame([{
    "Sira": i+1,
    "Sektor": v["isim"],
    "Kategori": v["kategori"],
    "Firsat": v["toplam"],
    "Talep": v["talep"],
    "Odeme": v["odeme"],
    "Aciliyet": v["aciliyet"],
    "Rekabet": v["rekabet"],
    "Trend": v["trend"],
    "Isletme": v["isletme"],
    "Butce": v["butce"],
    "Durum": "OK" if v["hazir"] else "-",
} for i, v in enumerate(veriler)])

st.dataframe(df, use_container_width=True, hide_index=True)
st.markdown("---")

st.subheader("Kategori Ozeti")
kat_dict = {}
for v in veriler:
    k = v["kategori"]
    if k not in kat_dict:
        kat_dict[k] = {"toplam": 0, "sayi": 0, "isletme": 0}
    kat_dict[k]["toplam"] += v["toplam"]
    kat_dict[k]["sayi"] += 1
    kat_dict[k]["isletme"] += v["isletme"]

df_kat = pd.DataFrame([{
    "Kategori": k,
    "Ortalama Puan": round(d["toplam"]/d["sayi"], 1),
    "Sektor Sayisi": d["sayi"],
    "Toplam Isletme": d["isletme"],
} for k, d in kat_dict.items()]).sort_values("Ortalama Puan", ascending=False)

st.dataframe(df_kat, use_container_width=True, hide_index=True)
st.markdown("---")

st.subheader("En Iyi 5 Sektor")
for i, v in enumerate(veriler[:5], 1):
    with st.expander(f"#{i} {v['isim']} - Puan: {v['toplam']:.1f}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Kategori:** {v['kategori']}")
            st.markdown(f"**Trend:** {v['trend']}")
            st.markdown(f"**Isletme:** {v['isletme']:,}")
            st.markdown(f"**Butce:** {v['butce']} TL")
        with col2:
            st.markdown(f"**Talep:** {v['talep']:.0f}/100")
            st.markdown(f"**Odeme:** {v['odeme']:.0f}/100")
            st.markdown(f"**Aciliyet:** {v['aciliyet']:.0f}/100")
            st.markdown(f"**Rekabet:** {v['rekabet']:.0f}/100")
        st.markdown(f"**Potansiyel Gelir:** {v['isletme'] * v['butce'] * 0.001:,.0f} TL")
        if v["hazir"]:
            st.success("Bu sektor odemeye hazir")
        else:
            st.warning("Bazi kriterler yetersiz")
