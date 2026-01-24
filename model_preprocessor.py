import os
import streamlit as st
import google.generativeai as genai
import datetime


class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Получаем ключ и очищаем его
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        api_key = raw_key.replace('"', '').replace("'", "").strip()

        # 2. Настраиваем библиотеку Google
        genai.configure(api_key=api_key)

        # 3. Инициализируем модель (используем именно это название)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.prompt_path = "system_prompt.txt"

    def _load_system_instruction(self):
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "Ты профессиональный психолог и маркетолог."

    def get_llm_response(self, user_data):
        system_instruction = self._load_system_instruction()
        full_prompt = f"{system_instruction}\n\nДанные для анализа:\n{user_data}"

        try:
            # Официальный метод генерации
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            # Если будет ошибка, мы увидим её детально
            return f"Ошибка Gemini SDK: {str(e)}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
