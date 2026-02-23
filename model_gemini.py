import os
import datetime
import time
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# === ЗАГРУЗКА .env ===
load_dotenv()

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === КЛИЕНТ GEMINI ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError(
        "❌ Переменная окружения GOOGLE_API_KEY не найдена. "
        "Добавь её в .env или в Secrets на Streamlit Cloud."
    )

genai.configure(api_key=GOOGLE_API_KEY)


class ModelProcessor:
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """
        Инициализация процессора для Gemini.
        """
        self.model_name = model_name
        self.prompt_path = "system_prompt.txt"

        logger.info(f"🔧 ModelProcessor (Gemini) инициализируется...")
        logger.info(f"   Модель: {self.model_name}")

    def _load_system_instruction(self, is_chat: bool = False) -> str:
        """Загрузка системного промпта."""
        if is_chat:
            return (
                "Ты — психолог-консультант, эксперт по профориентации. "
                "Отвечай кратко (2-4 предложения), конкретно и по делу. "
                "Пиши тёплым, поддерживающим тоном на русском языке. "
                "БЕЗ markdown-символов."
            )

        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    logger.info(f"✅ Системный промпт загружен из файла")
                    return content
            except Exception as e:
                logger.warning(f"⚠️ Ошибка чтения {self.prompt_path}: {e}")

        # Дефолтный промпт (тот же, что был у тебя)
        return """"Ты — психолог-консультант, эксперт по профориентации.
                Отвечай кратко (2-4 предложения), конкретно и по делу.
                Пиши тёплым, поддерживающим тоном на русском языке.
                БЕЗ markdown-символов."""

    def _get_model(self, is_chat: bool = False):
        """Создает экземпляр модели с нужными инструкциями."""
        instruction = self._load_system_instruction(is_chat)
        return genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=instruction,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 10000 if not is_chat else 5000,
            }
        )

    def get_llm_response(self, user_data: str, is_chat: bool = False) -> str:
        """Обычный запрос (не стриминг)."""
        logger.info(f"{'💬' if is_chat else '🧠'} Запрос к Gemini...")

        try:
            model = self._get_model(is_chat)
            response = model.generate_content(user_data)

            if response.text:
                return response.text.strip()
            return "❌ Модель вернула пустой ответ."

        except Exception as e:
            error_msg = f"❌ Ошибка Gemini API: {e}"
            logger.error(error_msg)
            return error_msg

    def get_streaming_response(self, user_data: str, is_chat: bool = False):
        """Стриминговый ответ (генератор)."""
        logger.info("📡 Начинаем стриминговый запрос к Gemini")

        try:
            model = self._get_model(is_chat)
            # В Gemini стриминг запускается через stream=True
            response = model.generate_content(user_data, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

            logger.info("✅ Стриминг завершён")

        except Exception as e:
            logger.error(f"Ошибка стриминга: {e}")
            yield f"[Ошибка стриминга: {e}]"

    def save_report(self, text: str, user_name: str) -> str:
        """Сохранение отчёта (логика не меняется)."""
        try:
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in user_name if c.isalnum() or c in (
                " ", "_", "-")).strip() or "user"
            filename = f"reports/{safe_name}_{timestamp}.txt"

            with open(filename, "w", encoding="utf-8-sig") as f:
                f.write(text)
            return filename
        except Exception as e:
            logger.error(f"⚠️ Не удалось сохранить отчёт: {e}")
            return ""
