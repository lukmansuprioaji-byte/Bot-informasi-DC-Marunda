import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# 2. Pengaturan API Key (Otomatis dari Streamlit Secrets atau Manual dari Sidebar)
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

# 3. LINK GOOGLE SHEETS UTAMA
SHEET_ID = "1e6eazfxdEfNXgupSIZNm7747Am4v2fU-b8VmfEp0gDs"

@st.cache_data(ttl=60)
def load_all_sheets(sheet_id):
    tab_names = [
        "Absensi", 
        "Insentif", 
        "Produktifitas", 
        "KPI Gudang", 
        "Sheet1"
    ]
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

# 4. Inisialisasi Riwayat Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan seluruh riwayat percakapan
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Pemrosesan Chat dengan AI
if context_data and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # MENGGUNAKAN GEMINI 3.8 FLASH
        model = genai.GenerativeModel("gemini-3.6-flash")

        user_query = st.chat_input("Tanyakan soal Absensi, Insentif, Produktifitas, atau KPI Gudang...")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            prompt = f"""
            Kamu adalah AI Asisten Operasional DC Marunda. 
            Jawab pertanyaan karyawan secara akurat, ramah, dan profesional berdasarkan seluruh data dari tab Google Sheets berikut.
            Jika pertanyaan mengenai histori/masa lalu, cari baris data sesuai tanggal/periode terkait.

            ================ SELURUH DATA GOOGLE SHEETS DC MARUNDA ================
            {context_data}
            ======================================================================

            PERTANYAAN KARYAWAN:
            {user_query}
            """

            with st.spinner("Mencari data..."):
                response = model.generate_content(prompt)
                bot_reply = response.text

                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        st.error(f"Terjadi kesalahan pada sistem AI: {e}")

elif not API_KEY:
    st.info("Silakan masukkan Gemini API Key di menu sebelah kiri (Sidebar) untuk mulai bertanya.")
