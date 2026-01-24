

import requests
import os
import streamlit as st


class ModelProcessor:
    # Добавляем аргумент model_name, чтобы app.py не выдавал ошибку
    def __init__(self, model_name="gemini-1.5-flash"):
        # Если в app.py передается что-то другое, мы все равно можем
        # принудительно использовать gemini или оставить переданное значение
        self.api_key = st.secrets.get("GEMINI_API_KEY", ".streamlit")
        self.model_name = model_name
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        self.prompt_path = "system_prompt.txt"

    # ... остальной код метода get_llm_response остается прежним ...
    def _load_system_instruction(self):
        try:
            if os.path.exists(self.prompt_path):
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return "Ты — эксперт-психолог."
        except:
            return "Ты — эксперт-психолог."

    def get_llm_response(self, user_data):
        system_instruction = self._load_system_instruction()

        # Формируем структуру запроса специально для Gemini
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\n\nДАННЫЕ ДЛЯ АНАЛИЗА:\n{user_data}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.0,  # Твоя любимая стабильность
                "maxOutputTokens": 2048
            }
        }

        try:
            response = requests.post(self.url, json=payload, timeout=30)
            if response.status_code == 200:
                # Извлекаем текст из ответа Gemini
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"Ошибка Gemini API: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Ошибка подключения: {str(e)}"

    def save_report(self, text, user_name):
        """Сохраняет отчет в текстовый файл в папку reports"""
        import os
        from datetime import datetime
        # Создаем папку reports, если её нет
        if not os.path.exists("reports"):
            os.makedirs("reports")
        # Формируем имя файла: Имя_Дата.txt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            return filename
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            return None
