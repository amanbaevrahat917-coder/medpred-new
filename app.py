import streamlit as st
from groq import Groq

st.set_page_config(page_title="Тренажер Медпреда", page_icon="🩺")
st.title("🩺 Симулятор визита к врачу")

api_key = st.sidebar.text_input("Введите Groq API Key:", type="password")

if not api_key:
    st.info("💡 Введите ваш Groq API-ключ в меню слева, чтобы начать.")
    st.stop()

client = Groq(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Ты скептичный врач-терапевт. Отвечай коротко (1-3 предложения), задавай каверзные вопросы."}]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if user_input := st.chat_input("Ваше сообщение:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = client.chat.completions.create(
        model="llama3-8b-8192",
,
        messages=st.session_state.messages
    )
    bot_reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)
