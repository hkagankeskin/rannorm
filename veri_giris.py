import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="RAN Ulusal Norm - Veri Girişi", layout="wide", initial_sidebar_state="collapsed")

# --- 1. VERİ TABANI ALTYAPISI ---
# Gerçek saha uygulamasında bu dosya bir bulut veritabanı (Google Sheets/Firebase) olacaktır.
# Şimdilik yerel bir CSV dosyası olarak kurguluyoruz.
DATA_FILE = "ran_ulusal_saha_verisi.csv"

def init_db():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            "Tarih_Saat", "Arastirmaci_Kodu", "Ogrenci_Kodu", "Cinsiyet", "SED", 
            "Dogum_Tarihi", "Test_Tarihi", "Yas_Ayi", 
            "Sekil_Sure", "Renk_Sure", "Sayi_Sure", "Harf_Sure"
        ])
        df.to_csv(DATA_FILE, index=False)

init_db()

# --- 2. KOTA KONTROL ALGORİTMASI ---
def check_quota(yas_ay, sed):
    try:
        df = pd.read_csv(DATA_FILE)
        # Seçili yaş ayı ve SED grubu için mevcut kayıt sayısı
        mevcut_sayi = len(df[(df["Yas_Ayi"] == yas_ay) & (df["SED"] == sed)])
    except:
        mevcut_sayi = 0
        
    # Her SED grubu için hedefler (Alt: 8, Orta: 8, Üst: 8 -> Toplam 24-30 arası)
    HEDEF_KOTA = 8
    MAKS_KOTA = 10
    
    return mevcut_sayi, HEDEF_KOTA, MAKS_KOTA

# --- 3. ANA ARAYÜZ ---
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
    # Yaş sınırları (60-167 ay) dikkate alınarak makul doğum yılı aralığı belirlendi
    dogum_tarihi = col_d.date_input("Doğum Tarihi", min_value=date(2010, 1, 1), max_value=date(2022, 12, 31))
    test_tarihi = col_t.date_input("Test Tarihi", value=date.today())

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
        # Pürüzsüz Yaş Ayı Hesaplama Formülü
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        
        # Test günü, doğum gününden önceyse henüz o ayı doldurmamıştır
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
            
        yas_ay = (yil_farki * 12) + ay_farki
        
        st.markdown(f"<h3 style='color: #2563eb;'>Hesaplanan Net Yaş: {yas_ay} Ay</h3>", unsafe_allow_html=True)
        
        # Yaş Sınırı Kontrolü
        if yas_ay < 60 or yas_ay > 167:
            st.error("❌ DİKKAT: Bu öğrencinin yaşı (60-167 ay) örneklem kapsamı dışındadır. Teste alınamaz.")
            kota_durumu = "gecersiz"
        else:
            mevcut, hedef, maks = check_quota(yas_ay, sed)
            
            st.markdown(f"**{yas_ay}. Ay — {sed} SED Kotası Durumu:**")
            
            # Dinamik Kota Bildirimleri
            if mevcut >= maks:
                st.error(f"🚨 KOTA DOLDU! (Mevcut: {mevcut} / Maks: {maks}) \n\nİstatistiksel tolerans aşıldığı için veri girişi kilitlendi. Lütfen listelerden başka yaş aylarına yöneliniz.")
                kota_durumu = "dolu"
            elif mevcut >= hedef:
                st.warning(f"⚠️ KOTA HEDEFİNE ULAŞILDI. (Mevcut: {mevcut} / Hedef: {hedef}) \n\nMecburi kalmadıkça (esneklik payı sınırındasınız) başka öğrencileri teste almayınız.")
                kota_durumu = "uyari"
            else:
                st.success(f"✅ KOTA AÇIK (Mevcut: {mevcut} / Hedef: {hedef}) \n\nÖğrenci teste alınabilir.")
                kota_durumu = "uygun"
    else:
        kota_durumu = "bekliyor"

# -----------------------------------------
# ALT PANEL: SÜRE GİRİŞİ VE KAYIT ALANI
# -----------------------------------------
st.divider()
st.subheader("3. Kronometre Süreleri (Saniye)")

# Güvenlik Kilitleri
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
        # Son bir hata kontrolü (Testlerin 0.0 olarak kalıp kalmadığına bakılır)
        if sure_sekil == 0.0 or sure_renk == 0.0 or sure_sayi == 0.0 or (yas_ay >= 83 and sure_harf == 0.0):
            st.error("Lütfen uygulanan tüm testlerin sürelerini 0.0'dan büyük bir değer olarak giriniz.")
        else:
            yeni_veri = pd.DataFrame([{
                "Tarih_Saat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Arastirmaci_Kodu": arastirmaci,
                "Ogrenci_Kodu": ogrenci_kod,
                "Cinsiyet": cinsiyet,
                "SED": sed,
                "Dogum_Tarihi": dogum_tarihi.strftime("%Y-%m-%d"),
                "Test_Tarihi": test_tarihi.strftime("%Y-%m-%d"),
                "Yas_Ayi": yas_ay,
                "Sekil_Sure": sure_sekil,
                "Renk_Sure": sure_renk,
                "Sayi_Sure": sure_sayi,
                "Harf_Sure": sure_harf
            }])
            
            yeni_veri.to_csv(DATA_FILE, mode='a', header=False, index=False)
            st.success(f"🎉 Başarılı! {ogrenci_kod} kodlu öğrencinin verileri sisteme işlendi. Kota durumu güncellendi.")
