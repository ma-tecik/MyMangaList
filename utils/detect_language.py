from flask import current_app as app
from time import time
import sqlite3
import asyncio
from googletrans import Translator


def detect_language(name) -> tuple[str, bool]:
    try:
        conn_lang = sqlite3.connect('utils/detect_language.sqlite3')
        cursor_lang = conn_lang.cursor()
        cursor_lang.execute("SELECT lang, confidence FROM names WHERE name = ?", (name,))
        row = cursor_lang.fetchone()
        if row:
            lang, confidence = row
            return lang, confidence > 0.8

        translator = Translator()

        def _detect_language(text):
            result = asyncio.run(translator.detect(text))
            return result.lang, result.confidence

        lang, confidence = _detect_language(name)
        timestamp = int(time())
        cursor_lang.execute(
            "INSERT OR REPLACE INTO names (name, lang, confidence, timestamp) VALUES (?, ?, ?, ?)",
            (name, lang, confidence, timestamp)
        )
        conn_lang.commit()
        conn_lang.close()

        return lang, confidence > 0.8
    except Exception as e:
        app.logger.error(f"for {name}: {e}")
        return "_", False

if __name__ == '__main__':
    print(detect_language("""Nanyou Laile Da Yima?!"""))
