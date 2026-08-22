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

# === ПОЛНОСТЬЮ ОБНОВЛЕННАЯ БАЗА СЦЕНАРИЕВ ПО МЕТОДИЧКЕ ===
SPIN_SCENARIOS = {
    "1. Врач только отпаивает (Ничего не назначает)": {
        "doctor_profile": "Ты врач, который придерживается строго физиологичного подхода. На вопрос о сиропах отвечай: 'Я не рекомендую сиропы от кашля, только обильное питьё и увлажнение'.",
        "expected_doctor_answers": "Если МП спрашивает про бактерии в мокроте — скажи 'Присоединение бактериальной инфекции'. Если спрашивает про реакцию родителей на антибиотики — скажи 'Да, я с вами согласна, реагируют плохо'.",
        "key_facts": "Проблема: мокрота богата белками -> бактерии -> антибиотики. Выгода: растительный экстракт защищает от бактериальной инфекции."
    },
    "2. Назначает конкурента: МУНАТОРИЛ": {
        "doctor_profile": "Ты врач, который назначает Мунаторил. На вопрос о сиропах с 2х лет отвечай: 'Мунаторил'.",
        "expected_doctor_answers": "Если МП говорит, что в Мунаториле мало экстрактов и мокрота задерживается — отвечай 'Усиливается кашель, чаще по ночам'. Если спрашивают, как утром чувствуют себя мама и ребенок — отвечай 'Обструкция, одышка, придется подключать гормоны'.",
        "key_facts": "Проблема: В Мунаториле всего мох 0.39% и подорожник 0.17%. Выгода: В нашем препарате в 9 раз больше подорожника и в 1.5 раза больше мха."
    },
    "3. Назначает конкурента: ГЕРБИОН": {
        "doctor_profile": "Ты врач, который назначает Гербион. На вопрос о сиропах с 4 лет отвечай: 'Гербион'.",
        "expected_doctor_answers": "Если МП спрашивает, к чему приведет незащищенная слизистая — отвечай 'Усиливается кашель. Да, по ночам особенно'.",
        "key_facts": "Проблема: В Гербионе не комбинация, а либо мох 1.69%, либо подорожник 3.97% (этого мало). Выгода: В нашем препарате в 1.8 раза больше подорожника и в 1.6 раз больше мха."
    },
    "4. Назначает конкурентов: ПРОСПАН / ЛИНКАС (Горькие)": {
        "doctor_profile": "Ты врач, который назначает Проспан, Бронхипрет или Линкас. На вопрос о сиропах отвечай: 'Проспан'.",
        "expected_doctor_answers": "Если МП говорит про горький вкус и что дети отказываются пить, и спрашивает про последствия — отвечай 'Кашель сохраняется'.",
        "key_facts": "Проблема: Горьковатый вкус, дети отказываются пить -> лечение срывается. Выгода: Наш препарат имеет приятный вкус, обеспечит спокойный сон."
    }
}
# =========================================================

st.title("🩺 SELTFAR: SPIN-Тренажер визита к врачу")

with st.sidebar:
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
                            st.write("Оценка не сохранилась (старая версия).")
                            
                        st.markdown("**💬 Диалог:**")
                        if 'dialog' in item:
                            st.text(item['dialog'])
                        else:
                            st.write("Диалог не сохранился (старая версия).")
        
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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Ваша реплика медпреда..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Улучшенный системный промпт с заслоном от повторных приветствий
    system_prompt = f"""
    Ты — врач-педиатр Асель Аскаровна (АА). 
    Контекст сценария: {scenario_data['doctor_profile']}.
    Ожидаемые ответы по методичке SPIN: {scenario_data['expected_doctor_answers']}
    
    СТРОГИЕ ПРАВИЛА:
    1. Никогда НЕ здоровайся повторно, если диалог уже идет!
    2. Отвечай прямо на вопрос медпреда, строго 1-2 предложениями.
    3. Если медпред задает вопрос про последствия/проблему (как на слайде), отвечай точно по методичке:
       например, 'Усиливается кашель, чаще по ночам' или 'Обструкция, одышка'.
    4. Не используй шаблонные фразы вроде 'Слушаю вас внимательно'.
    """

    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        groq_messages.append({"role": m["role"], "content": m["content"]})

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=groq_messages,
            temperature=0.5,
            max_tokens=250
        )
        bot_reply = completion.choices[0].message.content
        if not bot_reply or not bot_reply.strip():
            bot_reply = "Да, я вас слушаю, продолжайте."
            
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.write(bot_reply)
    except Exception as e:
        st.error(f"⚠️ Ошибка Groq API: {e}")

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
            Ключевые факты и аргументы против конкурентов: {scenario_data['key_facts']}
            
            История диалога:
            {dialog_history}
            
            Оцени строго по пунктам:
            1. **Ситуационный вопрос (S):** Спросил ли МП, какие сиропы врач рекомендует?
            2. **Проблемный вопрос (P):** Указал ли МП на недостаток конкурента (Мунаторил/Гербион/Проспан) с точными процентами или вкусом? Задал ли вопрос "к чему это может привести?"
            3. **Усугубляющий вопрос (I):** Усугубил ли МП проблему (вопросы про ночной кашель, недосып мамы и ребенка, антибиотики)?
            4. **Направляющий вопрос / Выгода (N):** Предложил ли МП препарат SELTFAR, назвав конкретные выгоды (в X раз больше экстракта, защита)?
            5. **Итоговая оценка (от 1 до 10):** и 2-3 совета.
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
