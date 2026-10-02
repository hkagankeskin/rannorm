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

# --- SOFT & MODERN BİLİŞSEL TELEMETRİ TEMASI ---
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

  .stApp {
      background-color: #0b1120 !important;
      color: #e2e8f0 !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
  }

  div[data-baseweb="input"] {
      background-color: #131d32 !important;
      border: 1px solid rgba(148, 163, 184, 0.18) !important;
      border-radius: 9px !important;
      transition: all 0.2s ease !important;
  }
  div[data-baseweb="input"]:focus-within {
      border-color: #38bdf8 !important;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.15) !important;
  }
  div[data-baseweb="input"] input {
      background-color: transparent !important;
      color: #f1f5f9 !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      font-size: 13.5px !important;
  }
  div[data-baseweb="input"] input::placeholder {
      color: #475569 !important;
  }

  div[data-baseweb="select"] > div {
      background-color: #131d32 !important;
      border: 1px solid rgba(148, 163, 184, 0.18) !important;
      color: #f1f5f9 !important;
      border-radius: 9px !important;
  }
  div[data-baseweb="select"] * {
      color: #f1f5f9 !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
  }

  input[type="number"] {
      font-family: 'Space Grotesk', sans-serif !important;
      font-weight: 600 !important;
      font-size: 19px !important;
      color: #38bdf8 !important;
      text-align: center !important;
  }

  label p {
      font-size: 11.5px !important;
      font-weight: 600 !important;
      letter-spacing: 0.3px !important;
      color: #94a3b8 !important;
  }

  div.stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #0284c7, #2563eb) !important;
      border: 1px solid rgba(56, 189, 248, 0.35) !important;
      color: #ffffff !important;
      border-radius: 9px !important;
      font-weight: 600 !important;
      font-size: 14px !important;
      letter-spacing: 0.3px !important;
      padding: 10px 20px !important;
      box-shadow: 0 4px 18px rgba(37, 99, 235, 0.3) !important;
      transition: all 0.2s ease !important;
  }
  div.stButton > button[kind="primary"]:hover {
      box-shadow: 0 6px 24px rgba(56, 189, 248, 0.5) !important;
      transform: translateY(-1px) !important;
  }

  .section-header {
      background: rgba(19, 29, 50, 0.7);
      border: 1px solid rgba(148, 163, 184, 0.12);
      border-left: 3px solid #38bdf8;
      padding: 9px 14px;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
  }
  .section-header span.title {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #38bdf8;
  }
  .section-header span.tag {
      font-family: 'Space Grotesk', monospace;
      font-size: 11px;
      color: #64748b;
  }

  .telemetry-age-box {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.05), rgba(19, 29, 50, 0.7));
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 9px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 14px 0;
  }
</style>
""", unsafe_allow_html=True)

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

SINIF_SEVIYELERI = [
    "Okul Öncesi", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf", 
    "5. Sınıf", "6. Sınıf", "7. Sınıf", "8. Sınıf", "Lise"
]

def get_yas_dilimi(ay):
    if ay < 60 or ay > 180:
        return None
    if ay == 180:
        return "180 Ay"
    baslangic = ((ay - 60) // 3) * 3 + 60
    bitis = baslangic + 2
    return f"{baslangic}-{bitis} Ay"

def get_tum_dilimler():
    dilimler = []
    for baslangic in range(60, 180, 3):
        dilimler.append(f"{baslangic}-{baslangic+2} Ay")
    dilimler.append("180 Ay")
    return dilimler

HEDEF_KISI_SAYISI = 15

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

@st.cache_data(ttl=60)
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

if not df_mevcut.empty and "Yas_Ayi" in df_mevcut.columns:
    df_mevcut["Yas_Dilimi"] = df_mevcut["Yas_Ayi"].apply(lambda x: get_yas_dilimi(pd.to_numeric(x, errors="coerce")))
else:
    df_mevcut["Yas_Dilimi"] = None

if "kaydediliyor" not in st.session_state:
    st.session_state.kaydediliyor = False

if "basari_mesaji" in st.session_state:
    st.toast(st.session_state.basari_mesaji, icon="✅")
    st.success(st.session_state.basari_mesaji)
    del st.session_state.basari_mesaji

st.markdown("""
<div style="background: rgba(19, 29, 50, 0.9); border: 1px solid rgba(148, 163, 184, 0.12); padding: 12px 20px; border-radius: 9px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #f8fafc; letter-spacing: 0.3px;">
            RAN Ulusal Norm Çalışması <span style="font-size: 10px; padding: 2px 8px; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border-radius: 4px; border: 1px solid rgba(56,189,248,0.25);">SAHA PANELİ</span>
        </h3>
        <p style="margin: 2px 0 0 0; font-size: 11.5px; color: #94a3b8;">Bilişsel İsimlendirme Hızı ve Örneklem Veri Toplama İstasyonu</p>
    </div>
    <div style="display: flex; gap: 10px;">
        <span style="font-family: 'Space Grotesk'; font-size: 11px; padding: 4px 10px; background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.25); color: #34d399; border-radius: 6px;">● SİSTEM AKTİF</span>
        <span style="font-family: 'Space Grotesk'; font-size: 11px; padding: 4px 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); color: #38bdf8; border-radius: 6px;">PROTOKOL: 60-180 AY</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_sol, col_sag = st.columns([1.15, 0.85], gap="large")

with col_sol:
    st.markdown("""
    <div class="section-header">
        <span class="title">01. ÖĞRENCİ VE DEMOGRAFİ</span>
        <span class="tag">GİRİŞ PANELİ</span>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_o = st.columns(2)
    arastirmaci = col_a.text_input("Araştırmacı", placeholder="Örn: Ayşe Yılmaz", key="arastirmaci_input").strip()
    ogrenci_kod = col_o.text_input("Öğrenci Kodu", placeholder="Örn: OKL-001-K", key="ogrenci_kod_input").strip()

    col_c, col_snf, col_s = st.columns(3)
    cinsiyet = col_c.selectbox("Cinsiyet", ["Kız", "Erkek"])
    sinif = col_snf.selectbox("Sınıf", SINIF_SEVIYELERI)
    sed = col_s.selectbox("Okul SED Türü", ["Alt", "Orta", "Üst"])

    secilen_okul = st.selectbox("Uygulama Yapılan Okul", OKUL_LISTESI.get(sed, ["Okul Bulunamadı"]))

    col_d, col_t = st.columns(2)
    dogum_tarihi = col_d.date_input("Doğum Tarihi", min_value=date(2008, 1, 1), max_value=date(2022, 12, 31), format="DD.MM.YYYY")
    test_tarihi = col_t.date_input("Test Tarihi", value=date.today(), format="DD.MM.YYYY")

    yas_ay = None
    yas_dilimi = None
    kota_durumu = "bekliyor"

    # --- YENİ ALFANÜMERİK KİLİT MANTIĞI ---
    alfanumerik_acik = True
    if sinif == "Okul Öncesi":
        alfanumerik_acik = False
    elif sinif == "1. Sınıf":
        # 9, 10, 11, 12, 1 ayları (Eylül - Ocak arası Güz Dönemi) kapalı
        if test_tarihi.month in [9, 10, 11, 12, 1]:
            alfanumerik_acik = False

    if dogum_tarihi and test_tarihi:
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
        yas_ay = (yil_farki * 12) + ay_farki
        yas_dilimi = get_yas_dilimi(yas_ay)

        if yas_ay < 60 or yas_ay > 180:
            st.error("❌ Bu öğrencinin yaşı (60 - 180 ay) örneklem kapsamı dışındadır.")
            kota_durumu = "gecersiz"
        else:
            if not df_mevcut.empty and "Yas_Dilimi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut_ogrenci = len(df_mevcut[(df_mevcut["Yas_Dilimi"] == yas_dilimi) & (df_mevcut["SED"] == sed)])
            else:
                mevcut_ogrenci = 0

            kalan_ihtiyac = max(0, HEDEF_KISI_SAYISI - mevcut_ogrenci)

            if mevcut_ogrenci >= HEDEF_KISI_SAYISI:
                rozet_html = f'<span style="color:#f87171; font-family:\'Space Grotesk\'; font-weight:700;">🔴 DOLDU ({mevcut_ogrenci}/{HEDEF_KISI_SAYISI}) — GİRİŞ AÇIK</span>'
                kota_durumu = "dolu_ama_acik"
            else:
                rozet_html = f'<span style="color:#34d399; font-family:\'Space Grotesk\'; font-weight:700;">🟢 KOTA AÇIK (İhtiyaç: {kalan_ihtiyac})</span>'
                kota_durumu = "uygun"

            st.markdown(f"""
            <div class="telemetry-age-box">
                <div>
                    <div style="font-size:10px; font-weight:600; text-transform:uppercase; color:#94a3b8;">HESAPLANAN YAŞ VE DİLİM</div>
                    <div style="font-family:'Space Grotesk'; font-size:22px; font-weight:700; color:#38bdf8;">
                        {yas_ay} Ay <span style="font-size:13px; color:#cbd5e1; font-weight:500;">({yas_dilimi})</span>
                    </div>
                </div>
                <div>{rozet_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.markdown("""
    <div class="section-header">
        <span class="title">02. REAKSİYON VE İSİMLENDİRME SÜRELERİ</span>
        <span class="tag" style="color:#fbbf24;">SANİYE (SN)</span>
    </div>
    """, unsafe_allow_html=True)

    if not arastirmaci or not ogrenci_kod:
        st.info("ℹ️ Lütfen araştırmacı adını ve öğrenci kodunu giriniz.")
    elif kota_durumu in ["uygun", "dolu_ama_acik"]:
        
        # RAN TESTLERİ BÖLÜMÜ
        st.markdown("<div style='margin-bottom:8px; font-size:11px; font-weight:600; color:#94a3b8; letter-spacing:0.5px;'>RAN (İSİMLENDİRME) BATARYASI</div>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        sure_sekil = r1.number_input("1. Şekil", min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="sekil_input")
        sure_renk  = r2.number_input("2. Renk",  min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="renk_input")
        
        if alfanumerik_acik:
            sure_sayi  = r3.number_input("3. Sayı",  min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="sayi_input")
        else:
            sure_sayi = 0.0
            r3.markdown('<div style="text-align:center; padding-top:28px; font-size:11px; color:#64748b; font-family:\'Space Grotesk\';">KİLİTLİ<br>(Müfredat Kuralı)</div>', unsafe_allow_html=True)

        # RAS TESTLERİ VE HARF BÖLÜMÜ
        st.markdown("<div style='margin-top:12px; margin-bottom:8px; font-size:11px; font-weight:600; color:#94a3b8; letter-spacing:0.5px;'>RAS (ARDIL İSİMLENDİRME) VE HARF BATARYASI</div>", unsafe_allow_html=True)
        r4, r5, r6 = st.columns(3)
        
        if alfanumerik_acik:
            sure_harf = r4.number_input("4. Harf", min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="harf_input")
            sure_ras2 = r5.number_input("5. 2'li RAS", min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="ras2_input")
            sure_ras3 = r6.number_input("6. 3'lü RAS", min_value=0.0, max_value=200.0, step=0.5, value=None, placeholder="0.0", key="ras3_input")
        else:
            sure_harf, sure_ras2, sure_ras3 = 0.0, 0.0, 0.0
            r4.markdown('<div style="text-align:center; padding-top:28px; font-size:11px; color:#64748b; font-family:\'Space Grotesk\';">KİLİTLİ<br>(Müfredat Kuralı)</div>', unsafe_allow_html=True)
            r5.markdown('<div style="text-align:center; padding-top:28px; font-size:11px; color:#64748b; font-family:\'Space Grotesk\';">KİLİTLİ<br>(Müfredat Kuralı)</div>', unsafe_allow_html=True)
            r6.markdown('<div style="text-align:center; padding-top:28px; font-size:11px; color:#64748b; font-family:\'Space Grotesk\';">KİLİTLİ<br>(Müfredat Kuralı)</div>', unsafe_allow_html=True)

        st.write("")
        kaydet = st.button("⚡ VERİYİ NORM HAVUZUNA İŞLE", use_container_width=True, type="primary", disabled=st.session_state.kaydediliyor)

        if kaydet:
            hatali_giris = False
            if sure_sekil is None or sure_sekil < 10.0: hatali_giris = True
            if sure_renk is None or sure_renk < 10.0: hatali_giris = True
            if alfanumerik_acik:
                if sure_sayi is None or sure_sayi < 10.0: hatali_giris = True
                if sure_harf is None or sure_harf < 10.0: hatali_giris = True
                if sure_ras2 is None or sure_ras2 < 10.0: hatali_giris = True
                if sure_ras3 is None or sure_ras3 < 10.0: hatali_giris = True

            if hatali_giris:
                st.error("Lütfen uygulanan tüm testler için en az 10 saniye geçerli bir süre giriniz.")
            else:
                st.session_state.kaydediliyor = True
                with st.spinner("Veri Google Sheets havuzuna işleniyor..."):
                    try:
                        client = get_gspread_client()
                        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                        sheet = client.open_by_url(sheet_url)
                        worksheet = sheet.worksheet("Sheet1")

                        mevcut_kodlar = [str(x).strip() for x in worksheet.col_values(3)[1:]]
                        if ogrenci_kod in mevcut_kodlar:
                            st.error(f"⚠️ DİKKAT: '{ogrenci_kod}' kodlu öğrenci sistemde zaten mevcut! Mükerrer kayıt engellendi.")
                            st.session_state.kaydediliyor = False
                        else:
                            yeni_satir = [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                arastirmaci,
                                ogrenci_kod,
                                cinsiyet,
                                sinif, # Yeni Sinif verisi eklendi
                                sed,
                                secilen_okul,
                                dogum_tarihi.strftime("%Y-%m-%d"),
                                test_tarihi.strftime("%Y-%m-%d"),
                                yas_ay,
                                sure_sekil,
                                sure_renk,
                                sure_sayi if sure_sayi is not None else 0.0,
                                sure_harf if sure_harf is not None else 0.0,
                                sure_ras2 if sure_ras2 is not None else 0.0,
                                sure_ras3 if sure_ras3 is not None else 0.0
                            ]
                            worksheet.append_row(yeni_satir)
                            
                            get_data.clear()
                            
                            for k in ['ogrenci_kod_input', 'sekil_input', 'renk_input', 'sayi_input', 'harf_input', 'ras2_input', 'ras3_input']:
                                if k in st.session_state:
                                    del st.session_state[k]
                            
                            st.session_state.basari_mesaji = f"İşlem Tamamlandı: {ogrenci_kod} başarıyla norm havuzuna işlendi!"
                            st.session_state.kaydediliyor = False
                            st.rerun()
                    except Exception as e:
                        st.session_state.kaydediliyor = False
                        st.error(f"Hata oluştu: {str(e)}")

with col_sag:
    st.markdown("""
    <div class="section-header">
        <span class="title">03. 3 AYLIK BLOK KOTA RADARI</span>
        <span class="tag">CANLI MATRİS</span>
    </div>
    """, unsafe_allow_html=True)

    tum_dilimler = get_tum_dilimler()
    toplam_kayit = len(df_mevcut[df_mevcut["Yas_Dilimi"].notna()]) if not df_mevcut.empty else 0
    toplam_hedef = len(tum_dilimler) * HEDEF_KISI_SAYISI * 3 
    kalan_genel = max(0, toplam_hedef - toplam_kayit)

    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;">
        <div style="background:#131d32; border:1px solid rgba(148,163,184,0.12); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#94a3b8; text-transform:uppercase; font-weight:600; display:block;">Mevcut N</span>
            <span style="font-family:'Space Grotesk'; font-size:18px; font-weight:700; color:#38bdf8;">{toplam_kayit}</span>
        </div>
        <div style="background:#131d32; border:1px solid rgba(148,163,184,0.12); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#94a3b8; text-transform:uppercase; font-weight:600; display:block;">Hedef N</span>
            <span style="font-family:'Space Grotesk'; font-size:18px; font-weight:700; color:#f8fafc;">{toplam_hedef}</span>
        </div>
        <div style="background:#131d32; border:1px solid rgba(148,163,184,0.12); border-radius:8px; padding:10px; text-align:center;">
            <span style="font-size:10px; color:#94a3b8; text-transform:uppercase; font-weight:600; display:block;">Kalan İhtiyaç</span>
            <span style="font-family:'Space Grotesk'; font-size:18px; font-weight:700; color:#34d399;">{kalan_genel}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    filtre_sed = f1.selectbox("SED Filtresi", ["Tümü", "Alt", "Orta", "Üst"])
    filtre_durum = f2.selectbox("Kota Filtresi", ["Tümü", "Sadece Açık Olanlar", "Dolup Aşanlar"])

    sed_listesi = ["Alt", "Orta", "Üst"] if filtre_sed == "Tümü" else [filtre_sed]
    matris_verisi = []

    for d in tum_dilimler:
        for s in sed_listesi:
            if not df_mevcut.empty and "Yas_Dilimi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut = len(df_mevcut[(df_mevcut["Yas_Dilimi"] == d) & (df_mevcut["SED"] == s)])
            else:
                mevcut = 0

            kalan = max(0, HEDEF_KISI_SAYISI - mevcut)

            if filtre_durum == "Sadece Açık Olanlar" and kalan == 0:
                continue
            if filtre_durum == "Dolup Aşanlar" and kalan > 0:
                continue

            if mevcut >= HEDEF_KISI_SAYISI:
                durum = "🔴 Doldu (Giriş Açık)"
            else:
                durum = "🟢 Açık"

            matris_verisi.append({
                "Yaş Dilimi": d,
                "SED": s,
                "Mevcut": mevcut,
                "Hedef": HEDEF_KISI_SAYISI,
                "İhtiyaç": kalan,
                "Durum": durum
            })

    df_matris = pd.DataFrame(matris_verisi)

    st.dataframe(
        df_matris,
        use_container_width=True,
        hide_index=True,
        height=480
    )

    st.write("")
    if st.button("🔄 Radarı Yenile", use_container_width=True):
        get_data.clear() 
        st.rerun()
