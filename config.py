# настройки

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5/weather'