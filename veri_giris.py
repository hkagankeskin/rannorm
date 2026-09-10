import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="RAN Ulusal Norm - Saha Telemetri Paneli",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DERİN KOYU BİLİŞSEL HUD CSS ---
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');

  /* Genel Arka Plan ve Metin */
  .stApp {
      background-color: #0a0f1d !important;
      color: #f8fafc !important;
      font-family: 'Inter', sans-serif !important;
  }

  /* Tüm Metin ve Sayı Giriş Kutuları */
  div[data-baseweb="input"] {
      background-color: #0f172a !important;
      border: 1px solid rgba(56, 189, 248, 0.25) !important;
      border-radius: 8px !important;
  }
  div[data-baseweb="input"] input {
      background-color: #0f172a !important;
      color: #f8fafc !important;
  }
  div[data-baseweb="input"] input::placeholder {
      color: #64748b !important;
  }

  /* Selectbox / Açılır Menüler */
  div[data-baseweb="select"] > div {
      background-color: #0f172a !important;
      border: 1px solid rgba(56, 189, 248, 0.25) !important;
      color: #f8fafc !important;
      border-radius: 8px !important;
  }
  div[data-baseweb="select"] * {
      color: #f8fafc !important;
  }

  /* Kronometre Sayı Girişleri (Dijital Sayaç Fontu) */
  input[type="number"] {
      font-family: 'JetBrains Mono', monospace !important;
      font-weight: 700 !important;
      font-size: 18px !important;
      color: #38bdf8 !important;
      text-align: center !important;
  }

  /* Form Başlıkları / Etiketler */
  label p {
      font-size: 11px !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.5px !important;
      color: #94a3b8 !important;
  }

  /* Buton Stili (Neon Gradyan) */
  div.stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #0284c7, #2563eb) !important;
      border: 1px solid rgba(56, 189, 248, 0.4) !important;
      color: #ffffff !important;
      border-radius: 10px !important;
      font-weight: 600 !important;
      font-size: 14px !important;
      letter-spacing: 0.5px !important;
      box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4) !important;
      transition: all 0.2s ease !important;
  }
  div.stButton > button[kind="primary"]:hover {
      box-shadow: 0 6px 25px rgba(56, 189, 248, 0.7) !important;
      transform: translateY(-1px) !important;
  }

  /* Telemetri Kart Başlıkları */
  .section-header {
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-left: 4px solid #38bdf8;
      padding: 8px 14px;
      border-radius: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
  }
  .section-header span.title {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #38bdf8;
  }
  .section-header span.tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #64748b;
  }

  /* Yaş Göstergesi Kartı */
  .telemetry-age-box {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.08), rgba(15, 23, 42, 0.8));
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 10px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 14px 0;
  }

  /* Sağ Panel Kota Tablosu (Demodaki Koyu Tasarım) */
  .hud-table-wrapper {
      max-height: 480px;
      overflow-y: auto;
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 8px;
      background: #0f172a;
  }
  .hud-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      text-align: left;
  }
  .hud-table thead th {
      background: #0a0f1d;
      color: #94a3b8;
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 600;
      padding: 10px 14px;
      position: sticky;
      top: 0;
      border-bottom: 1px solid rgba(56, 189, 248, 0.2);
  }
  .hud-table tbody tr {
      border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  }
  .hud-table tbody tr:hover {
      background: rgba(56, 189, 248, 0.06);
  }
  .hud-table td {
      padding: 8px 14px;
      font-family: 'JetBrains Mono', monospace;
      color: #f8fafc;
  }
  .badge-open {
      color: #10b981;
      background: rgba(16, 185, 129, 0.12);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .badge-target {
      color: #f59e0b;
      background: rgba(245, 158, 11, 0.12);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid rgba(245, 158, 11, 0.3);
  }
  .badge-locked {
      color: #f43f5e;
      background: rgba(244, 63, 94, 0.12);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid rgba(244, 63, 94, 0.3);
  }
</style>
""", unsafe_allow_html=True)

# --- OKUL LİSTESİ ---
OKUL_LISTESI = {
    "Alt": [
        "Karapürçek Abdülhamit Han Anaokulu (ALTINDAĞ)",
        "Altındağ Belediyesi Nenehatun Anaokulu (ALTINDAĞ)",
        "Piri Reis Anaokulu (ALTINDAĞ)",
        "Karapürçek Şehit Ferhat Muratoğlu İlkokulu (ALTINDAĞ)",
        "Hayme Hatun İlkokulu (ALTINDAĞ)",
        "Şehit Harun Aydın İlkokulu (ALTINDAĞ)",
        "Karapürçek Şehit Osman Kablan Ortaokulu (ALTINDAĞ)",
        "Ertuğrul Gazi Ortaokulu (ALTINDAĞ)",
        "Yusuf Has Hacip Ortaokulu (ALTINDAĞ)",
        "Neşeli Çocuklar Anaokulu (MAMAK)",
        "Habibe-Mehmet Kaya Anaokulu (MAMAK)",
        "İmirzalıoğlu Ganime Hanım Anaokulu (MAMAK)",
        "Mehmetçik İlkokulu (MAMAK)",
        "Gülveren Şehit Umut Coşkun İlkokulu (MAMAK)",
        "Mehmet Rıfat Börekçi İlkokulu (MAMAK)",
        "Mamak Ortaokulu (MAMAK)",
        "Mehmet Çekiç Ortaokulu (MAMAK)",
        "Yavuz Sultan Selim Ortaokulu (MAMAK)"
    ],
    "Orta": [
        "Mehmetçik Anaokulu (ETİMESGUT)",
        "Şehit Mehmet Çetin İlkokulu (ETİMESGUT)",
        "Bağlıca Ortaokulu (ETİMESGUT)",
        "Çiğdem Çiçeği Anaokulu (SİNCAN)",
        "Adalet Anaokulu (SİNCAN)",
        "Hayriye Andiçen Anaokulu (SİNCAN)",
        "Cemal Yüksel İlkokulu (SİNCAN)",
        "Dr. Nurettin - Beyhan Elbir İlkokulu (SİNCAN)",
        "Şehit Emre Karagöz İlkokulu (SİNCAN)",
        "Dr. Nurettin - Beyhan Elbir Ortaokulu (SİNCAN)",
        "Özkent Akbilek Ortaokulu (SİNCAN)",
        "Semiha İsen Ortaokulu (SİNCAN)"
    ],
    "Üst": [
        "Eryaman Başak Anaokulu (ETİMESGUT)",
        "Şehit Eyyüp Oğuz Anaokulu (ETİMESGUT)",
        "Eryaman Türkkent İlkokulu (ETİMESGUT)",
        "Cahit Zarifoğlu İlkokulu (ETİMESGUT)",
        "Cenk Yakın Ortaokulu (ETİMESGUT)",
        "Eryaman Kooperatifler Birliği Ortaokulu (ETİMESGUT)",
        "Şaziye Tekışık Anaokulu (ÇANKAYA)",
        "Beytepe Jandarma Lojmanları Anaokulu (ÇANKAYA)",
        "Zübeyde Hanım Anaokulu (ÇANKAYA)",
        "Beytepe İlkokulu (ÇANKAYA)",
        "Türk-İş Blokları İlkokulu (ÇANKAYA)",
        "Ulubatlı Hasan İlkokulu (ÇANKAYA)",
        "Şehit Battal İlgün İlkokulu (ÇANKAYA)",
        "Beytepe Ortaokulu (ÇANKAYA)",
        "T Emlak Bankası Ortaokulu (ÇANKAYA)",
        "Fevzi Özbey Ortaokulu (ÇANKAYA)",
        "Necdet Seçkinöz Ortaokulu (ÇANKAYA)"
    ]
}

# --- GOOGLE SHEETS BAĞLANTISI ---
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = {
        "type": st.secrets["connections"]["gsheets"]["type"],
        "project_id": st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"],
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"],
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

def get_data():
    try:
        client = get_gspread_client()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.worksheet("Sheet1")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

df_mevcut = get_data()

if "kaydediliyor" not in st.session_state:
    st.session_state.kaydediliyor = False

# --- ÜST TELEMETRİ BARI ---
st.markdown("""
<div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.2); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #f8fafc; letter-spacing: 0.5px;">
            ⚡ RAN ULUSAL NORM ÇALIŞMASI <span style="font-size: 10px; padding: 2px 8px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border-radius: 4px; border: 1px solid rgba(56,189,248,0.3);">SAHA HUD V2</span>
        </h3>
        <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8;">Bilişsel İsimlendirme Hızı ve Örneklem Veri Toplama İstasyonu</p>
    </div>
    <div style="display: flex; gap: 10px;">
        <span style="font-family: 'JetBrains Mono'; font-size: 11px; padding: 4px 10px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; border-radius: 6px;">● SİSTEM: AKTİF</span>
        <span style="font-family: 'JetBrains Mono'; font-size: 11px; padding: 4px 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; border-radius: 6px;">PROTOKOL: 60-180 AY</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_sol, col_sag = st.columns([1.15, 0.85], gap="large")

# -----------------------------------------
# SOL PANEL: DENEK VE SÜRE GİRİŞİ
# -----------------------------------------
with col_sol:
    st.markdown("""
    <div class="section-header">
        <span class="title">01. DENEK PROFİL & DEMOGRAFİ</span>
        <span class="tag">ID GİRİŞİ</span>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_o = st.columns(2)
    arastirmaci = col_a.text_input("Araştırmacı Kodu", placeholder="Örn: A-01").strip()
    ogrenci_kod = col_o.text_input("Öğrenci Kodu", placeholder="Örn: OKL-001-K").strip()

    col_c, col_s = st.columns(2)
    cinsiyet = col_c.selectbox("Cinsiyet", ["Kız", "Erkek"])
    sed = col_s.selectbox("Okul SED Türü", ["Alt", "Orta", "Üst"])

    secilen_okul = st.selectbox("Uygulama Yapılan Okul", OKUL_LISTESI.get(sed, ["Okul Bulunamadı"]))

    col_d, col_t = st.columns(2)
    dogum_tarihi = col_d.date_input("Doğum Tarihi", min_value=date(2008, 1, 1), max_value=date(2022, 12, 31), format="DD.MM.YYYY")
    test_tarihi = col_t.date_input("Test Tarihi", value=date.today(), format="DD.MM.YYYY")

    # Yaş ve Kota Telemetrisi
    yas_ay = None
    kota_durumu = "bekliyor"

    if dogum_tarihi and test_tarihi:
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
        yas_ay = (yil_farki * 12) + ay_farki

        if yas_ay < 60 or yas_ay > 180:
            st.error("❌ Bu öğrencinin yaşı (60 - 180 ay) örneklem kapsamı dışındadır.")
            kota_durumu = "gecersiz"
        else:
            if not df_mevcut.empty and "Yas_Ayi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut_ogrenci = len(df_mevcut[(df_mevcut["Yas_Ayi"] == yas_ay) & (df_mevcut["SED"] == sed)])
            else:
                mevcut_ogrenci = 0

            kalan_ihtiyac = max(0, 8 - mevcut_ogrenci)

            if mevcut_ogrenci >= 10:
                rozet_html = '<span style="color:#f43f5e; font-family:\'JetBrains Mono\'; font-weight:700;">● KOTA DOLDU (10/10)</span>'
                kota_durumu = "dolu"
            elif mevcut_ogrenci >= 8:
                rozet_html = '<span style="color:#f59e0b; font-family:\'JetBrains Mono\'; font-weight:700;">● HEDEF TAMAMLANDI (8/8)</span>'
                kota_durumu = "uyari"
            else:
                rozet_html = f'<span style="color:#10b981; font-family:\'JetBrains Mono\'; font-weight:700;">● KOTA AÇIK (KALAN: {kalan_ihtiyac})</span>'
                kota_durumu = "uygun"

            st.markdown(f"""
            <div class="telemetry-age-box">
                <div>
                    <div style="font-size:10px; font-weight:600; text-transform:uppercase; color:#64748b;">HESAPLANAN KRONOLOJİK YAŞ</div>
                    <div style="font-family:'JetBrains Mono'; font-size:26px; font-weight:700; color:#38bdf8;">{yas_ay} <span style="font-size:12px; color:#94a3b8;">AY</span></div>
                </div>
                <div>{rozet_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.markdown("""
    <div class="section-header">
        <span class="title">02. REAKSİYON & İSİMLENDİRME SÜRELERİ</span>
        <span class="tag" style="color:#f59e0b;">SANİYE (SN)</span>
    </div>
    """, unsafe_allow_html=True)

    if kota_durumu == "dolu":
        st.error("🔒 Bu yaş ve SED hücresi için veri girişi kilitlenmiştir.")
    elif not arastirmaci or not ogrenci_kod:
        st.info("ℹ️ Lütfen araştırmacı ve öğrenci kodunu giriniz.")
    elif kota_durumu in ["uygun", "uyari"]:
        c1, c2, c3, c4 = st.columns(4)
        sure_sekil = c1.number_input("1. Şekil", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        sure_renk  = c2.number_input("2. Renk",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        sure_sayi  = c3.number_input("3. Sayı",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)

        if yas_ay and yas_ay >= 83:
            sure_harf = c4.number_input("4. Harf (83+)", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        else:
            sure_harf = 0.0
            c4.markdown('<div style="text-align:center; padding-top:28px; font-size:11px; color:#64748b; font-family:\'JetBrains Mono\';">KİLİTLİ<br>(83+ AY)</div>', unsafe_allow_html=True)

        st.write("")
        kaydet = st.button("⚡ VERİYİ NORM HAVUZUNA İŞLE", use_container_width=True, type="primary", disabled=st.session_state.kaydediliyor)

        if kaydet:
            if sure_sekil < 10.0 or sure_renk < 10.0 or sure_sayi < 10.0 or (yas_ay and yas_ay >= 83 and sure_harf < 10.0):
                st.error("Lütfen uygulanan tüm testler için 10 saniyeden büyük geçerli süreler giriniz.")
            else:
                st.session_state.kaydediliyor = True
                with st.spinner("Telemetri verisi şifrelenip Google Sheets havuzuna işleniyor..."):
                    try:
                        client = get_gspread_client()
                        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                        sheet = client.open_by_url(sheet_url)
                        worksheet = sheet.worksheet("Sheet1")

                        mevcut_kodlar = [str(x).strip() for x in worksheet.col_values(3)[1:]]
                        if ogrenci_kod in mevcut_kodlar:
                            st.error(f"⚠️ DİKKAT: '{ogrenci_kod}' kodlu öğrenci sistemde zaten kayıtlı! Mükerrer kayıt engellendi.")
                            st.session_state.kaydediliyor = False
                        else:
                            yeni_satir = [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                arastirmaci,
                                ogrenci_kod,
                                cinsiyet,
                                sed,
                                secilen_okul,
                                dogum_tarihi.strftime("%Y-%m-%d"),
                                test_tarihi.strftime("%Y-%m-%d"),
                                yas_ay,
                                sure_sekil,
                                sure_renk,
                                sure_sayi,
                                sure_harf
                            ]
                            worksheet.append_row(yeni_satir)
                            st.success(f"✓ {ogrenci_kod} başarıyla veri havuzuna işlendi.")
                            st.session_state.kaydediliyor = False
                            st.rerun()
                    except Exception as e:
                        st.session_state.kaydediliyor = False
                        st.error(f"Hata: {str(e)}")

# -----------------------------------------
# SAĞ PANEL: DEMODAKİ ÖRNEKLEM KOTA RADARI
# -----------------------------------------
with col_sag:
    st.markdown("""
    <div class="section-header">
        <span class="title">03. ULUSAL ÖRNEKLEM KOTA RADARI</span>
        <span class="tag">CANLI MATRİS</span>
    </div>
    """, unsafe_allow_html=True)

    toplam_kayit = len(df_mevcut) if not df_mevcut.empty else 0
    toplam_hedef = 121 * 8 * 3
    kalan_genel = max(0, toplam_hedef - toplam_kayit)

    # Üst Sayaç Kutuları
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;">
        <div style="background:#0f172a; border:1px solid rgba(56,189,248,0.2); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#64748b; text-transform:uppercase; font-weight:600; display:block;">Mevcut N</span>
            <span style="font-family:'JetBrains Mono'; font-size:18px; font-weight:700; color:#38bdf8;">{toplam_kayit}</span>
        </div>
        <div style="background:#0f172a; border:1px solid rgba(56,189,248,0.2); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#64748b; text-transform:uppercase; font-weight:600; display:block;">Hedef N</span>
            <span style="font-family:'JetBrains Mono'; font-size:18px; font-weight:700; color:#f8fafc;">{toplam_hedef}</span>
        </div>
        <div style="background:#0f172a; border:1px solid rgba(56,189,248,0.2); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#64748b; text-transform:uppercase; font-weight:600; display:block;">Kalan İhtiyaç</span>
            <span style="font-family:'JetBrains Mono'; font-size:18px; font-weight:700; color:#10b981;">{kalan_genel}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    filtre_sed = f1.selectbox("SED Filtresi", ["Tümü", "Alt", "Orta", "Üst"])
    filtre_durum = f2.selectbox("Kota Filtresi", ["Tümü", "Sadece Açık Olanlar", "Hedef Tamamlananlar"])

    # Demodaki Koyu HTML Tablosunu Oluşturma
    sed_listesi = ["Alt", "Orta", "Üst"] if filtre_sed == "Tümü" else [filtre_sed]
    tablo_satirlari_html = ""

    for ay in range(60, 181):
        for s in sed_listesi:
            if not df_mevcut.empty and "Yas_Ayi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut = len(df_mevcut[(df_mevcut["Yas_Ayi"] == ay) & (df_mevcut["SED"] == s)])
            else:
                mevcut = 0

            kalan = max(0, 8 - mevcut)

            if filtre_durum == "Sadece Açık Olanlar" and kalan == 0:
                continue
            if filtre_durum == "Hedef Tamamlananlar" and kalan > 0:
                continue

            if mevcut >= 10:
                badge = '<span class="badge-locked">Kilitli</span>'
            elif mevcut >= 8:
                badge = '<span class="badge-target">Hedef Tamam</span>'
            else:
                badge = '<span class="badge-open">Açık</span>'

            # Öğrencinin o anki yaşıyla eşleşen satırı hafif siyan renkle aydınlat
            satir_stili = ' style="background: rgba(56, 189, 248, 0.08);"' if yas_ay == ay else ""

            tablo_satirlari_html += f"""
            <tr{satir_stili}>
                <td>{ay} Ay</td>
                <td>{s}</td>
                <td>{mevcut}</td>
                <td>{kalan}</td>
                <td>{badge}</td>
            </tr>
            """

    st.markdown(f"""
    <div class="hud-table-wrapper">
        <table class="hud-table">
            <thead>
                <tr>
                    <th>Yaş Ayı</th>
                    <th>SED</th>
                    <th>Mevcut</th>
                    <th>İhtiyaç</th>
                    <th>Durum</th>
                </tr>
            </thead>
            <tbody>
                {tablo_satirlari_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("🔄 Radarı Yenile", use_container_width=True):
        st.rerun()
