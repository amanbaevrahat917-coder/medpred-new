import streamlit as st
from groq import Groq
import json
import os

st.set_page_config(page_title="SPIN-Тренажер SELTFAR", page_icon="🩺", layout="wide")

HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(name, scenario, dialog_text, feedback):
    data = load_history()
    data.append({
        "name": name, 
        "scenario": scenario, 
        "dialog": dialog_text,
        "feedback": feedback
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

raw_key = None
if "GROQ_API_KEY" in st.secrets:
    raw_key = st.secrets["GROQ_API_KEY"]

if not raw_key:
    raw_key = st.sidebar.text_input("Введите Groq API Key:", type="password")

if not raw_key:
    st.info("💡 Введите ваш Groq API-ключ в меню слева или сохраните в Secrets.")
    st.stop()

api_key = str(raw_key).strip().strip('"').strip("'")
client = Groq(api_key=api_key)

@st.cache_data(ttl=3600)
def get_working_model():
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        for m_id in model_ids:
            if "llama" in m_id.lower() and "guard" not in m_id.lower():
                return m_id
        return model_ids[0] if model_ids else "llama-3.3-70b-versatile"
    except Exception:
        return "llama-3.3-70b-versatile"

ACTIVE_MODEL = get_working_model()

# === СЦЕНАРИИ КЛИНИЧЕСКИХ ВИЗИТОВ ===
SPIN_SCENARIOS = {
    "1. Врач только отпаивает (Ничего не назначает)": {
        "first_reply": "Здравствуйте! Я обычно не рекомендую сиропы от кашля детям с 2 лет, только обильное питьё.",
        "key_facts": "Проблема: мокрота -> бактерии -> антибиотики. Выгода: растительный экстракт защищает от бактерий."
    },
    "2. Назначает конкурента: МУНАТОРИЛ": {
        "first_reply": "Здравствуйте! Обычно я рекомендую сироп Мунаторил.",
        "key_facts": "В Мунаториле мох 0.39% и подорожник 0.17%. В нашем: в 9 раз больше подорожника и в 1.5 раза больше мха."
    },
    "3. Назначает конкурента: ГЕРБИОН": {
        "first_reply": "Здравствуйте! Из сиропов я предпочитаю назначать Гербион.",
        "key_facts": "В Гербионе один компонент. В нашем: в 1.8 раза больше подорожника и в 1.6 раз больше мха."
    },
    "4. Назначает конкурентов: ПРОСПАН / ЛИНКАС (Горькие)": {
        "first_reply": "Здравствуйте! Я обычно рекомендую Проспан или Линкас.",
        "key_facts": "Горький вкус конкурентов -> отказ -> срыв лечения. Наш имеет приятный вкус."
    }
}

st.title("🩺 SELTFAR: SPIN-Тренажер визита к врачу")

with st.sidebar:
    st.header("👩‍⚕️ Профиль врача")
    st.info("""
    **Асель Аскаровна**
    * **Специализация:** Врач-педиатр высшей категории
    * **Стаж работы:** 14 лет
    * **Характер:** Опытная, консервативная, опирается только на доказательную медицину и факты. Не любит пустых рекламных обещаний.
    """)
    st.divider()

    st.header("⚙️ Настройки визита")
    
    user_name = st.text_input("👤 Ваше имя (для отчета):", "Аноним")
    
    selected_scenario_name = st.selectbox("Выберите клинический сценарий:", list(SPIN_SCENARIOS.keys()))
    scenario_data = SPIN_SCENARIOS[selected_scenario_name]
    
    if user_name == "Рахат_Босс":
        st.divider()
        st.success("🔓 Режим разработчика")
        
        with st.expander("🌍 История прохождений (только для админа)"):
            global_history = load_history()
            if not global_history:
                st.write("Пока никто не прошел.")
            else:
                for i, item in enumerate(reversed(global_history[-15:]), 1):
                    with st.expander(f"👤 {item.get('name', 'Аноним')} | {item['scenario'][:15]}..."):
                        st.markdown("**📝 Оценка и разбор:**")
                        if 'feedback' in item:
                            st.info(item['feedback'])
                        else:
                            st.write("Оценка не сохранилась.")
                            
                        st.markdown("**💬 Диалог:**")
                        if 'dialog' in item:
                            st.text(item['dialog'])
                        else:
                            st.write("Диалог не сохранился.")
        
        if st.button("🗑️ Очистить историю", type="primary"):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
                st.success("История очищена!")
                st.rerun()
                
    if st.button("🔄 Начать визит заново", type="secondary"):
        st.session_state.messages = []
        st.rerun()

if "current_scenario" not in st.session_state or st.session_state.current_scenario != selected_scenario_name:
    st.session_state.current_scenario = selected_scenario_name
    st.session_state.messages = []

# === ОТРИСОВКА ИСТОРИИ ЧАТА ===
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("Медицинский представитель", avatar="💼"):
            st.write(msg["content"])
    else:
        with st.chat_message("Педиатр Асель Аскаровна", avatar="👩‍⚕️"):
            st.write(msg["content"])

if user_input := st.chat_input("Ваша реплика медпреда..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("Медицинский представитель", avatar="💼"):
        st.write(user_input)

    user_text_lower = user_input.lower()
    user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    
    is_asking_prescription = any(w in user_text_lower for w in ["какой", "какие", "что", "рекоменду", "назнача", "сироп", "препарат", "спрей", "выбор"])
    key_phrase = scenario_data["first_reply"].replace("Здравствуйте! ", "")
    has_stated_position = any(key_phrase in m["content"] for m in st.session_state.messages if m["role"] == "assistant")
    
    # 1. ЛОГИКА СТАРТА
    if user_msgs_count == 1 and not is_asking_prescription:
        bot_reply = "Здравствуйте! Проходите, присаживайтесь. Слушаю вас."
        
    elif is_asking_prescription and not has_stated_position:
        if user_msgs_count == 1:
            bot_reply = scenario_data["first_reply"]
        else:
            bot_reply = key_phrase

    # 2. УСЛОВИЯ КАПИТУЛЯЦИИ (ЗАЩИТА ОТ РАННЕЙ ПРОДАЖИ: user_msgs_count >= 4)
    elif selected_scenario_name.startswith("1") and any(w in user_text_lower for w in ["защит", "препарат", "вывод", "авирутус", "сироп", "растительн"]):
        if user_msgs_count >= 4:
            bot_reply = "Да, конечно. Аргумент про защиту от бактерий и профилактику антибиотиков действительно звучит убедительно. Я готова попробовать ваш препарат!"
        else:
            bot_reply = "Вы сразу предлагаете свой препарат, но меня устраивает моя тактика с обильным питьем. Зачем мне лишний раз давать детям сиропы?"

    elif selected_scenario_name.startswith("2") and any(w in user_text_lower for w in ["9", "1.5", "в 9 раз", "в 1.5"]):
        if user_msgs_count >= 4:
            bot_reply = "Да, согласна, это впечатляет! В 9 раз больше подорожника и в 1.5 раза больше мха — действительно мощная дозировка. Хорошо, буду рекомендовать ваш сироп!"
        else:
            bot_reply = "Интересные цифры, но меня вполне устраивает Мунаторил. Зачем мне менять препарат, если пациенты пока не жаловались?"

    elif selected_scenario_name.startswith("3") and any(w in user_text_lower for w in ["1.8", "1.6", "в 1.8", "в 1.6"]):
        if user_msgs_count >= 4:
            bot_reply = "Да, конечно. Ничего себе, в 1.8 раза больше активных веществ! С такими цифрами я готова попробовать заменить Гербион на ваш препарат."
        else:
            bot_reply = "Цифры — это хорошо, но Гербион проверен временем. Я пока не вижу веских причин переходить на что-то новое."

    elif selected_scenario_name.startswith("4") and any(w in user_text_lower for w in ["вкус", "сладк", "горьк", "дети легко"]):
        if user_msgs_count >= 4:
            bot_reply = "Да, вы абсолютно правы! Из-за горького вкуса дети часто отказываются пить сироп. Приятный вкус — это большой плюс, я попробую ваш!"
        else:
            bot_reply = "Вкус — не самое главное. Проспан и Линкас отлично лечат кашель, меня они полностью устраивают."

    # 3. ЕСТЕСТВЕННЫЙ ИИ-ОТВЕТ
    else:
        system_prompt = f"""
        Ты — врач-педиатр Асель Аскаровна (14 лет стажа). Беседуешь с медицинским представителем.
        Твой текущий сценарий: {selected_scenario_name}
        
        ПРАВИЛА ОТВЕТА:
        1. Отвечай живым, естественным языком человеческого общения (используй фразы по типу "Да, конечно", "Да, согласна", "Именно так, это действительно проблема").
        2. ОБЯЗАТЕЛЬНО дописывай каждое предложение и мысль до конца. Никогда не обрывай фразу!
        3. Если медпред спрашивает про опасности задержки мокроты, осложнения, бессонные ночи или антибиотики — естественно поддакивай и соглашайся.
        4. Если медпред прямо предлагает купить/назначить препарат БЕЗ конкретных цифр или дозировок — вежливо проявляй скепсис и проси факты.
        5. Ответ должен быть лаконичным (2-3 завершенных предложения).
        """

        groq_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            groq_messages.append({"role": m["role"], "content": m["content"]})

        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=groq_messages,
                temperature=0.5,
                max_tokens=400
            )
            bot_reply = completion.choices[0].message.content
            
            if not bot_reply or not bot_reply.strip():
                bot_reply = "Да, конечно, это действительно важный момент в лечении кашля. Каковы ваши конкретные аргументы по препарату?"
                
        except Exception as e:
            bot_reply = "Да, согласна с вами. Но расскажите подробнее о преимуществе вашего состава?"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    
    with st.chat_message("Педиатр Асель Аскаровна", avatar="👩‍⚕️"):
        st.write(bot_reply)

st.divider()
if st.button("📊 Завершить визит и получить разбор", type="primary"):
    if not st.session_state.messages:
        st.warning("Сначала проведите диалог с врачом!")
    else:
        with st.spinner("Бизнес-тренер анализирует вашу технику SPIN..."):
            
            dialog_history = ""
            for m in st.session_state.messages:
                role_name = "МЕДПРЕД" if m['role'] == "user" else "ВРАЧ"
                dialog_history += f"[{role_name}]: {m['content']}\n\n"
            
            eval_prompt = f"""
            Ты — строгий бизнес-тренер фармацевтической компании SELTFAR.
            Оцени работу медицинского представителя (МП) по технике SPIN.
            "Учитывай, что вопросы могут быть как открытыми, так и закрытыми с подтверждением. Не снижай балл только за формулировку закрытого вопроса, если логика SPIN и ключевые аргументы сохранены."
            
            Сценарий: {selected_scenario_name}
            Ключевые факты и аргументы: {scenario_data['key_facts']}
            
            История диалога:
            {dialog_history}
            
            Оцени строго по пунктам:
            1. **Ситуационный вопрос (S):**
            2. **Проблемный вопрос (P):** Указал ли МП на недостаток конкурента или текущего лечения?
            3. **Усугубляющий вопрос (I):** Усугубил ли проблему (вопросы про последствия)?
            4. **Направляющий вопрос / Выгода (N):** Дожал ли МП врача РЕАЛЬНЫМИ фактами? Смог ли убедить врача согласиться?
            5. **Итоговая оценка (от 1 до 10):** и 2-3 совета для улучшения навыков переговоров.
            """
            
            try:
                eval_completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": eval_prompt}],
                    temperature=0.3
                )
                
                coach_feedback = eval_completion.choices[0].message.content
                
                st.success("### 📝 Отчет бизнес-тренера SELTFAR")
                st.markdown(coach_feedback)
                
                save_name = user_name if user_name.strip() else "Аноним"
                save_history(save_name, selected_scenario_name, dialog_history, coach_feedback)
                
            except Exception as e:
                st.error(f"Ошибка при генерации отчета: {e}")
