import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="RAN Ulusal Norm - Veri Girişi", layout="wide", initial_sidebar_state="collapsed")

# --- KOTA KONTROL ALGORİTMASI (Canlı Okuma) ---
def check_quota(yas_ay, sed, conn):
    try:
        # ttl=0 parametresi cache'i devre dışı bırakır, her defasında canlı veriyi çeker
        df = conn.read(worksheet="Sheet1", ttl=0)
        
        # Eğer tablo henüz boşsa veya ilgili sütunlar yoksa hatayı önlemek için
        if "Yas_Ayi" in df.columns and "SED" in df.columns:
            mevcut_sayi = len(df[(df["Yas_Ayi"] == yas_ay) & (df["SED"] == sed)])
        else:
            mevcut_sayi = 0
    except Exception:
        mevcut_sayi = 0
        
    # Her yaş ayı ve SED grubu için hedefler
    HEDEF_KOTA = 8
    MAKS_KOTA = 10
    
    return mevcut_sayi, HEDEF_KOTA, MAKS_KOTA

# --- GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

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
        # Yaş Ayı Hesaplama Formülü
        yil_farki = test_tarihi.year - dogum_tarihi.year
        ay_farki = test_tarihi.month - dogum_tarihi.month
        
        if test_tarihi.day < dogum_tarihi.day:
            ay_farki -= 1
            
        yas_ay = (yil_farki * 12) + ay_farki
        
        st.markdown(f"<h3 style='color: #2563eb;'>Hesaplanan Net Yaş: {yas_ay} Ay</h3>", unsafe_allow_html=True)
        
        # Yaş Sınırı Kontrolü
        if yas_ay < 60 or yas_ay > 167:
            st.error("❌ DİKKAT: Bu öğrencinin yaşı (60-167 ay) örneklem kapsamı dışındadır. Teste alınamaz.")
            kota_durumu = "gecersiz"
        else:
            # Canlı kotayı Google Sheets üzerinden çekiyoruz
            mevcut, hedef, maks = check_quota(yas_ay, sed, conn)
            
            st.markdown(f"**{yas_ay}. Ay — {sed} SED Kotası Durumu:**")
            
            if mevcut >= maks:
                st.error(f"🚨 KOTA DOLDU! (Mevcut: {mevcut} / Maks: {maks}) \n\nİstatistiksel tolerans aşıldığı için veri girişi kilitlendi. Lütfen listelerden başka yaş aylarına yöneliniz.")
                kota_durumu = "dolu"
            elif mevcut >= hedef:
                st.warning(f"⚠️ KOTA HEDEFİNE ULAŞILDI. (Mevcut: {mevcut} / Hedef: {hedef}) \n\nMecburi kalmadıkça başka öğrencileri teste almayınız.")
                kota_durumu = "uyari"
            else:
                st.success(f"✅ KOTA AÇIK (Mevcut: {mevcut} / Hedef: {hedef}) \n\nÖğrenci teste alınabilir.")
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
            with st.spinner("Veri Google Sheets sunucularına güvenle kaydediliyor, lütfen bekleyiniz..."):
                try:
                    client = conn._instance._client
                    sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
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
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"KAYIT HATASI OLUŞTU: {str(e)}")
