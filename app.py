import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Тренажер Медпреда", page_icon="🩺")
st.title("🩺 Симулятор визита к врачу")

# Получаем ключ из Secrets или sidebar
raw_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Введите Gemini API Key:", type="password")

if not raw_key:
    st.info("💡 Введите ваш Gemini API-ключ в меню слева или сохраните в Secrets.")
    st.stop()

api_key = raw_key.strip().strip('"').strip("'")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-3.6-flash')

system_instruction = "Ты опытный, немного уставший педиатр детской поликлиники. Очень переживаешь за безопасность маленьких пациентов, поэтому строго и скептично относишься к новым препаратам. Отвечай коротко (1-3 предложения), задавай каверзные вопросы о побочках и дозировках для детей."

if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.chat_session.send_message(f"Системная установка: {system_instruction}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Ваше сообщение:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    try:
        response = st.session_state.chat_session.send_message(user_input)
        bot_reply = response.text
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.write(bot_reply)
    except Exception as e:
        st.error(f"⚠️ Ошибка Gemini API: {e}")
