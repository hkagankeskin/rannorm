import streamlit as st
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from io import BytesIO

st.set_page_config(page_title="RAN Analytics", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🔐 RAN Karar Destek Aracı</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        entered_password = st.text_input("Lütfen erişim şifresini giriniz", type="password")
        if st.button("Giriş Yap"):
            if entered_password == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre.")
    return False

def arka_plan_dosya_bulucu(yas):
    # Matematiksel okuma için yaşın bulunduğu CSV grubunu tespit eder (Sınıf etiketinden bağımsız)
    if 60 <= yas <= 83: return 1
    elif 84 <= yas <= 95: return 2
    elif 96 <= yas <= 107: return 3
    elif 108 <= yas <= 119: return 4
    elif 120 <= yas <= 131: return 5
    elif 132 <= yas <= 143: return 6
    elif 144 <= yas <= 155: return 7
    elif 156 <= yas <= 180: return 8
    else: return 1 

def bant_goster(t_puani):
    if t_puani <= 30:
        bant = "Çok Zayıf"; renk = "#ef4444"; dolu = 1
    elif t_puani <= 40:
        bant = "Zayıf"; renk = "#f97316"; dolu = 2
    elif t_puani <= 60:
        bant = "Normal"; renk = "#3b82f6"; dolu = 3
    elif t_puani <= 70:
        bant = "İyi"; renk = "#22c55e"; dolu = 4
    else:
        bant = "Çok İyi"; renk = "#16a34a"; dolu = 5

    kareler = ""
    for i in range(1, 6):
        if i <= dolu:
            kareler += f"<span style='background:{renk}; color:white; padding:2px 8px; margin:1px; border-radius:3px; font-size:0.8rem;'>■</span>"
        else:
            kareler += f"<span style='background:#e2e8f0; color:#e2e8f0; padding:2px 8px; margin:1px; border-radius:3px; font-size:0.8rem;'>■</span>"
    return f"{kareler} <span style='font-weight:600; color:{renk};'>{bant}</span>"

def t_skoru_grafigi(t_puani, persentil, baslik):
    fig, ax = plt.subplots(figsize=(4.2, 2.0))
    x = np.linspace(10, 90, 500)
    y = stats.norm.pdf(x, 50, 10)

    bantlar = [(10, 30, '#ef4444'), (30, 40, '#f97316'), (40, 60, '#3b82f6'), (60, 70, '#22c55e'), (70, 90, '#16a34a')]
    for lo, hi, renk in bantlar:
        mask = (x >= lo) & (x <= hi)
        ax.fill_between(x[mask], 0, y[mask], color=renk, alpha=0.25)
    ax.plot(x, y, color='#475569', linewidth=1)

    if t_puani >= 60: marker_renk = '#16a34a'
    elif t_puani <= 40: marker_renk = '#ef4444'
    else: marker_renk = '#eab308'

    t_clamped = max(10, min(90, t_puani))
    y_ogrenci = stats.norm.pdf(t_clamped, 50, 10)
    ax.axvline(t_clamped, color=marker_renk, linewidth=2.5)
    ax.plot(t_clamped, y_ogrenci, marker='v', color=marker_renk, markersize=11, zorder=5, markeredgecolor='#1e293b', markeredgewidth=0.8)
    ax.text(t_clamped, y_ogrenci + max(y)*0.10, f'T={t_puani:.1f}  (%{persentil:.1f})', ha='center', fontsize=10, fontweight='bold', color=marker_renk)

    ax.set_xlim(10, 90)
    ax.set_ylim(0, max(y)*1.30)
    ax.set_xticks([10, 30, 40, 50, 60, 70, 90])
    ax.set_yticks([])
    ax.spines[['left','top','right']].set_visible(False)
    ax.tick_params(axis='x', labelsize=7)
    ax.set_xlabel('T-Skoru', fontsize=8)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=110, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def sonuc_hesapla(df, yas_ay, ham_sure):
    df_yas = df[df['Aylik_Yas'] == yas_ay].copy()
    if df_yas.empty:
        return None
    df_yas['raw_numeric'] = pd.to_numeric(df_yas['raw'], errors='coerce')
    idx = (df_yas['raw_numeric'] - ham_sure).abs().idxmin()
    satir = df_yas.loc[idx]
    return {"t": satir['norm'], "p": satir['percentile']}

def egitsel_yorum_uret(sonuclar, yas_ay, aktif_testler, sinif_metni):
    satirlar = [f"Öğrenci, **{yas_ay} aylık** gelişim norm grubu baz alınarak (**{sinif_metni}** öğrencisi olarak) değerlendirilmiştir."]
    satirlar.append("**Test Bazında Değerlendirme:**")
    for test in aktif_testler:
        s = sonuclar.get(test)
        if not s: continue
        p = s["p"]
        t = s["t"]

        if t <= 40:
            satirlar.append(f"- **{test}:** Öğrencinin tepki hızı yalnızca akranlarının **%{p:.1f}**'inden daha iyidir. Bu, büyük çoğunluğun bu öğrenciden daha hızlı bir bilişsel otomatizasyona sahip olduğunu gösterir.")
        elif t <= 60:
            satirlar.append(f"- **{test}:** Öğrenci akranlarının **%{p:.1f}**'inden daha iyidir; gelişimsel beklentilerle uyumlu bir otomatizasyon hızı sergilemiştir.")
        else:
            satirlar.append(f"- **{test}:** Öğrenci akranlarının **%{p:.1f}**'inden daha iyidir. Bu durum, belirgin bir şekilde üstün bir okuma öncesi/okuma otomatizasyonuna işaret etmektedir.")

    zayif = [t for t in aktif_testler if sonuclar.get(t) and sonuclar[t]["t"] <= 40]
    iyi   = [t for t in aktif_testler if sonuclar.get(t) and sonuclar[t]["t"] > 60]

    satirlar.append("")
    satirlar.append("**Genel Özet:**")
    if iyi: satirlar.append(f"**Güçlü alanlar:** {', '.join(iyi)} testlerinde yaşitlarının üzerinde performans sergilemiştir.")
    if zayif: satirlar.append(f"**Dikkat gerektiren alanlar:** {', '.join(zayif)} testlerinde yavaşlık tespit edilmiştir. RAN hızındaki bu zayıflık okuma güçlüğüne işaret edebilir; pedagojik müdahale önerilir.")
    if not zayif: satirlar.append("Genel değerlendirmede RAN performansı yaş düzeyiyle uyumlu veya üzerindedir. Özel bir müdahale gereksinimi görülmemiştir.")

    return "\n\n".join(satirlar)

if check_password():
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
        .header-logo { height: 60px; border-radius: 8px; }
        h1 { color: #1e3a8a !important; font-family: 'Inter', sans-serif; font-weight: 700; margin: 0; }
        [data-testid="stMetricValue"] { color: #2563eb !important; font-size: 1.8rem !important; }
        hr { border-top: 1px solid #cbd5e1 !important; }
        </style>
        """, unsafe_allow_html=True)

    logo_url = "https://support.renaissance.com/servlet/rtaImage?eid=ka0Nx00000073KX&feoid=00NQg000006K5pm&refid=0EMQg00000IutXM"
    st.markdown(f"""
        <div class="header-container">
            <img src="{logo_url}" class="header-logo" alt="RAN Logo">
            <h1>RAN Analytics System</h1>
        </div>
        """, unsafe_allow_html=True)
    st.write("Hızlı Otomatik İsimlendirme (RAN) Eğitsel Karar Destek Aracı")

    @st.cache_data
    def load_data():
        norms = {}
        tum_testler = ["Sekil", "Renk", "Rakam", "Harf", "RAS2", "RAS3"]
        tum_siniflar = range(1, 9)
        
        for sinif in tum_siniflar:
            for test in tum_testler:
                dosya = f"RAN_{test}_Sinif{sinif}_Norm.csv"
                if os.path.exists(dosya):
                    norms[f"{test}_{sinif}"] = pd.read_csv(dosya)
        return norms

    norms = load_data()

    if not norms:
        st.error("Sistem Hatası: Hiçbir norm dosyası (.csv) bulunamadı. Lütfen GitHub deponuza dosyaları yükleyin.")
    else:
        st.sidebar.subheader("⚙️ Parametreler")
        
        # SINIF VE YAŞ SEÇİMİ TEKRAR BAĞIMSIZ HALE GETİRİLDİ
        secilen_sinif = st.sidebar.selectbox("Öğrenci Sınıfı", range(1, 9), format_func=lambda x: f"{x}. Sınıf")
        yas_ay = st.sidebar.slider("Öğrenci Yaşı (Ay)", 60, 180, 84)
        
        # Arka planda okunacak dosyayı yaş belirler (Sınıfın ne seçildiğinden bağımsız)
        dosya_index = arka_plan_dosya_bulucu(yas_ay)

        st.sidebar.divider()
        st.sidebar.subheader("⏱️ Test Süreleri (Saniye)")
        st.sidebar.caption("Uygulanmayan test için 0 bırakın.")

        sure_sekil = st.sidebar.number_input("Şekil", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        sure_renk  = st.sidebar.number_input("Renk",  min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        
        # Pedagojik olarak öğretmenin seçtiği "Sınıf" dikkate alınır
        if secilen_sinif == 1:
            st.sidebar.caption("⚠️ 1. Sınıf öğrencisi: Alfanümerik testler isteğe bağlıdır.")
        
        sure_sayi = st.sidebar.number_input("Rakam", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        sure_harf = st.sidebar.number_input("Harf", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        sure_ras2 = st.sidebar.number_input("2'li RAS", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
        sure_ras3 = st.sidebar.number_input("3'lü RAS", min_value=0.0, max_value=300.0, value=0.0, step=0.5)

        # Normlar yaşın işaret ettiği dosyadan (dosya_index) çekilir
        sureler = {
            "Şekil": (sure_sekil, f"Sekil_{dosya_index}"),
            "Renk":  (sure_renk,  f"Renk_{dosya_index}"),
            "Rakam": (sure_sayi,  f"Rakam_{dosya_index}"),
            "Harf":  (sure_harf,  f"Harf_{dosya_index}"),
            "2'li RAS": (sure_ras2, f"RAS2_{dosya_index}"),
            "3'lü RAS": (sure_ras3, f"RAS3_{dosya_index}"),
        }

        aktif = {t: (s, k) for t, (s, k) in sureler.items() if s > 0}

        if not aktif:
            st.info("👈 Sol panelden öğrenci sınıfı, yaşını ve test sürelerini girerek analizi başlatın.")
        else:
            sonuclar = {}
            for test, (sure, norm_key) in aktif.items():
                if norm_key in norms:
                    s = sonuc_hesapla(norms[norm_key], yas_ay, sure)
                    if s: sonuclar[test] = s
                else:
                    st.warning(f"⚠️ {yas_ay} ay için ({test}) CSV dosyası sistemde bulunamadı.")

            if sonuclar:
                st.divider()
                st.subheader("📊 Klinik Profil: Test Karşılaştırması")
                
                # 3'LÜ SATIRLAR HALİNDE GÖSTERME DÜZENİ
                test_listesi = list(sonuclar.keys())
                
                for i in range(0, len(test_listesi), 3):
                    chunk = test_listesi[i:i+3]
                    cols = st.columns(3)
                    
                    for idx, test in enumerate(chunk):
                        with cols[idx]:
                            st.markdown(f"### {test}")
                            metrik_col1, metrik_col2 = st.columns(2)
                            metrik_col1.metric("T-Skoru", f"{sonuclar[test]['t']:.1f}")
                            metrik_col2.metric("Persentil", f"%{sonuclar[test]['p']:.1f}")
                            
                            st.markdown(bant_goster(sonuclar[test]['t']), unsafe_allow_html=True)
                            st.image(t_skoru_grafigi(sonuclar[test]['t'], sonuclar[test]['p'], test), use_container_width=True)
                    st.write("") 

                st.divider()
                st.subheader("📝 Öğretmen/Uzman İçin Eğitsel Değerlendirme")
                # Rapor kısmına öğretmenin seçtiği sınıf gönderiliyor
                yorum = egitsel_yorum_uret(sonuclar, yas_ay, list(sonuclar.keys()), f"{secilen_sinif}. Sınıf")
                st.info(yorum)

    st.write("")
    st.divider()
    _, l_col1, l_col2, l_col3, _ = st.columns([1, 2, 2, 2, 1])
    with l_col1:
        if os.path.exists("hacettepe.svg"): st.image("hacettepe.svg", width=85)
    with l_col2:
        if os.path.exists("duzce.svg"): st.image("duzce.svg", width=140)
    with l_col3:
        if os.path.exists("Rlogo.svg"): st.image("Rlogo.svg", width=120)

    st.write("")
    st.markdown(
        "<div style='text-align: center; color: #374151; font-size: 0.90rem; margin-bottom: 6px;'>"
        "<strong>Proje Ekibi</strong><br>"
        "Prof. Dr. H. Kağan Keskin — Düzce Üniversitesi &nbsp;|&nbsp; "
        "Prof. Dr. Özay Karadağ — Hacettepe Üniversitesi"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 0.80rem;'>"
        "Bu ulusal norm sistemi (N=1696), sürekli normlama (continuous norming) yaklaşımı benimsenerek "
        "geliştirilmiştir. Ham puanlar, Hazen düzeltmesi (p = (sıra − 0.5) / n) ile persentil değerlerine dönüştürülmüş "
        "ve standart normal dağılımın ters kümülatif dağılım fonksiyonu (inverse CDF) ile T-puanlarına (M = 50, SD = 10) çevrilmiştir. "
        "Yaş ve ham puan arasındaki gelişimsel eğilim, üçüncü derece polinom regresyon (Ridge düzenlileştirme, α = 1.0) "
        "ile modellenmiştir (Keskin & Karadağ, 2026).</div>",
        unsafe_allow_html=True
    )
