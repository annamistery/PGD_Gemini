import requests
import os
import streamlit as st
import datetime


class ModelProcessor:
    def __init__(self, model_name=None):
        # Получаем ключ и очищаем его от возможных случайных кавычек или пробелов
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = raw_key.replace('"', '').replace("'", "").strip()

        # Используем стабильное имя модели
        self.model_name = "gemini-1.5-flash"

        # Переходим на стабильную версию v1
        self.url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_name}:generateContent?key={self.api_key}"
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

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\n\nДанные пользователя для анализа:\n{user_data}"
                }]
            }]
        }

        try:
            response = requests.post(self.url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                # Выводим подробности ошибки для диагностики
                return f"Ошибка API ({response.status_code}): {response.text}"
        except Exception as e:
            return f" Ошибка соединения: {str(e)}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
