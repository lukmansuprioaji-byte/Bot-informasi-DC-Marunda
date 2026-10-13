import streamlit as st
import pandas as pd
import google.generativeai as genai

# Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# Sidebar untuk Input API Key
API_KEY = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

# Tautan CSV dari Google Sheets Kamu
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRixx1TQe_8rc2jatwN8lxF8IXK6M7DNDAgoSzDUHScMpk7jOozQgK2kxMrHQNeJ0_shU7EiVqxTLi-/pub?output=csv"

@st.cache_data(ttl=300)
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
        # Menggunakan model gemini-2.5-flash terbaru
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Mengubah data tabel sheet menjadi teks referensi untuk AI
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
