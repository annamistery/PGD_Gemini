import os
import streamlit as st
import google.generativeai as genai
import datetime


class ModelProcessor:
    def __init__(self, model_name=None):
        # 1. Получаем ключ и очищаем его
        raw_key = st.secrets.get("GEMINI_API_KEY", "")
        self.api_key = raw_key.replace('"', '').replace("'", "").strip()

        # 2. Настраиваем библиотеку Google
        genai.configure(api_key=self.api_key)

        # 3. Настройка фильтров безопасности
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 4. Настройка генерации (SEED и TEMPERATURE)
        # Установка temperature=0.0 критически важна для стабильности seed
        generation_config = {
            "temperature": 0.0,
            "seed": 42,
        }

        # 5. Инициализируем модель с конфигом
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.5-pro',
            safety_settings=safety_settings,
            generation_config=generation_config
        )
        self.prompt_path = "system_prompt.txt"

    def _load_system_instruction(self):
        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except:
                return "Ты профессиональный психолог."
        return "Ты профессиональный психолог."

    def get_llm_response(self, user_data, is_chat=False):
        system_instruction = self._load_system_instruction()
        full_prompt = f"{system_instruction}\n\nДанные для анализа:\n{user_data}"

        try:
            if not self.api_key:
                return "Ошибка: API ключ не найден в Secrets!"

            response = self.model.generate_content(full_prompt)

            if response and response.candidates:
                if response.candidates[0].content.parts:
                    return response.text
                else:
                    return "⚠️ Модель заблокировала ответ из-за фильтров. Попробуйте изменить ввод."
            else:
                return "⚠️ Сервер перегружен. Пожалуйста, попробуйте позже."

        except Exception as e:
            error_msg = str(e)
            if "User location is not supported" in error_msg:
                return "Ошибка: Регион сервера не поддерживается Gemini."
            return "⚠️ Возникла ошибка связи с ИИ. Пожалуйста, обновите страницу."

    def save_report(self, text, user_name):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{user_name}_{timestamp}.txt"

        # utf-8-sig для корректного отображения на всех устройствах
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(text)
        return filename
