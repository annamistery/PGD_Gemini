import os
import streamlit as st
import google.generativeai as genai
import datetime


class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Получаем ключ и сохраняем его именно в self.api_key
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = raw_key.replace('"', '').replace("'", "").strip()

        # 2. Настраиваем библиотеку Google
        genai.configure(api_key=self.api_key)

        # 3. Инициализируем модель
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        self.prompt_path = "system_prompt.txt"

    def _load_system_instruction(self):
        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except:
                return "Ты профессиональный психолог и маркетолог."
        return "Ты профессиональный психолог и маркетолог."

    def get_llm_response(self, user_data):
        system_instruction = self._load_system_instruction()
        full_prompt = f"{system_instruction}\n\nДанные для анализа:\n{user_data}"

        try:
            # Теперь self.api_key существует и ошибки не будет
            if not self.api_key:
                return "Ошибка: API ключ не найден в Secrets!"

            response = self.model.generate_content(full_prompt)

            # Проверка на наличие текста в ответе
            if response and response.text:
                return response.text
            else:
                return "Модель вернула пустой ответ (возможно, сработали фильтры безопасности)."

        except Exception as e:
            error_msg = str(e)
            # Если проблема в регионе, мы увидим это сообщение
            if "User location is not supported" in error_msg:
                return "Ошибка: Сервер Streamlit находится в регионе, который не поддерживает Gemini."
            return f"Детальная ошибка SDK: {error_msg}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
