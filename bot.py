import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветственное сообщение с инструкцией"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Просто напиши мне название города, и я покажу текущую погоду.\n"
        "Например: Москва или London\n\n"
        "Команды:\n"
        "/help - справка\n"
        "/weather - альтернативный способ запроса погоды"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Справка по использованию бота"""
    await update.message.reply_text(
        "Как пользоваться ботом:\n"
        "1. Просто напиши название города (например: Париж)\n"
        "2. Или используй команду /weather\n\n"
        "Бот поддерживает города на любом языке, как на русском (Москва), "
        "так и на английском (Moscow)."
    )


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Альтернативный способ запроса погоды через команду"""
    await update.message.reply_text(
        "Напиши название города, и я покажу текущую погоду:"
    )


def get_weather_data(city: str) -> dict:
    """Получение данных о погоде из API"""
    import requests
    try:
        response = requests.get(
            Config.WEATHER_API_URL,
            params={
                'q': city,
                'appid': Config.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API error: {e}")
        return None


def format_weather_message(weather_data: dict) -> str:
    """Форматирование данных о погоде в читаемое сообщение"""
    city = weather_data.get('name', 'Неизвестный город')
    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    description = weather_data['weather'][0]['description'].capitalize()
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']

    return (
        f"🌤 Погода в {city}:\n"
        f"• Температура: {temp}°C (ощущается как {feels_like}°C)\n"
        f"• Состояние: {description}\n"
        f"• Влажность: {humidity}%\n"
        f"• Ветер: {wind_speed} м/с\n\n"
        f"Обновлено: {weather_data['dt']}"
    )


async def handle_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода названия города"""
    city = update.message.text.strip()

    if len(city) < 2:
        await update.message.reply_text("Слишком короткое название города. Попробуйте еще раз.")
        return

    await update.message.reply_text(f"🔍 Ищу погоду для {city}...")

    weather_data = get_weather_data(city)

    if not weather_data or weather_data.get('cod') != 200:
        await update.message.reply_text(
            f"Не удалось найти город '{city}'. Проверьте название и попробуйте еще раз.\n"
            "Примеры: Москва, London, 東京"
        )
        return

    weather_message = format_weather_message(weather_data)
    await update.message.reply_text(weather_message)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error("Exception while handling update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
        )


def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("weather", weather_command))

    # Основной обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_input))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()