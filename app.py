import streamlit as st
import asyncio
import edge_tts
import os
import re
import time
from datetime import datetime
import logging

# Импортируем твои модули
from model_gemini import ModelProcessor
from chashka_points import chashka
from pgd_bot import PGD_Person_Mod
from personality_preprocessor import PersonalityCupProcessor

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_MODEL_ID = "gemini-2.5-pro"

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

    filename = f"speech_{int(time.time())}.mp3"

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
        max_value=datetime.now(),
        format="DD.MM.YYYY",
    )
    gender = st.radio("Пол", ("Женский", "Мужской"), horizontal=True)
    process_btn = st.button("🚀 Запустить полный анализ", use_container_width=True)

# ==== МЕСТО ДЛЯ ВЫВОДА (Static Placeholders) ====
# Создаем пустые контейнеры заранее, чтобы порядок элементов не менялся
main_output_container = st.container()
audio_output_container = st.container()

# ==== Основная логика анализа ====
if process_btn:
    if not dob or not name:
        st.error("Пожалуйста, введите имя и дату рождения!")
    else:
        # Индикаторы процесса
        progress_bar = st.progress(0)
        status_label = st.empty()
        
        # 1. Подготовка данных
        status_label.write("📐 Расчет параметров...")
        date_str = dob.strftime("%d.%m.%Y")
        sex_char = "Ж" if gender == "Женский" else "М"
        person = PGD_Person_Mod(name, date_str, sex_char)
        main_data = person.calculate_points()
        
        processor = PersonalityCupProcessor(main_data, {}, gender=sex_char)
        raw_description = str(processor.result(chashka))
        progress_bar.progress(30)

        # 2. СТРИМИНГ ТЕКСТА
        status_label.write(f"🧠 Gemini анализирует личность {name}...")
        data_with_context = (
            f"ИМЯ ПОЛЬЗОВАТЕЛЯ: {name}\n"
            f"ДАТА РОЖДЕНИЯ: {date_str}\n"
            f"ПОЛ: {gender}\n\n"
            f"ДАННЫЕ ДИАГНОСТИКИ (PGD):\n{raw_description}"
        )

        with main_output_container:
            st.subheader("📄 Ваш персональный анализ")
            text_area = st.empty() # Место, где будет появляться текст
            full_response = ""
            
            try:
                for chunk in st.session_state.ai_manager.get_streaming_response(data_with_context, is_chat=False):
                    full_response += chunk
                    text_area.markdown(full_response + "▌")
                
                text_area.markdown(full_response) # Финальный текст без курсора
                st.session_state.ai_analysis = full_response
                progress_bar.progress(70)
            except Exception as e:
                st.error(f"Ошибка Gemini: {e}")

        # 3. ГЕНЕРАЦИЯ АУДИО (Текст уже на экране и никуда не денется)
        if st.session_state.ai_analysis:
            status_label.write("🎙 Создаю аудио-версию...")
            try:
                # Сохраняем отчет (твоя логика)
                st.session_state.ai_manager.save_report(st.session_state.ai_analysis, name)
                
                # Генерация голоса
                audio_path = asyncio.run(generate_voice(st.session_state.ai_analysis))
                st.session_state.audio_file = audio_path
                
                with audio_output_container:
                    st.divider()
                    st.subheader("🎧 Аудио-разбор")
                    st.audio(audio_path)
                    st.download_button(
                        label="💾 Скачать текстовый отчет",
                        data=st.session_state.ai_analysis.encode("utf-8-sig"),
                        file_name=f"PGD_Result_{name}.txt",
                        mime="text/plain"
                    )
                
                progress_bar.progress(100)
                status_label.empty()
                progress_bar.empty()
                st.success("✅ Все готово!")
                st.balloons()
                
            except Exception as e:
                logger.error(f"Ошибка TTS: {e}")
                status_label.error("Не удалось создать аудио, но текст доступен выше.")

# ==== ОТОБРАЖЕНИЕ ИЗ ПАМЯТИ (если страница обновилась или пишем в чат) ====
elif st.session_state.ai_analysis:
    with main_output_container:
        st.subheader("📄 Ваш персональный анализ")
        st.markdown(st.session_state.ai_analysis)
    
    if st.session_state.audio_file:
        with audio_output_container:
            st.divider()
            st.subheader("🎧 Аудио-разбор")
            st.audio(st.session_state.audio_file)
            st.download_button(
                label="💾 Скачать текстовый отчет",
                data=st.session_state.ai_analysis.encode("utf-8-sig"),
                file_name=f"PGD_Result_{name}.txt",
                mime="text/plain"
            )

# ==== ЧАТ С GEMINI ====
if st.session_state.ai_analysis:
    st.divider()
    st.subheader("💬 Дополнительные вопросы")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if query := st.chat_input("Спросите что-то конкретное о вашей матрице..."):
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            chat_placeholder = st.empty()
            full_chat_response = ""
            chat_context = (
                f"Контекст анализа пользователя {name}:\n{st.session_state.ai_analysis}\n\n"
                f"Вопрос пользователя: {query}"
            )

            try:
                for chunk in st.session_state.ai_manager.get_streaming_response(chat_context, is_chat=True):
                    full_chat_response += chunk
                    chat_placeholder.markdown(full_chat_response + "▌")
                chat_placeholder.markdown(full_chat_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_chat_response})
            except Exception as e:
                st.error(f"Ошибка чата: {e}")


