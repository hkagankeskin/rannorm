import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="RAN Ulusal Norm - Veri Girişi", layout="wide", initial_sidebar_state="collapsed")

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

# --- KOTA KONTROL ALGORİTMASI ---
def check_quota(yas_ay, sed):
    try:
        client = get_gspread_client()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.worksheet("Sheet1")
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty and "Yas_Ayi" in df.columns and "SED" in df.columns:
            mevcut_sayi = len(df[(df["Yas_Ayi"] == yas_ay) & (df["SED"] == sed)])
        else:
            mevcut_sayi = 0
    except Exception:
        mevcut_sayi = 0
        
    HEDEF_KOTA = 8
    MAKS_KOTA = 10
    
    return mevcut_sayi, HEDEF_KOTA, MAKS_KOTA

# --- ANA ARAYÜZ ---
st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>📋 RAN Ulusal Norm - Saha Veri Toplama Paneli</h2>", unsafe_allow_html=True)
st.divider()

col_sol, col_sag = st.columns([1, 1], gap="large")

# -----------------------------------------
# SOL PANEL: ÖĞRENCİ BİLGİLERİ VE DIŞLAMA
# -----------------------------------------
with col_sol:
    st.subheader("1. Öğrenci Bilgileri")
    
    arastirmaci = st.text_input("Araştırmacı Adı / Kodu (Örn: A-01)")
    ogrenci_kod = st.text_input("Öğrenci Kodu (Örn: OKL-001-K)")
    
    col_c, col_s = st.columns(2)
    cinsiyet = col_c.selectbox("Cinsiyet", ["Kız", "Erkek"])
    sed = col_s.selectbox("Okul SED Türü", ["Alt", "Orta", "Üst"])
    
    col_d, col_t = st.columns(2)
    # Gün-Ay-Yıl formatı (DD.MM.YYYY)
    dogum_tarihi = col_d.date_input("Doğum Tarihi", min_value=date(2010, 1, 1), max_value=date(2022, 12, 31), format="DD.MM.YYYY")
    test_tarihi = col_t.date_input("Test Tarihi", value=date.today(), format="DD.MM.YYYY")

    st.markdown("---")
    st.markdown("**(Zorunlu) Norm Dışlama Kriterleri:**")
    kriter_1 = st.checkbox("Öğrencinin anadili Türkçedir.")
    kriter_2 = st.checkbox("Bilinen bir nörogelişimsel (örn: DEHB, Disleksi) veya görme/işitme engeli yoktur.")
    
    kriterler_uygun = kriter_1 and kriter_2

# -----------------------------------------
# SAĞ PANEL: YAŞ HESABI VE KOTA DURUMU
# -----------------------------------------
with col_sag:
    st.subheader("2. Yaş Ayı ve Kota Kontrolü")
    
    if dogum_tarihi and test_tarihi:
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
            
        yas_ay = (yil_farki * 12) + ay_farki
        
        st.markdown(f"<h3 style='color: #2563eb;'>Hesaplanan Net Yaş: {yas_ay} Ay</h3>", unsafe_allow_html=True)
        
        if yas_ay < 60 or yas_ay > 167:
            st.error("❌ DİKKAT: Bu öğrencinin yaşı (60-167 ay) örneklem kapsamı dışındadır. Teste alınamaz.")
            kota_durumu = "gecersiz"
        else:
            mevcut, hedef, maks = check_quota(yas_ay, sed)
            
            st.markdown(f"**{yas_ay}. Ay — {sed} SED Kotası Durumu:**")
            
            if mevcut >= maks:
                st.error(f"🚨 KOTA DOLDU! (Mevcut: {mevcut} / Maks: {maks}) \n\nİstatistiksel tolerans aşıldığı için veri girişi kilitlendi.")
                kota_durumu = "dolu"
            elif mevcut >= hedef:
                st.warning(f"⚠️ KOTA HEDEFİNE ULAŞILDI. (Mevcut: {mevcut} / Hedef: {hedef})")
                kota_durumu = "uyari"
            else:
                st.success(f"✅ KOTA AÇIK (Mevcut: {mevcut} / Hedef: {hedef})")
                kota_durumu = "uygun"
    else:
        kota_durumu = "bekliyor"

# -----------------------------------------
# ALT PANEL: SÜRE GİRİŞİ VE ATOMİK KAYIT
# -----------------------------------------
st.divider()
st.subheader("3. Kronometre Süreleri (Saniye)")

if kota_durumu == "dolu":
    st.error("🔒 Bu alt grup için veri girişi sistem tarafından kapatılmıştır.")
elif not kriterler_uygun:
    st.warning("🔒 Devam etmek için yukarıdaki iki norm dışlama kriterini onaylamalısınız.")
elif not arastirmaci or not ogrenci_kod:
    st.info("ℹ️ Lütfen öğrenci kodunu ve araştırmacı kodunu eksiksiz doldurunuz.")
elif kota_durumu in ["uygun", "uyari"]:
    
    c1, c2, c3, c4 = st.columns(4)
    sure_sekil = c1.number_input("Şekil Testi (sn)", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
    sure_renk  = c2.number_input("Renk Testi (sn)",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)
    sure_sayi  = c3.number_input("Sayı Testi (sn)",  min_value=0.0, max_value=200.0, step=0.5, value=0.0)
    
    if yas_ay >= 83:
        sure_harf = c4.number_input("Harf Testi (sn)", min_value=0.0, max_value=200.0, step=0.5, value=0.0)
    else:
        sure_harf = 0.0
        c4.info("ℹ️ Harf testi sadece 83. ay ve üzeri için uygulanır.")

    st.write("")
    if st.button("💾 VERİYİ ANA HAVUZA KAYDET", use_container_width=True, type="primary"):
        if sure_sekil < 10.0 or sure_renk < 10.0 or sure_sayi < 10.0 or (yas_ay >= 83 and sure_harf < 10.0):
            st.error("Lütfen uygulanan tüm testlerin sürelerini 10 saniyeden büyük, geçerli bir değer olarak giriniz.")
        else:
            with st.spinner("Veri Google Sheets sunucularına güvenle kaydediliyor..."):
                try:
                    client = get_gspread_client()
                    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    sheet = client.open_by_url(sheet_url)
                    worksheet = sheet.worksheet("Sheet1")
                    
                    yeni_satir = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        arastirmaci,
                        ogrenci_kod,
                        cinsiyet,
                        sed,
                        dogum_tarihi.strftime("%Y-%m-%d"),
                        test_tarihi.strftime("%Y-%m-%d"),
                        yas_ay,
                        sure_sekil,
                        sure_renk,
                        sure_sayi,
                        sure_harf
                    ]
                    
                    worksheet.append_row(yeni_satir)
                    st.success(f"🎉 Başarılı! {ogrenci_kod} kodlu öğrencinin verileri sisteme işlendi.")
                    
                except Exception as e:
                    st.error(f"KAYIT HATASI OLUŞTU: {str(e)}")
