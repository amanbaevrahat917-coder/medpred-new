import streamlit as st
from groq import Groq
import json
import os

st.set_page_config(page_title="SPIN-Тренажер SELTFAR", page_icon="🩺", layout="wide")

# --- ФУНКЦИИ ДЛЯ ОБЩЕЙ ИСТОРИИ ПРОХОЖДЕНИЙ ---
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# Теперь функция принимает и сохраняет сам диалог
def save_history(name, scenario, dialog_text):
    data = load_history()
    data.append({"name": name, "scenario": scenario, "dialog": dialog_text})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# --------------------------------------------

# Проверка API ключа Groq
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

# Динамическое получение доступной модели
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

# Данные сценариев SPIN
SPIN_SCENARIOS = {
    "1. Врач только отпаивает (Ничего не назначает)": {
        "doctor_profile": "Асель Аскаровна — педиатр. Придерживается строго физиологичного подхода (обильное питьё, увлажнение воздуха). Не любит лишний раз назначать сиропы от кашля.",
        "key_facts": "Мокрота богата белками и углеводами -> риск присоединения бактериальной инфекции -> необходимость антибиотиков."
    },
    "2. Назначает Мунаторил": {
        "doctor_profile": "Асель Аскаровна — педиатр. Назначает Мунаторил детям с 2 лет.",
        "key_facts": "В Мунаториле исландский мох 0.39% и подорожник 0.17% (недостаточная дозировка). В нашем препарате: мха в 1.5 раза больше, подорожника в 9 раз больше!"
    },
    "3. Назначает Гербион (Подорожник, Мох)": {
        "doctor_profile": "Асель Аскаровна — педиатр. Назначает Гербион с 4 лет.",
        "key_facts": "Гербион разрешен с 4 лет, содержит только один компонент (мох 1.69% или подорожник 3.97%). В нашем препарате: в 1.8 раза больше подорожника и в 1.6 раз больше мха (комбинация!)."
    },
    "4. Назначает Проспан / Линкас / Амбробене (Горький вкус)": {
        "doctor_profile": "Асель Аскаровна — педиатр. Назначает Проспан/Бронхипрет/Линкас.",
        "key_facts": "У этих сиропов специфический горьковатый вкус, дети отказываются пить -> срыв лечения -> осложнения на нижние дыхательные пути."
    }
}

st.title("🩺 SELTFAR: SPIN-Тренажер визита к врачу")

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки визита")
    
    # Поле видно всем
    user_name = st.text_input("👤 Ваше имя (для отчета):", "Аноним")
    
    selected_scenario_name = st.selectbox("Выберите клинический сценарий:", list(SPIN_SCENARIOS.keys()))
    scenario_data = SPIN_SCENARIOS[selected_scenario_name]
    
    st.info(f"**Профиль врача:** {scenario_data['doctor_profile']}")
    st.caption(f"🤖 Активная модель: `"openai/gpt-oss-20b"`")
    
    # === СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ С ИСТОРИЕЙ ДИАЛОГОВ ===
    if user_name == "Рахат_Босс":
        st.divider()
        st.success("🔓 Режим разработчика")
        
        with st.expander("🌍 История прохождений (только для админа)"):
            global_history = load_history()
            if not global_history:
                st.write("Пока никто не прошел.")
            else:
                for i, item in enumerate(reversed(global_history[-15:]), 1):
                    # Делаем вложенный блок, чтобы открывать диалог кликом
                    with st.expander(f"👤 {item.get('name', 'Аноним')} | {item['scenario'][:15]}..."):
                        if 'dialog' in item:
                            st.text(item['dialog'])
                        else:
                            st.write("Диалог не сохранился (старая версия).")
        
        if st.button("🗑️ Очистить историю", type="primary"):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
                st.success("История очищена!")
                st.rerun()
    # ==================================================
    
    if st.button("🔄 Начать визит заново", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Инициализация истории сообщений
if "current_scenario" not in st.session_state or st.session_state.current_scenario != selected_scenario_name:
    st.session_state.current_scenario = selected_scenario_name
    st.session_state.messages = []

# Отображение истории
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Ввод пользователя
if user_input := st.chat_input("Ваша реплика медпреда..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    system_prompt = f"""
    Ты — врач-педиатр Асель Аскаровна (АА). 
    Контекст сценария: {scenario_data['doctor_profile']}.
    Твои ключевые установки: {scenario_data['key_facts']}.
    
    Правила поведения:
    1. Отвечай строго в роли Асель Аскаровны.
    2. Будь реалистичным врачом: отвечай коротко (1-3 предложения), немного сдержанно, как на реальном приеме.
    3. Отвечай на вопросы медицинского представителя (пользователя) согласно логике сценария SPIN.
    """

    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        groq_messages.append({"role": m["role"], "content": m["content"]})

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=groq_messages,
            temperature=0.7,
            max_tokens=300
        )
        bot_reply = completion.choices[0].message.content
        if not bot_reply or not bot_reply.strip():
            bot_reply = "Здравствуйте! Слушаю вас внимательно."
            
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.write(bot_reply)
    except Exception as e:
        st.error(f"⚠️ Ошибка Groq API: {e}")

# Кнопка разбора тренером
st.divider()
if st.button("📊 Завершить визит и получить разбор", type="primary"):
    if not st.session_state.messages:
        st.warning("Сначала проведите диалог с врачом!")
    else:
        with st.spinner("Бизнес-тренер анализирует вашу технику SPIN..."):
            
            # Собираем диалог в красивый текст для тренера И ДЛЯ СОХРАНЕНИЯ
            dialog_history = ""
            for m in st.session_state.messages:
                role_name = "МЕДПРЕД" if m['role'] == "user" else "ВРАЧ"
                dialog_history += f"[{role_name}]: {m['content']}\n\n"
            
            eval_prompt = f"""
            Ты — строгий бизнес-тренер фармацевтической компании SELTFAR.
            Оцени работу медицинского представителя в диалоге с врачом Асель Аскаровной.
            
            Сценарий: {selected_scenario_name}
            Ключевые факты/цифры сценария: {scenario_data['key_facts']}
            
            История диалога:
            {dialog_history}
            
            Дай разбор по пунктам:
            1. **Ситуационный вопрос (S):** Задал ли МП вопрос о текущих назначениях?
            2. **Проблемный вопрос (P):** Выявил ли МП проблему (дозировка, вкус, застой мокроты)?
            3. **Извлекающий / Усугубляющий вопрос (I):** Усугубил ли МП проблему (осложнения, кашель ночью, антибиотики)?
            4. **Направляющий вопрос / Выгода (N):** Предложил ли МП решение через выгоду?
            5. **Использование ключевых цифр/аргументов:** Насколько точно использованы факты SELTFAR?
            6. **Итоговая оценка (от 1 до 10):** и 2-3 главных совета для улучшения.
            """
            
            try:
                eval_completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": eval_prompt}],
                    temperature=0.3
                )
                st.success("### 📝 Отчет бизнес-тренера SELTFAR")
                st.markdown(eval_completion.choices[0].message.content)
                
                # ---> СОХРАНЯЕМ ИМЯ, СЦЕНАРИЙ И САМ ТЕКСТ ДИАЛОГА <---
                save_name = user_name if user_name.strip() else "Аноним"
                save_history(save_name, selected_scenario_name, dialog_history)
                
            except Exception as e:
                st.error(f"Ошибка при генерации отчета: {e}")
