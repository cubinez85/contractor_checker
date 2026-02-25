import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # База
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Почта
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 25))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Пути
    REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
    LOGS_FOLDER = os.path.join(os.path.dirname(__file__), 'logs')
    
    # Настройки проверки
    CHECK_TIMEOUT = 30  # секунд
    MAX_INN_BATCH = 100  # максимум ИНН за одну проверку
