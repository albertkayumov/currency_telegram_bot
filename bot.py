# -*- coding: utf-8 -*-
"""
Основной модуль Telegram-бота для конвертации валют.
Использует библиотеку python-telegram-bot версии 20.x (асинхронную).
Реализован интерактивный интерфейс с кнопками и пошаговой конвертацией.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler
)

from currency_api import convert_currency
from database import init_db, add_record, get_user_history

# Загружаем переменные из .env файла
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler (пошаговая конвертация)
CHOOSE_FROM_CURRENCY, ENTER_AMOUNT, CHOOSE_TO_CURRENCY = range(3)

# Список доступных валют с полными названиями
AVAILABLE_CURRENCIES = {
    "USD": "Доллар США ($)",
    "EUR": "Евро (€)",
    "RUB": "Российский рубль (₽)",
    "GBP": "Британский фунт (£)",
    "JPY": "Японская йена (¥)",
    "CNY": "Китайский юань",
    "CHF": "Швейцарский франк",
    "CAD": "Канадский доллар",
    "AUD": "Австралийский доллар"
}

# Глобальный обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует ошибки и уведомляет пользователя."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😕 Произошла внутренняя ошибка. Мы уже работаем над её исправлением.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard():
    """Создаёт главную клавиатуру с кнопками 'Конвертация' и 'История'."""
    keyboard = [
        [KeyboardButton("💱 Конвертация"), KeyboardButton("📊 История")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_currency_keyboard():
    """Создаёт клавиатуру с доступными валютами."""
    keyboard = []
    row = []
    
    for i, currency_code in enumerate(AVAILABLE_CURRENCIES.keys()):
        row.append(KeyboardButton(currency_code))
        if (i + 1) % 3 == 0 or i == len(AVAILABLE_CURRENCIES) - 1:
            keyboard.append(row)
            row = []
    
    # Добавляем кнопку отмены
    keyboard.append([KeyboardButton("❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура только с кнопкой отмены."""
    return ReplyKeyboardMarkup([[KeyboardButton("❌ Отмена")]], resize_keyboard=True)

# ==================== КОМАНДЫ ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Приветственное сообщение с подробным описанием возможностей бота.
    Отображает главное меню с кнопками.
    """
    user = update.effective_user
    
    welcome_text = (
        f"👋 *Привет, {user.first_name}!*\n\n"
        "Я — *интеллектуальный ассистент для конвертации валют*.\n\n"
        "🎯 *Мои возможности:*\n"
        "• Пошаговая конвертация с выбором из списка валют\n"
        "• Сохранение истории ваших запросов\n"
        "• Работа с основными мировыми валютами\n\n"
        "🛠 *Технологии, использованные в проекте:*\n"
        "• `SQLite` — хранение истории запросов\n"
        "• `python-telegram-bot` — асинхронный фреймворк\n"
        "• `ExchangeRate-API` — получение актуальных курсов валют\n\n"
        "📌 *Как пользоваться:*\n"
        "1️⃣ Нажмите *\"💱 Конвертация\"* для пошагового выбора валют и суммы\n"
        "2️⃣ Нажмите *\"📊 История\"* чтобы посмотреть последние 5 запросов\n"
        "3️⃣ Нажмите *\"❓ Помощь\"* для получения справки\n\n"
        "Выберите действие на клавиатуре ниже 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по использованию бота с подробным описанием валют."""
    
    # Формируем список валют с описаниями
    currencies_list = []
    for code, description in AVAILABLE_CURRENCIES.items():
        currencies_list.append(f"• *{code}* — {description}")
    
    help_text = (
        "ℹ️ *Справка по использованию*\n\n"
        "🔹 *Пошаговая конвертация:*\n"
        "Нажмите кнопку \"💱 Конвертация\" и следуйте инструкциям:\n"
        "1. Выберите исходную валюту\n"
        "2. Введите сумму\n"
        "3. Выберите целевую валюту\n\n"
        "🔹 *Просмотр истории:*\n"
        "Нажмите \"📊 История\" или отправьте команду /history\n\n"
        "🔹 *Поддерживаемые валюты:*\n"
        f"{chr(10).join(currencies_list)}\n\n"
        "🔹 *Доступные команды:*\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/history — история запросов"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает последние 5 запросов пользователя."""
    user = update.effective_user
    records = get_user_history(user.id, limit=5)

    if not records:
        await update.message.reply_text(
            "📭 Ваша история пуста. Сделайте первый запрос!",
            reply_markup=get_main_keyboard()
        )
        return

    lines = ["📊 *Ваши последние запросы:*\n"]
    for amount, from_cur, to_cur, result, timestamp in records:
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            time_str = "дата неизвестна"
        
        lines.append(
            f"• `{amount:.2f} {from_cur}` → `{result:.2f} {to_cur}`\n"
            f"  _{time_str}_"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== ПОШАГОВАЯ КОНВЕРТАЦИЯ ====================

async def start_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает пошаговую конвертацию. Шаг 1: выбор исходной валюты."""
    await update.message.reply_text(
        "🔄 *Пошаговая конвертация*\n\n"
        "*Шаг 1 из 3:* Выберите *исходную валюту* (из какой конвертируем):",
        parse_mode="Markdown",
        reply_markup=get_currency_keyboard()
    )
    return CHOOSE_FROM_CURRENCY

async def choose_from_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет исходную валюту и запрашивает сумму."""
    currency = update.message.text.strip().upper()
    
    if currency == "❌ ОТМЕНА":
        await cancel_conversion(update, context)
        return ConversationHandler.END
    
    if currency not in AVAILABLE_CURRENCIES:
        await update.message.reply_text(
            f"❌ Валюта {currency} не поддерживается. Выберите из списка:",
            reply_markup=get_currency_keyboard()
        )
        return CHOOSE_FROM_CURRENCY
    
    # Сохраняем исходную валюту в контексте пользователя
    context.user_data['from_currency'] = currency
    
    await update.message.reply_text(
        f"✅ Исходная валюта: *{currency}* ({AVAILABLE_CURRENCIES[currency]})\n\n"
        "*Шаг 2 из 3:* Введите *сумму* для конвертации (только число):\n"
        "Например: `100` или `50.5`",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ENTER_AMOUNT

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет сумму и запрашивает целевую валюту."""
    text = update.message.text.strip()
    
    if text == "❌ Отмена":
        await cancel_conversion(update, context)
        return ConversationHandler.END
    
    # Пытаемся преобразовать в число
    try:
        # Заменяем запятую на точку для дробных чисел
        text = text.replace(',', '.')
        amount = float(text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное *положительное число*.\n"
            "Например: `100` или `50.5`",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ENTER_AMOUNT
    
    # Сохраняем сумму
    context.user_data['amount'] = amount
    
    await update.message.reply_text(
        f"✅ Сумма: *{amount:,.2f} {context.user_data['from_currency']}*\n\n"
        "*Шаг 3 из 3:* Выберите *целевую валюту* (в какую конвертируем):",
        parse_mode="Markdown",
        reply_markup=get_currency_keyboard()
    )
    return CHOOSE_TO_CURRENCY

async def choose_to_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выполняет конвертацию и показывает результат."""
    user = update.effective_user
    currency = update.message.text.strip().upper()
    
    if currency == "❌ ОТМЕНА":
        await cancel_conversion(update, context)
        return ConversationHandler.END
    
    if currency not in AVAILABLE_CURRENCIES:
        await update.message.reply_text(
            f"❌ Валюта {currency} не поддерживается. Выберите из списка:",
            reply_markup=get_currency_keyboard()
        )
        return CHOOSE_TO_CURRENCY
    
    # Получаем сохранённые данные
    from_cur = context.user_data['from_currency']
    amount = context.user_data['amount']
    to_cur = currency
    
    # Выполняем конвертацию
    result = convert_currency(amount, from_cur, to_cur)
    
    if result is None:
        await update.message.reply_text(
            "⚠️ Не удалось получить курс валют. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Формируем ответ
    response_text = (
        f"✅ *Конвертация выполнена!*\n\n"
        f"`{amount:,.2f} {from_cur}` ({AVAILABLE_CURRENCIES[from_cur]})\n"
        f"=\n"
        f"`{result:,.2f} {to_cur}` ({AVAILABLE_CURRENCIES[to_cur]})\n\n"
        f"_Курс: 1 {from_cur} = {(result/amount):,.4f} {to_cur}_"
    )
    
    await update.message.reply_text(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Сохраняем в историю
    username = user.username if user.username else user.full_name
    add_record(
        user_id=user.id,
        username=username,
        request_text=f"[Пошаговая] {amount} {from_cur} to {to_cur}",
        amount=amount,
        from_cur=from_cur,
        to_cur=to_cur,
        result=result
    )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет пошаговую конвертацию."""
    await update.message.reply_text(
        "❌ Конвертация отменена.",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# ==================== ОБРАБОТЧИК КНОПОК ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки главного меню."""
    text = update.message.text
    
    if text == "💱 Конвертация":
        return await start_conversion(update, context)
    elif text == "📊 История":
        return await history_command(update, context)
    elif text == "❓ Помощь":
        return await help_command(update, context)
    else:
        # На всякий случай, если что-то пошло не так
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

def main():
    """Точка входа в приложение."""
    # Инициализируем базу данных
    init_db()
    
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Создаём ConversationHandler для пошаговой конвертации
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💱 Конвертация$"), start_conversion),
        ],
        states={
            CHOOSE_FROM_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_from_currency)
            ],
            ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)
            ],
            CHOOSE_TO_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_to_currency)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Отмена$"), cancel_conversion)
        ],
    )
    
    app.add_handler(conv_handler)

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    
    # Обработчик кнопок главного меню
    app.add_handler(MessageHandler(
        filters.Regex("^(💱 Конвертация|📊 История|❓ Помощь)$"),
        button_handler
    ))
    
    # Глобальный обработчик ошибок
    app.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("Бот запущен с интерактивным меню...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()