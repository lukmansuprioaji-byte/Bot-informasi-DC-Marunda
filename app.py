import streamlit as st
import pandas as pd
import google.generativeai as genai
import time

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Bot Informasi DC Marunda", page_icon="🤖")
st.title("🤖 Bot Informasi DC Marunda")

# 2. Pengaturan API Key (Dari Streamlit Secrets atau Sidebar)
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
        model = genai.GenerativeModel("gemini-3.8-flash")

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
                response_text = None
                # Percobaan otomatis hingga 3 kali jika terkena batas limit per menit (Error 429)
                for attempt in range(3):
                    try:
                        response = model.generate_content(prompt)
                        response_text = response.text
                        break
                    except Exception as err:
                        if "429" in str(err) and attempt < 2:
                            time.sleep(5)  # Tunggu 5 detik sebelum coba lagi
                        else:
                            raise err

                if response_text:
                    with st.chat_message("assistant"):
                        st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Sistem sedang padat (batas request per menit). Silakan tunggu beberapa detik lalu coba lagi. Detail: {e}")

elif not API_KEY:
    st.info("Silakan masukkan Gemini API Key di menu sebelah kiri (Sidebar) untuk mulai bertanya.")
