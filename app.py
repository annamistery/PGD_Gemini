import streamlit as st
import asyncio
import edge_tts
import os
import re
import time
from datetime import datetime

# Твои импорты...
from personality_preprocessor import PersonalityCupProcessor
from pgd_bot import PGD_Person_Mod
from chashka_points import chashka
from model_preprocessor_gemini import ModelProcessor

# Настройки
MODEL_ID = "gemini-2.5-pro"

if 'ai_manager' not in st.session_state:
    st.session_state.ai_manager = ModelProcessor(model_name=MODEL_ID)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---


def clean_text_for_speech(text):
    """Очистка текста для качественной озвучки на мобильных"""
    text = re.sub(r'[\*\#\_\-\>\<\`]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def generate_voice(text):
    """Генерация аудио с защитой от кэширования мобильных браузеров"""
    clean_text = clean_text_for_speech(text)
    final_text = clean_text[:7000]

    if not final_text:
        return None

    # Уникальное имя файла критически важно для мобильных (они жестко кэшируют аудио)
    filename = f"speech_{int(time.time())}.mp3"

    # Очистка старых файлов, чтобы не забивать память на Streamlit Cloud
    for f in os.listdir():
        if f.startswith("speech_") and f.endswith(".mp3"):
            try: os.remove(f)
            except: pass

    communicate = edge_tts.Communicate(final_text, "ru-RU-SvetlanaNeural")
    await communicate.save(filename)
    return filename

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="PGD Диагностика", layout="wide")
st.title("🌟 Проективная психогенетическая диагностика")

# Состояния
if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = None
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("📋 Данные")
    name = st.text_input("Имя")
    dob = st.date_input("Дата рождения", value=None,
                        min_value=datetime(1900, 1, 1), format="DD.MM.YYYY")
    gender = st.radio("Пол", ('Женский', 'Мужской'), horizontal=True)
    process_btn = st.button("🚀 Запустить анализ", use_container_width=True)

# --- ЛОГИКА ---
if process_btn:
    if not dob or not name:
        st.error("Введите данные!")
    else:
        progress_bar = st.progress(0)
        with st.status("Обработка...", expanded=True) as status:
            # 1. Расчеты
            date_str = dob.strftime('%d.%m.%Y')
            sex_char = 'Ж' if gender == "Женский" else 'М'
            person = PGD_Person_Mod(name, date_str, sex_char)
            main_data = person.calculate_points()
            progress_bar.progress(30)

            # 2. ИИ Анализ
            data_with_context = f"ИМЯ: {name}\nДАННЫЕ:\n{str(PersonalityCupProcessor(main_data, {}, gender=sex_char).result(chashka))}"
            ai_text = st.session_state.ai_manager.get_llm_response(
                data_with_context)
            st.session_state.ai_analysis = ai_text
            progress_bar.progress(70)

            # 3. Голос (Важно: сохраняем в session_state)
            audio_path = asyncio.run(generate_voice(ai_text))
            st.session_state.audio_file = audio_path

            progress_bar.progress(100)
            status.update(label="✅ Готово!", state="complete")
        st.balloons()

# --- ВЫВОД РЕЗУЛЬТАТОВ (Оптимизировано для мобильных) ---
if st.session_state.ai_analysis:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📄 Анализ")
        st.markdown(st.session_state.ai_analysis)

    with col2:
        st.subheader("📥 Результаты")

        # Исправленный блок аудио
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
            st.write("🎵 Слушать отчет:")
            # Мы используем сохраненное имя файла из session_state
            st.audio(st.session_state.audio_file)

        # Кнопка скачивания с корректной кодировкой для смартфонов
        st.download_button(
            label="💾 Скачать текст",
            data=st.session_state.ai_analysis.encode('utf-8-sig'),
            file_name=f"PGD_{name}.txt",
            mime="text/plain",
            use_container_width=True
        )

      st.divider()

    # --- ЧАТ ---
    st.subheader("💬 Диалог с вашим профилем")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if query := st.chat_input("Задайте уточняющий вопрос..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.spinner("Анализирую..."):
                chat_context = f"Это диагностика пользователя {name}: {st.session_state.ai_analysis}. Ответь на вопрос: {query}"
                response = st.session_state.ai_manager.get_llm_response(
                    chat_context, is_chat=True)
                st.write(response)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response})
