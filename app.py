import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="RAN / RAS Karar Destek ve Norm Değerlendirme Sistemi",
    page_icon="⏱️",
    layout="wide"
)

# ----------------------------------------------------
# 1. VERİLERİN YÜKLENMESİ
# ----------------------------------------------------
@st.cache_data
def load_norm_data():
    files = {
        "Sekil": "RAN_Sekil_Norm.csv",
        "Renk": "RAN_Renk_Norm.csv",
        "Rakam": "RAN_Rakam_Norm.csv",
        "Harf": "RAN_Harf_Norm.csv",
        "RAS2": "RAN_RAS2_Norm.csv",
        "RAS3": "RAN_RAS3_Norm.csv"
    }
    dfs = {}
    for test_key, filename in files.items():
        if os.path.exists(filename):
            dfs[test_key] = pd.read_csv(filename)
        elif os.path.exists(os.path.join("Norm_Verileri", filename)):
            dfs[test_key] = pd.read_csv(os.path.join("Norm_Verileri", filename))
        else:
            dfs[test_key] = None
    return dfs

norm_dfs = load_norm_data()

# ----------------------------------------------------
# 2. HESAPLAMA VE DEĞERLENDİRME FONKSİYONLARI
# ----------------------------------------------------
def sonuc_hesapla(df, yas_ay, ham_sure):
    if df is None:
        return None
    df_yas = df[df['Aylik_Yas'] == yas_ay].copy()
    if df_yas.empty:
        return None
    
    df_yas['raw_diff'] = (df_yas['raw'] - ham_sure).abs()
    en_yakin = df_yas.loc[df_yas['raw_diff'].idxmin()]
    return {
        "norm": float(en_yakin['norm']),
        "percentile": float(en_yakin['percentile'])
    }

def yorum_uret(p_skoru):
    if p_skoru <= 15.0:
        return ("Bilişsel otomatizasyon hızında belirgin yavaşlık gözlemlenmiştir. "
                "Okuma akıcılığı/otomatizasyon güçlüğü riski bulunmaktadır; pedagojik müdahale önerilir.", "🔴")
    elif p_skoru <= 25.0:
        return ("Hız performansı sınır düzeydedir; gelişimsel takip ve destekleyici çalışmalar önerilir.", "🟠")
    elif p_skoru <= 75.0:
        return ("Gelişimsel beklentilerle tam uyumlu bir tepki hızı sergilemiştir.", "🟢")
    else:
        return ("Akran grubuna göre belirgin düzeyde hızlı ve üstün otomatizasyon performansı sergilemiştir.", "🔵")

# ----------------------------------------------------
# 3. YAN PANEL (KULLANICI GİRİŞLERİ)
# ----------------------------------------------------
st.sidebar.header("📋 Öğrenci ve Test Bilgileri")

yas_ay = st.sidebar.number_input(
    "Öğrencinin Yaşı (Ay Olarak):",
    min_value=60,
    max_value=168,
    value=84,
    step=1,
    help="Ulusal normlarımız 60-168 ay arasını kapsamaktadır."
)

st.sidebar.markdown(f"**Gelişim Dönemi:** {yas_ay // 12} Yaş {yas_ay % 12} Ay")

st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Test Süreleri (Saniye)")

# Şekil ve Renk her zaman aktif (60-168 ay)
sekil_sure = st.sidebar.number_input("Şekil Testi Süresi (sn):", min_value=0.0, max_value=200.0, value=50.0, step=0.5)
renk_sure = st.sidebar.number_input("Renk Testi Süresi (sn):", min_value=0.0, max_value=200.0, value=55.0, step=0.5)

# Alfanümerik testler için 84 ay pedagojik eşik kontrolü
alfanumerik_aktif = yas_ay >= 84

if alfanumerik_aktif:
    rakam_sure = st.sidebar.number_input("Rakam Testi Süresi (sn):", min_value=0.0, max_value=200.0, value=25.0, step=0.5)
    harf_sure = st.sidebar.number_input("Harf Testi Süresi (sn):", min_value=0.0, max_value=200.0, value=25.0, step=0.5)
    ras2_sure = st.sidebar.number_input("2'li RAS Süresi (sn):", min_value=0.0, max_value=200.0, value=28.0, step=0.5)
    ras3_sure = st.sidebar.number_input("3'lü RAS Süresi (sn):", min_value=0.0, max_value=200.0, value=30.0, step=0.5)
else:
    rakam_sure = None
    harf_sure = None
    ras2_sure = None
    ras3_sure = None
    st.sidebar.info("🔒 **Harf, Rakam ve RAS testleri kilitlidir.** (Ulusal protokol gereği alfanümerik testler 84 aydan itibaren uygulanmaktadır).")

# ----------------------------------------------------
# 4. ANA EKRAN VE RAPORLAMA
# ----------------------------------------------------
st.title("⏱️ RAN / RAS Ulusal Norm Değerlendirme Raporu")

if not alfanumerik_aktif:
    st.warning(
        f"ℹ️ **Pedagojik Not:** Öğrenci **{yas_ay} aylıktır** (Okul Öncesi / 1. Sınıf dönemi). "
        "Bu yaş grubunda henüz formal okuma-yazma ve harf/rakam otomatizasyonu zorunlu olmadığından, "
        "bilimsel ulusal standarda göre **yalnızca Alfanümerik Olmayan (Şekil ve Renk)** testleri değerlendirilmektedir."
    )
else:
    st.success(f"✅ Öğrenci **{yas_ay} aylıktır** (2. Sınıf ve üzeri). 6 temel RAN/RAS testinin tamamı değerlendirmeye uygundur.")

st.markdown("---")

test_listesi = [
    ("Sekil", "Şekil Testi", sekil_sure),
    ("Renk", "Renk Testi", renk_sure),
]

if alfanumerik_aktif:
    test_listesi.extend([
        ("Rakam", "Rakam Testi", rakam_sure),
        ("Harf", "Harf Testi", harf_sure),
        ("RAS2", "2'li RAS Testi", ras2_sure),
        ("RAS3", "3'lü RAS Testi", ras3_sure),
    ])

sonuclar = []
risk_alanlari = []

for key, label, sure in test_listesi:
    if sure is not None and sure > 0:
        res = sonuc_hesapla(norm_dfs[key], yas_ay, sure)
        if res:
            yorum, simge = yorum_uret(res['percentile'])
            sonuclar.append({
                "Test": label,
                "Ham Süre (sn)": f"{sure:.1f}",
                "T-Skoru": f"{res['norm']:.1f}",
                "Persentil (%)": f"%{res['percentile']:.1f}",
                "Durum": f"{simge} {yorum}"
            })
            if res['percentile'] <= 15.0:
                risk_alanlari.append(label)

if sonuclar:
    st.subheader("📊 Test Bazında Değerlendirme Tablosu")
    df_sonuc = pd.DataFrame(sonuclar)
    st.table(df_sonuc)

    st.subheader("📝 Genel Değerlendirme Özeti")
    if risk_alanlari:
        st.error(f"⚠️ **Dikkat Gerektiren Alanlar:** {', '.join(risk_alanlari)} testlerinde belirgin yavaşlık tespit edilmiştir. "
                 f"Bu durum bilişsel otomatizasyon güçlüğüne veya okuma riski göstergelerine işaret edebilir; hedefe yönelik pedagojik müdahale önerilir.")
    else:
        st.success("🎉 **Genel Profil:** Tüm uygulanan testlerde bilişsel isimlendirme ve otomatizasyon hızları yaş akran grubu gelişimsel beklentileriyle uyumludur.")
else:
    st.error("Hesaplama yapılamadı. Lütfen norm CSV dosyalarının proje dizininde bulunduğundan emin olun.")
