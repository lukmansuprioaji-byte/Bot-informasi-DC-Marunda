import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# Sidebar untuk Input API Key
API_KEY = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

# TEMPEL LINK HASIL 'SALIN LINK' DARI TOMBOL BAGIKAN DI SINI
ORIGINAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1e6eazfxdEfNXgupSIZNm7747Am4v2fU-b8VmfEp0gDs/edit?usp=sharing"

def get_csv_url(url):
    # Mengubah otomatis link /edit atau /view menjadi format CSV export
    if "/edit" in url or "/view" in url:
        return re.sub(r'/(edit|view).*', '/export?format=csv', url)
    return url

SHEET_CSV_URL = get_csv_url(ORIGINAL_SHEET_URL)

@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal membaca data dari Google Sheets: {e}")
        return None

data = load_data(SHEET_CSV_URL)

if data is not None and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        context = data.to_string(index=False)

        user_query = st.chat_input("Tanyakan jadwal absen atau nama karyawan...")

        if user_query:
            st.chat_message("user").write(user_query)

            prompt = f"""
            Kamu adalah asisten bot informasi jadwal absen karyawan DC Marunda. 
            Jawab pertanyaan pengguna secara akurat berdasarkan data tabel berikut.
            Jika nama atau informasi tidak ada dalam data, jawab dengan sopan bahwa data tidak ditemukan.

            [DATA JADWAL ABSEN]:
            {context}

            [PERTANYAAN PENGGUNA]:
            {user_query}
            """

            with st.spinner("Mencari data..."):
                response = model.generate_content(prompt)
                st.chat_message("assistant").write(response.text)

    except Exception as e:
        st.error(f"Terjadi kesalahan pada API Gemini: {e}")

elif not API_KEY:
    st.info("Silakan masukkan Gemini API Key di menu sebelah kiri (Sidebar) untuk mulai bertanya.")
