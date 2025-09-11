from flask import current_app as app
import time
import sqlite3
import asyncio
from googletrans import Translator


def detect_language(title) -> tuple[str, bool]:
    try:
        conn_lang = sqlite3.connect('data/detect_language.sqlite3')
        cursor_lang = conn_lang.cursor()
        cursor_lang.execute("SELECT lang, confidence FROM titles WHERE title = ?", (title,))
        row = cursor_lang.fetchone()
        if row:
            lang, confidence = row
            conn_lang.close()
            return lang, confidence > 0.8

        translator = Translator()

        def _detect_language(text):
            result = asyncio.run(translator.detect(text))
            return result.lang, result.confidence

        lang, confidence = _detect_language(title)
        timestamp = int(time.time())
        cursor_lang.execute(
            "INSERT OR REPLACE INTO titles (title, lang, confidence, timestamp) VALUES (?, ?, ?, ?)",
            (title, lang, confidence, timestamp)
        )
        conn_lang.commit()
        conn_lang.close()

        return lang, confidence > 0.8
    except Exception as e:
        app.logger.error(f"for {title}: {e}")
        return "_", False