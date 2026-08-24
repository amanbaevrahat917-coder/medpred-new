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
            bot_reply = "Аргумент про защиту от бактерий и профилактику антибиотиков действительно звучит убедительно. Хорошо, я готова попробовать ваш препарат!"
        else:
            bot_reply = "Вы сразу предлагаете свой препарат, но меня устраивает моя тактика с обильным питьем. Зачем мне лишний раз давать детям сиропы?"

    elif selected_scenario_name.startswith("2") and any(w in user_text_lower for w in ["9", "1.5", "в 9 раз", "в 1.5"]):
        if user_msgs_count >= 4:
            bot_reply = "Ого, в 9 раз больше подорожника и в 1.5 раза больше мха? Это действительно мощная дозировка. Хорошо, убедили, буду рекомендовать ваш сироп!"
        else:
            bot_reply = "Интересные цифры, но меня вполне устраивает Мунаторил. Зачем мне менять препарат, если пациенты пока не жаловались?"

    elif selected_scenario_name.startswith("3") and any(w in user_text_lower for w in ["1.8", "1.6", "в 1.8", "в 1.6"]):
        if user_msgs_count >= 4:
            bot_reply = "Ничего себе, в 1.8 раза больше активных веществ! С такими цифрами я готова попробовать заменить Гербион на ваш препарат."
        else:
            bot_reply = "Цифры — это хорошо, но Гербион проверен временем. Я пока не вижу веских проблем, чтобы переходить на что-то новое."

    elif selected_scenario_name.startswith("4") and any(w in user_text_lower for w in ["вкус", "сладк", "горьк", "дети легко"]):
        if user_msgs_count >= 4:
            bot_reply = "Вот тут вы правы, из-за горького вкуса дети часто отказываются пить сироп. Приятный вкус — это большой плюс, я попробую ваш!"
        else:
            bot_reply = "Вкус — не самое главное. Проспан и Линкас отлично лечат кашель, меня они полностью устраивают."

    # 3. Если еще не сдалась — отвечает ИИ
    else:
        system_prompt = f"""
        Ты — врач-педиатр Асель Аскаровна. Беседуешь с медпредом.
        Твой текущий сценарий: {selected_scenario_name}
        
        ПРАВИЛА:
        1. На вопросы про симптомы, задержку мокроты, одышку, антибиотики или бессонные ночи мамы — сочувственно соглашайся (1-2 предложения).
        2. На просьбы переключиться на их сироп БЕЗ четких аргументов/цифр — отказывай: "Я привыкла к своей схеме лечения. Назовите факты."
        3. Отвечай коротко (1-2 предложения), от первого лица.
        """

        groq_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            groq_messages.append({"role": m["role"], "content": m["content"]})

        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=groq_messages,
                temperature=0.4,
                max_tokens=200
            )
            bot_reply = completion.choices[0].message.content
            
            if not bot_reply or not bot_reply.strip():
                if any(w in user_text_lower for w in ["бактери", "инфекци", "антибиоти"]):
                    bot_reply = "Да, доводить до антибиотиков очень не хочется, это всегда крайняя мера."
                elif any(w in user_text_lower for w in ["задержк", "мокрот", "застаив", "кашель", "ноч"]):
                    bot_reply = "Да, задержка мокроты действительно опасна развитием осложнений и сильно выматывает."
                else:
                    bot_reply = "Я пока не вижу причин менять привычную схему. Чем ваш подход лучше?"
                
        except Exception as e:
            bot_reply = "Я привыкла к своей схеме. Чем ваше предложение лучше?"

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
