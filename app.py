# app.py
# ⬅️ Теперь импортируем обновленный класс для Gemini
from model_gemini import ModelProcessor
from chashka_points import chashka
from pgd_bot import PGD_Person_Mod
from personality_preprocessor import PersonalityCupProcessor
import streamlit as st
import asyncio
import edge_tts
import os
import re
import time
from datetime import datetime
import logging

from model_gemini import ModelProcessor

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Импортируем новый файл
...
GEMINI_MODEL_ID = "gemini-2.5-pro"  # Или "gemini-1.5-flash" для скорости
...
if "ai_manager" not in st.session_state:
    st.session_state.ai_manager = ModelProcessor(model_name=GEMINI_MODEL_ID)

# ==== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def clean_text_for_speech(text: str) -> str:
    """Очистка текста от Markdown и спецсимволов для TTS."""
    text = re.sub(r"[\*\#\_\-\>\<\`]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def generate_voice(text: str):
    """Генерация аудиофайла через Microsoft Edge TTS."""
    clean_text = clean_text_for_speech(text)
    final_text = clean_text[:7000]
    if not final_text:
        return None

    # Уникальное имя файла
    filename = f"speech_{int(time.time())}.mp3"

    # Чистим старые файлы
    for f in os.listdir():
        if f.startswith("speech_") and f.endswith(".mp3"):
            try:
                os.remove(f)
            except:
                pass

    communicate = edge_tts.Communicate(final_text, "ru-RU-SvetlanaNeural")
    await communicate.save(filename)
    return filename


# ==== UI ====
st.set_page_config(page_title="PGD Диагностика", layout="wide")
st.title("🌟 Карта личности (Gemini Edition)")

with st.expander("📖 Инструкция по применению", expanded=False):
    st.write("""
    1. **Введите данные**: Имя, дату рождения и пол.
    2. **Анализ**: Нажмите 'Запустить полный анализ'.
    3. **Результат**: Получите текстовый и аудио-разбор от Gemini.
    4. **Чат**: Задавайте уточняющие вопросы внизу.
    """)

# Состояния (Session State)
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# ==== Сайдбар: ввод данных ====
with st.sidebar:
    st.header("📋 Данные пользователя")
    name = st.text_input("Имя", placeholder="Введите ваше имя")
    dob = st.date_input(
        "Дата рождения",
        value=None,
        min_value=datetime(1900, 1, 1),
        format="DD.MM.YYYY",
    )
    gender = st.radio("Пол", ("Женский", "Мужской"), horizontal=True)

    process_btn = st.button("🚀 Запустить полный анализ",
                            use_container_width=True)

# ==== Основная логика анализа ====
if process_btn:
    if not dob or not name:
        st.error("Пожалуйста, введите имя и дату рождения!")
    else:
        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        with status_placeholder.container():
            st.write("📐 Расчет параметров матрицы...")
            progress_bar.progress(10)

            # 1. PGD расчёты
            date_str = dob.strftime("%d.%m.%Y")
            sex_char = "Ж" if gender == "Женский" else "М"
            person = PGD_Person_Mod(name, date_str, sex_char)
            main_data = person.calculate_points()

            progress_bar.progress(20)

            # 2. Препроцессор данных
            st.write("🔍 Сбор текстовых описаний...")
            processor = PersonalityCupProcessor(main_data, {}, gender=sex_char)
            raw_description = str(processor.result(chashka))
            progress_bar.progress(30)

            # 3. Модель Gemini — формируем итоговый текст
            st.write(f"🧠 Gemini формирует глубокий отчет для {name}...")
            data_with_context = (
                f"ИМЯ ПОЛЬЗОВАТЕЛЯ: {name}\n"
                f"ДАТА РОЖДЕНИЯ: {date_str}\n"
                f"ПОЛ: {gender}\n\n"
                f"ДАННЫЕ ДИАГНОСТИКИ (PGD):\n{raw_description}"
            )

            # === СТРИМИНГ ОТВЕТА (АНАЛИЗ) ===
            try:
                response_placeholder = st.empty()
                full_response = ""

                # Передаем is_chat=False для использования полного системного промпта
                for chunk in st.session_state.ai_manager.get_streaming_response(
                    data_with_context, is_chat=False
                ):
                    full_response += chunk
                    response_placeholder.markdown(full_response + " ")

                response_placeholder.markdown(full_response)
                st.session_state.ai_analysis = full_response

            except Exception as e:
                logger.error(f"Ошибка Gemini при анализе: {e}")
                st.error(f"Произошла техническая ошибка: {e}")

            progress_bar.progress(80)

            # 4. Голос + сохранение
            st.write("🎙 Синтез речи...")
            try:
                st.session_state.ai_manager.save_report(
                    st.session_state.ai_analysis, name)
                audio_path = asyncio.run(
                    generate_voice(st.session_state.ai_analysis))
                st.session_state.audio_file = audio_path
            except Exception as e:
                logger.warning(f"Ошибка постобработки: {e}")

            progress_bar.progress(100)
            st.success("✅ Анализ готов!")
            st.balloons()

# ==== Вывод результатов ====
if st.session_state.ai_analysis:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📄 Ваш персональный анализ")
        st.markdown(st.session_state.ai_analysis)

    with col2:
        st.subheader("📥 Результаты")
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
            st.audio(st.session_state.audio_file)

        st.download_button(
            label="💾 Скачать отчет",
            data=st.session_state.ai_analysis.encode("utf-8-sig"),
            file_name=f"PGD_Result_{name}.txt",
            mime="text/plain",
        )

    st.divider()

    # ==== ЧАТ С GEMINI ====
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
            chat_placeholder = st.empty()
            full_chat_response = ""

            # Контекст для чата: анализ + новый вопрос
            chat_context = (
                f"Контекст анализа пользователя {name}:\n{st.session_state.ai_analysis}\n\n"
                f"Вопрос пользователя: {query}"
            )

            try:
                # Передаем is_chat=True для кратких ответов
                for chunk in st.session_state.ai_manager.get_streaming_response(
                    chat_context, is_chat=True
                ):
                    full_chat_response += chunk
                    chat_placeholder.markdown(full_chat_response + " ")

                chat_placeholder.markdown(full_chat_response)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": full_chat_response}
                )
            except Exception as e:
                st.error(f"Ошибка чата: {e}")
