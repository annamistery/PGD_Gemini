import os
import streamlit as st
import requests
import datetime


class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Достаем ключ и очищаем его от всего лишнего
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = str(raw_key).replace('"', '').replace("'", "").strip()

        # 2. Используем чистый ID без префиксов
        self.model_id = "gemini-1.5-flash"

        # 3. ВАЖНО: Переходим на стабильную версию v1 (не v1beta!)
        self.url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_id}:generateContent?key={self.api_key}"
        self.prompt_path = "system_prompt.txt"

    def _load_system_instruction(self):
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "Ты эксперт-психолог и маркетолог."

    def get_llm_response(self, user_data):
        system_instruction = self._load_system_instruction()

        # Прямая структура JSON для Google API
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\n\nДАННЫЕ:\n{user_data}"
                }]
            }]
        }

        headers = {'Content-Type': 'application/json'}

        try:
            # Делаем обычный POST запрос
            response = requests.post(
                self.url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                # Выводим тело ответа, чтобы понять, что не так
                return f"Ошибка сервера ({response.status_code}): {response.text}"

        except Exception as e:
            return f"Ошибка сети: {str(e)}"

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
