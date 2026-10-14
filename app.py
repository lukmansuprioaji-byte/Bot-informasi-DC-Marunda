import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# 2. Pengaturan API Key Otomatis (Dari Streamlit Secrets)
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Masukkan Gemini API Key (Opsional):", type="password")

# 3. LINK GOOGLE SHEETS UTAMA (GANTI DENGAN LINK BAGIKAN KAMU)
ORIGINAL_SHEET_URL = "PASANG_LINK_BAGIKAN_DI_SINI"

# Fungsi Otomatis Mengubah Link ke CSV Export
def extract_sheet_id(url):
    match = re.search(r'/d/([a-zA-10-9-_]+)', url)
    if match:
        return match.group(1)
    return None

SHEET_ID = extract_sheet_id(ORIGINAL_SHEET_URL)

@st.cache_data(ttl=60)
def load_all_sheets(sheet_id):
    if not sheet_id:
        return ""
    
    # Daftar nama-nama tab sheet di Google Sheets kamu
    tab_names = ["Absen", "Insentif", "Produktivitas", "KPI Gudang", "Sheet1"]
    all_context = ""

    for tab in tab_names:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab}"
        try:
            df = pd.read_csv(url)
            if not df.empty:
                all_context += f"\n\n--- DATA TAB: {tab.upper()} ---\n"
                all_context += df.to_string(index=False)
        except Exception:
            continue
            
    return all_context

context_data = load_all_sheets(SHEET_ID)

# 4. Antarmuka Chat & Pemrosesan AI
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Inisialisasi Riwayat Chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Tampilkan Riwayat Chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_query = st.chat_input("Tanyakan apa saja soal Absen, Insentif, Produktivitas, atau KPI...")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            prompt = f"""
            Kamu adalah AI Asisten Resmi Operasional DC Marunda. 
            Jawab pertanyaan karyawan dengan ramah, jelas, dan profesional berdasarkan data dari berbagai lembar kerja berikut.
            Jika data yang ditanyakan tidak ada dalam tabel, jawab dengan sopan bahwa data tidak ditemukan.

            ==================== SELURUH DATA DC MARUNDA ====================
            {context_data}
            =================================================================

            PERTANYAAN KARYAWAN:
            {user_query}
            """

            with st.spinner("Memproses jawaban dari data..."):
                response = model.generate_content(prompt)
                bot_reply = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        st.error(f"Terjadi kesalahan pada sistem AI: {e}")

else:
    st.info("Sistem sedang memuat kunci API. Jika tidak muncul otomatis, silakan masukkan API Key di sidebar kiri.")
