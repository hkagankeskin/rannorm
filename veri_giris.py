import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="RAN Ulusal Norm - Veri Girişi", layout="wide", initial_sidebar_state="collapsed")

# --- OKUL LİSTESİ (SED GRUPLARINA GÖRE) ---
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

# --- GOOGLE SHEETS BAĞLANTI FONKSİYONU ---
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
    client = gspread.authorize(creds)
    return client

# --- CANLI VERİ ÇEKME FONKSİYONU ---
def get_data():
    try:
        client = get_gspread_client()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.worksheet("Sheet1")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception:
        return pd.DataFrame()

# Tablodan canlı verileri al
df_mevcut = get_data()

# --- ÇİFT TIKLAMA ÖNLEYİCİ DURUM YÖNETİMİ ---
if "kaydediliyor" not in st.session_state:
    st.session_state.kaydediliyor = False

# --- ANA ARAYÜZ ---
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>📋 RAN Ulusal Norm - Saha Veri Toplama Paneli</h2>", unsafe_allow_html=True)
st.divider()

col_sol, col_sag = st.columns([1, 1], gap="large")

# -----------------------------------------
# SOL PANEL: ÖĞRENCİ BİLGİLERİ VE VERİ GİRİŞİ
# -----------------------------------------
with col_sol:
    st.subheader("1. Öğrenci Bilgileri")
    
    arastirmaci = st.text_input("Araştırmacı Adı / Kodu (Örn: A-01)").strip()
    ogrenci_kod = st.text_input("Öğrenci Kodu (Örn: OKL-001-K)").strip()
    
    col_c, col_s = st.columns(2)
    cinsiyet = col_c.selectbox("Cinsiyet", ["Kız", "Erkek"])
    sed = col_s.selectbox("Okul SED Türü", ["Alt", "Orta", "Üst"])
    
    secilen_okul = st.selectbox("Uygulama Yapılacak Okul", OKUL_LISTESI.get(sed, ["Okul Bulunamadı"]))
    
    col_d, col_t = st.columns(2)
    # 60 - 180 ay aralığını kapsayacak şekilde takvim aralığı (2008 - 2022)
    dogum_tarihi = col_d.date_input("Doğum Tarihi", min_value=date(2008, 1, 1), max_value=date(2022, 12, 31), format="DD.MM.YYYY")
    test_tarihi = col_t.date_input("Test Tarihi", value=date.today(), format="DD.MM.YYYY")

    # Öğrencinin anlık yaş ve kota durumu hesabı
    yas_ay = None
    kota_durumu = "bekliyor"
    
    if dogum_tarihi and test_tarihi:
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
        yas_ay = (yil_farki * 12) + ay_farki
        
        st.markdown(f"**Hesaplanan Yaş:** `{yas_ay} Ay`")
        
        # 60 - 180 Ay Kontrolü
        if yas_ay < 60 or yas_ay > 180:
            st.error("❌ Bu öğrencinin yaşı (60 - 180 ay) örneklem kapsamı dışındadır.")
            kota_durumu = "gecersiz"
        else:
            if not df_mevcut.empty and "Yas_Ayi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut_ogrenci = len(df_mevcut[(df_mevcut["Yas_Ayi"] == yas_ay) & (df_mevcut["SED"] == sed)])
            else:
                mevcut_ogrenci = 0
                
            if mevcut_ogrenci >= 10:
                st.error(f"🚨 Bu grupta kota tamamen doldu! ({mevcut_ogrenci}/10). Veri girişi kilitlendi.")
                kota_durumu = "dolu"
            elif mevcut_ogrenci >= 8:
                st.warning(f"⚠️ Kota hedefine ulaşıldı ({mevcut_ogrenci}/8). Mecbur kalmadıkça eklemeyiniz.")
                kota_durumu = "uyari"
            else:
                st.success(f"✅ Kota Açık ({mevcut_ogrenci}/8). Kalan İhtiyaç: {8 - mevcut_ogrenci}")
                kota_durumu = "uygun"

    st.markdown("---")
    st.subheader("2. Kronometre Süreleri (Saniye)")

    if kota_durumu == "dolu":
        st.error("🔒 Bu alt grup için veri girişi kapalıdır.")
    elif not arastirmaci or not ogrenci_kod:
        st.info("ℹ️ Lütfen araştırmacı ve öğrenci kodunu giriniz.")
    elif kota_durumu in ["uygun", "uyari"]:
        c1, c2, c3, c4 = st.columns(4)
        sure_sekil = c1.number_input("Şekil (sn)", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        sure_renk  = c2.number_input("Renk (sn)",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        sure_sayi  = c3.number_input("Sayı (sn)",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        
        if yas_ay and yas_ay >= 83:
            sure_harf = c4.number_input("Harf (sn)", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
        else:
            sure_harf = 0.0
            c4.info("Harf: 83+ ay")

        st.write("")
        kaydet_butonu = st.button("💾 VERİYİ HAVUZA KAYDET", use_container_width=True, type="primary", disabled=st.session_state.kaydediliyor)
        
        if kaydet_butonu:
            if sure_sekil < 10.0 or sure_renk < 10.0 or sure_sayi < 10.0 or (yas_ay and yas_ay >= 83 and sure_harf < 10.0):
                st.error("Lütfen geçerli test süreleri (en az 10 sn) giriniz.")
            else:
                # 1. Çift Tıklama Koruması
                st.session_state.kaydediliyor = True
                
                with st.spinner("Veri doğrulanıyor ve kaydediliyor, lütfen bekleyiniz..."):
                    try:
                        client = get_gspread_client()
                        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                        sheet = client.open_by_url(sheet_url)
                        worksheet = sheet.worksheet("Sheet1")
                        
                        # 2. Mükerrer / Duplicate Kontrolü (Aynı Öğrenci Kodu var mı?)
                        mevcut_kodlar = [str(x).strip() for x in worksheet.col_values(3)[1:]] # 3. sütun Ogrenci_Kodu
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
                            st.success(f"🎉 {ogrenci_kod} başarıyla kaydedildi!")
                            st.session_state.kaydediliyor = False
                            st.rerun()  # Ekranı temizleyip kota tablosunu anında günceller
                            
                    except Exception as e:
                        st.session_state.kaydediliyor = False
                        st.error(f"Kayıt Hatası: {str(e)}")

# -----------------------------------------
# SAĞ PANEL: CANLI KOTA VE İHTİYAÇ TABLOSU
# -----------------------------------------
with col_sag:
    st.subheader("📊 Canlı Kota ve İhtiyaç Durumu")
    
    if st.button("🔄 Tabloyu Yenile", help="En son kayıtları çekmek için tıklayın"):
        st.rerun()

    # Filtreleme Seçenekleri
    f_col1, f_col2 = st.columns(2)
    filtre_sed = f_col1.selectbox("Filtrelenecek SED Türü", ["Tümü", "Alt", "Orta", "Üst"])
    filtre_durum = f_col2.selectbox("Kota Filtresi", ["Tümü", "Sadece İhtiyaç Olanlar (Açık)", "Dolanlar"])

    # 60 - 180 ay arası (121 tekil ay)
    tum_satirlar = []
    sed_listesi = ["Alt", "Orta", "Üst"] if filtre_sed == "Tümü" else [filtre_sed]
    
    for ay in range(60, 181):
        for s in sed_listesi:
            if not df_mevcut.empty and "Yas_Ayi" in df_mevcut.columns and "SED" in df_mevcut.columns:
                mevcut = len(df_mevcut[(df_mevcut["Yas_Ayi"] == ay) & (df_mevcut["SED"] == s)])
            else:
                mevcut = 0
            
            kalan_ihtiyac = max(0, 8 - mevcut)
            
            if mevcut >= 10:
                durum = "🔴 Doldu"
            elif mevcut >= 8:
                durum = "🟡 Hedef Tamam"
            else:
                durum = "🟢 Açık"
                
            tum_satirlar.append({
                "Yaş Ayı": f"{ay} Ay",
                "SED": s,
                "Mevcut Kayıt": mevcut,
                "Hedef": 8,
                "Kalan İhtiyaç": kalan_ihtiyac,
                "Durum": durum
            })
            
    df_kota = pd.DataFrame(tum_satirlar)
    
    # Durum filtresi uygulama
    if filtre_durum == "Sadece İhtiyaç Olanlar (Açık)":
        df_kota = df_kota[df_kota["Kalan İhtiyaç"] > 0]
    elif filtre_durum == "Dolanlar":
        df_kota = df_kota[df_kota["Kalan İhtiyaç"] == 0]

    # Özet Sayılar: 60-180 ay arası 121 aydır
    toplam_kayit = len(df_mevcut) if not df_mevcut.empty else 0
    toplam_hedef = 121 * 8 * (3 if filtre_sed == "Tümü" else 1)
    
    st.markdown(f"**Toplam Girilen Kayıt:** `{toplam_kayit}` | **Hedeflenen Veri Sayısı:** `{toplam_hedef}`")
    
    # İnteraktif Tablo Gösterimi
    st.dataframe(
        df_kota,
        use_container_width=True,
        hide_index=True,
        height=540
    )
