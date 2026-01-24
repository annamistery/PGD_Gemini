import os
import streamlit as st
import google.generativeai as genai
import datetime

class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Загрузка ключа
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = raw_key.replace('"', '').replace("'", "").strip()

        # 2. Инициализация Google SDK
        genai.configure(api_key=self.api_key)

        # 3. Установка вашей модели (gemini-2.5-pro)
        # Если возникнет 404, попробуйте убрать префикс 'models/'
        self.model_name = 'models/gemini-2.5-pro'
        self.model = genai.GenerativeModel(self.model_name)
        self.prompt_path = "system_prompt.txt"
        
        # Счетчик для ограничения чата до 15 сообщений
        if 'chat_counter' not in st.session_state:
            st.session_state.chat_counter = 0

    def _load_system_instruction(self):
        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except:
                return "Ты профессиональный психолог и маркетолог."
        return "Ты профессиональный психолог и маркетолог."

    # ИСПРАВЛЕНИЕ: Добавлен параметр is_chat=False
    def get_llm_response(self, user_data, is_chat=False):
        # Проверка лимита запросов
        if is_chat:
            if st.session_state.chat_counter >= 15:
                return "Извините, лимит в 15 сообщений для этого чата исчерпан."
            st.session_state.chat_counter += 1

        system_instruction = self._load_system_instruction()
        full_prompt = f"{system_instruction}\n\nКонтекст запроса:\n{user_data}"

        try:
            if not self.api_key:
                return "Ошибка: API ключ не найден в настройках (Secrets)."

            # Запрос к Gemini 2.5 Pro
            response = self.model.generate_content(full_prompt)

            if response and response.text:
                return response.text
            else:
                return "Модель не смогла сгенерировать текст. Возможно, сработали фильтры безопасности."

        except Exception as e:
            return f"Детальная ошибка SDK: {str(e)}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
