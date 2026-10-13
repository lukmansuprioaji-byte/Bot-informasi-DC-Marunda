import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# 2. Pengaturan API Key (Otomatis dari Streamlit Secrets atau Manual dari Sidebar)
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

# 3. LINK GOOGLE SHEETS BARU KAMU
ORIGINAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1e6eazfxdEfNXgupSIZNm7747Am4v2fU-b8VmfEp0gDs/edit?usp=sharing"

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
    
    # AI akan mencoba membaca daftar nama tab umum yang mungkin kamu buat
    # Tambahkan nama tab baru kamu ke dalam list ini jika ada
    tab_names = ["Absen", "Jadwal", "Insentif", "Produktivitas", "KPI Gudang", "KPI", "Sheet1"]
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

# 4. Inisialisasi Riwayat Chat (Supaya percakapan lama tidak terhapus)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan seluruh percakapan yang pernah dilakukan
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Pemrosesan Chat dengan AI Gemini
if context_data and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # Menggunakan Model Gemini 3.6 Flash
        model = genai.GenerativeModel("gemini-3.6-flash")

        user_query = st.chat_input("Tanyakan soal Jadwal Absen, Insentif, Produktivitas, atau KPI...")

        if user_query:
            # Tampilkan pesan user
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            prompt = f"""
            Kamu adalah AI Asisten Operasional DC Marunda.
            Tugasmu adalah memberikan informasi yang akurat, ramah, dan jelas kepada karyawan berdasarkan data dari Google Sheets.

            ATURAN PENTING:
            1. Jawab pertanyaan berdasarkan data dari berbagai tab lembar kerja di bawah ini.
            2. Jika pengguna menanyakan data historis (minggu lalu/bulan lalu), carilah baris data sesuai tanggal/periode tersebut.
            3. Jika pengguna menanyakan kondisi saat ini/update terbaru, berikan data periode yang paling baru.
            4. Jika data tidak ditemukan, jawab dengan sopan bahwa data tidak tersedia dalam sistem.

            ================ SELURUH DATA GOOGLE SHEETS DC MARUNDA ================
            {context_data}
            =======================================================================

            PERTANYAAN KARYAWAN:
            {user_query}
            """

            with st.spinner("Memproses jawaban dari data..."):
                response = model.generate_content(prompt)
                bot_reply = response.text

                # Tampilkan jawaban AI
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        st.error(f"Terjadi kesalahan pada sistem AI: {e}")

elif not API_KEY:
    st.info("Silakan masukkan Gemini API Key di menu sebelah kiri (Sidebar) untuk mulai bertanya.")
