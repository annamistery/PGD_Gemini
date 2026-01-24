import os
import streamlit as st
import google.generativeai as genai
import datetime

class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Получаем ключ
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = raw_key.replace('"', '').replace("'", "").strip()

        # 2. Настраиваем библиотеку Google
        genai.configure(api_key=self.api_key)

        # 3. Инициализируем модель (используем ту, что подходит под твой ключ)
        # Если gemini-2.5-pro не сработает, попробуй без префикса 'models/'
        self.model_name = 'models/gemini-2.5-pro' 
        self.model = genai.GenerativeModel(self.model_name)
        self.prompt_path = "system_prompt.txt"
        
        # Счетчик сообщений для лимита
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

    # Добавлен параметр is_chat=False для совместимости с app.py
    def get_llm_response(self, user_data, is_chat=False):
        # Проверка лимита в 15 запросов
        if is_chat:
            if st.session_state.chat_counter >= 15:
                return "Лимит чата (15 сообщений) исчерпан. Пожалуйста, начните новый анализ."
            st.session_state.chat_counter += 1

        system_instruction = self._load_system_instruction()
        full_prompt = f"{system_instruction}\n\nДанные для анализа:\n{user_data}"

        try:
            if not self.api_key:
                return "Ошибка: API ключ не найден в Secrets!"

            response = self.model.generate_content(full_prompt)

            if response and response.text:
                return response.text
            else:
                return "Модель вернула пустой ответ. Возможно, сработали фильтры безопасности."

        except Exception as e:
            error_msg = str(e)
            # Если 404 повторится, попробуй изменить self.model_name в __init__
            return f"Детальная ошибка SDK: {error_msg}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
