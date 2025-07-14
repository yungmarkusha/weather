import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CITY, UNIT = range(2)


def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение при команде /start"""
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Я бот, который покажет тебе текущую погоду в любом городе.\n"
        "Нажми /weather чтобы узнать погоду или /help для списка команд."
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Отправляет сообщение с помощью при команде /help"""
    update.message.reply_text(
        "Доступные команды:\n"
        "/start - приветственное сообщение\n"
        "/weather - узнать погоду в городе\n"
        "/help - список команд\n"
        "Просто отправь мне название города, и я покажу погоду в нем!"
    )


def weather_command(update: Update, context: CallbackContext) -> int:
    """Начинает диалог запроса погоды"""
    update.message.reply_text(
        "В каком городе ты хочешь узнать погоду?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CITY


def get_weather(city: str, api_key: str) -> dict:
    """Получает данные о погоде с OpenWeatherMap API"""
    import requests
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }
    try:
        response = requests.get(Config.WEATHER_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе погоды: {e}")
        return None


def format_weather(weather_data: dict) -> str:
    """Форматирует данные о погоде в читаемое сообщение"""
    if not weather_data:
        return "Не удалось получить данные о погоде. Попробуйте позже."

    city = weather_data.get('name', 'Неизвестный город')
    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    humidity = weather_data['main']['humidity']
    pressure = weather_data['main']['pressure']
    wind_speed = weather_data['wind']['speed']
    description = weather_data['weather'][0]['description'].capitalize()

    return (
        f"Погода в {city}:\n"
        f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
        f"📝 {description}\n"
        f"💧 Влажность: {humidity}%\n"
        f"🌀 Давление: {pressure} hPa\n"
        f"🌬 Ветер: {wind_speed} м/с"
    )


def receive_city(update: Update, context: CallbackContext) -> int:
    """Получает город от пользователя и показывает погоду"""
    city = update.message.text
    weather_data = get_weather(city, Config.OPENWEATHER_API_KEY)

    if weather_data and weather_data.get('cod') == 200:
        message = format_weather(weather_data)
    else:
        message = "Город не найден. Пожалуйста, попробуйте еще раз."

    update.message.reply_text(message)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Завершает диалог"""
    update.message.reply_text(
        'Диалог завершен.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_text(update: Update, context: CallbackContext) -> None:
    """Обрабатывает текстовые сообщения, не являющиеся командами"""
    city = update.message.text
    weather_data = get_weather(city, Config.OPENWEATHER_API_KEY)

    if weather_data and weather_data.get('cod') == 200:
        message = format_weather(weather_data)
    else:
        message = "Город не найден. Пожалуйста, попробуйте еще раз или используйте /weather."

    update.message.reply_text(message)


def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирует ошибки"""
    logger.error(msg="Ошибка при обработке сообщения:", exc_info=context.error)
    if update.message:
        update.message.reply_text('Произошла ошибка. Пожалуйста, попробуйте позже.')


def main() -> None:
    """Запуск бота"""
    updater = Updater(Config.TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # ConversationHandler для команды /weather
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('weather', weather_command)],
        states={
            CITY: [MessageHandler(Filters.text & ~Filters.command, receive_city)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)

    # Обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Обработчик ошибок
    dispatcher.add_error_handler(error_handler)

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()