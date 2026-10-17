# -*- coding: utf-8 -*-
"""
Анонимный антибуллинг-бот.
Автоматически проверяет и устанавливает библиотеку vkbottle при запуске.
"""

# ==================== АВТОУСТАНОВКА БИБЛИОТЕК ====================
import subprocess
import sys

def install_packages():
    try:
        import vkbottle
        print("Библиотека vkbottle уже установлена.")
    except ImportError:
        print("Библиотека vkbottle не найдена. Устанавливаю...")
        # Устанавливаем vkbottle
        subprocess.check_call([sys.executable, "-m", "pip", "install", "vkbottle"])
        print("Установка завершена!")

# Запускаем проверку/установку ДО основных импортов
install_packages()

# ==================== ОСНОВНОЙ КОД ====================

import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# ==================== НАСТРОЙКИ ====================

# --- ВК ---
VK_TOKEN = "vk1.a.4w0vaymOcHly1eOS5mLLBnrWNI0dIQLd4pEFcY2cuEQ87SICWZaYrda56L9g72gum2DmqQFmcaFHOyyuXCvDtixgiIDakD7l_EhvZgoKPpaq315XmRDbgBrl8LNKGIsGLwr6t3XS16F4uBcfp_oaI-CxImUP5ce5K_wF6eMQ9-7z2BYSeBNSJC8yJoczYqK8hjbprZpx-3ylClChDOnX5Q"

# --- Почта (Mail.ru) ---
SMTP_HOST = "smtp.mail.ru"
SMTP_PORT = 465
SMTP_USER = "school.pochta1@mail.ru"
SMTP_PASS = "qK7wVC6WXPblAom6iRPj"             # ← пароль приложения
EMAIL_TO = [
    "licey121@list.ru",                        # ← школа получает
    "school.pochta1@mail.ru",                  # ← копия вам
]

# ==================== БОТ ====================

bot = Bot(token=VK_TOKEN)

waiting = set()
last_sent = {}
SPAM_INTERVAL_SEC = 60 * 10  # 10 минут


def main_keyboard():
    kb = Keyboard(one_time=False)
    kb.add(Text("📢 Пожаловаться"), color=KeyboardButtonColor.NEGATIVE)
    return kb


def send_email(text: str):
    """Отправляет анонимный текст на почту. Полностью в UTF-8."""
    body = (
        "Анонимное сообщение от ученика\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        "--- ТЕКСТ СООБЩЕНИЯ ---\n\n"
        f"{text}\n\n"
        "--- КОНЕЦ ---\n\n"
        "Это автоматическое письмо от VK-бота.\n"
        "Личность отправителя не сохраняется и не передаётся.\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg.set_charset("utf-8")
    msg["Subject"] = Header("Анонимное сообщение от ученика", "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(EMAIL_TO)
    msg["MIME-Version"] = "1.0"
    msg["Content-Type"] = "text/plain; charset=utf-8"

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())


# ==================== ОБРАБОТЧИКИ ====================

@bot.on.message(text=["Начать", "начать", "start", "/start", "Привет", "привет", "Здравствуйте"])
async def start_handler(message: Message):
    waiting.discard(message.from_id)
    await message.answer(
        "👋 Привет!\n\n"
        "Это анонимный бот. Если тебя обижают — напиши, что случилось.\n\n"
        "Например:\n"
        "• «Меня бьёт мальчик Вадим из 6Б»\n"
        "• «Надо мной смеются в чате класса»\n"
        "• «У меня отбирают деньги старшеклассники»\n\n"
        "Твоё сообщение уйдёт школе и совету. Никто не узнает, что это ты.\n\n"
        "Нажми «📢 Пожаловаться», чтобы начать.",
        keyboard=main_keyboard()
    )


@bot.on.message(text="📢 Пожаловаться")
async def complaint_handler(message: Message):
    waiting.add(message.from_id)
    await message.answer(
        "✍️ Напиши, что случилось.\n\n"
        "Укажи класс и имя обидчика, если знаешь — так будет проще разобраться.\n\n"
        "Своё имя можешь не писать."
    )


@bot.on.message()
async def text_handler(message: Message):
    # Логируем получение (для отладки)
    print(f"[ПОЛУЧЕНО] от {message.from_id}: {message.text}")

    # Игнорируем команды
    if message.text and message.text.startswith("/"):
        return

    # Если пользователь не в режиме жалобы — просим нажать кнопку
    if message.from_id not in waiting:
        await message.answer(
            "Нажми «📢 Пожаловаться» или напиши «Начать».",
            keyboard=main_keyboard()
        )
        return

    text = message.text.strip() if message.text else ""

    # Минимальная длина
    if len(text) < 10:
        await message.answer("Напиши чуть подробнее, пожалуйста (минимум 10 символов).")
        return

    # Антиспам: 10 минут между жалобами
    now = time.time()
    if message.from_id in last_sent:
        delta = now - last_sent[message.from_id]
        if delta < SPAM_INTERVAL_SEC:
            wait_min = int((SPAM_INTERVAL_SEC - delta) // 60) + 1
            await message.answer(f"⏳ Подожди ещё ~{wait_min} мин. перед новой жалобой.")
            return

    # Отправка
    try:
        send_email(text)
        last_sent[message.from_id] = now
        await message.answer(
            "✅ Отправлено анонимно школе и совету.\n\n"
            "Если тебе страшно или больно прямо сейчас — позвони 112 "
            "или скажи взрослому, которому доверяешь.",
            keyboard=main_keyboard()
        )
    except Exception as e:
        print("Ошибка отправки:", repr(e))
        await message.answer(
            "⚠️ Не получилось отправить. Попробуй ещё раз через минуту.",
            keyboard=main_keyboard()
        )

    waiting.discard(message.from_id)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("Бот запущен. Напиши ему в ВК.")
    bot.run_forever()
