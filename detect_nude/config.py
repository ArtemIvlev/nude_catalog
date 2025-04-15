import os
import sys
from dotenv import load_dotenv

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Загружаем переменные окружения
load_dotenv()


# Пути к файлам и директориям
PHOTO_DIR = os.getenv('PHOTO_DIR', r"/mnt/smb/OneDrive/Pictures/!Фотосессии/")
DB_FILE = os.getenv('DB_FILE', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DB", "database.db")))
REVIEW_DIR = os.getenv('REVIEW_DIR', "review")
TELEGRAM_DB = os.getenv('TELEGRAM_DB', os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "telegram_bot", "published_photos.sqlite")))
LOG_DIR = os.getenv('LOG_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs")))

# Параметры PostgreSQL
POSTGRES_HOST = os.getenv('POSTGRES_HOST', '192.168.2.228')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'DB')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Passw0rd')

# Параметры базы данных
TABLE_NAME = os.getenv('TABLE_NAME', "photos_ok")

# Пороговые значения для классификации
NSFW_THRESHOLD = float(os.getenv('NSFW_THRESHOLD', "0.8"))
CLIP_THRESHOLD = float(os.getenv('CLIP_THRESHOLD', "0.8"))
MIN_IMAGE_SIZE = int(os.getenv('MIN_IMAGE_SIZE', "1500"))  # минимальный размер изображения (ширина или высота)
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', "10000"))  # максимальный размер изображения (ширина или высота)

# Статусы фотографий
STATUS_REVIEW = "review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_PUBLISHED = "published"

# Параметры базы данных SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'DB', 'database.db')

# Параметры подключения к PostgreSQL в виде словаря
PG_CONNECTION_PARAMS = {
    'host': POSTGRES_HOST,
    'port': POSTGRES_PORT,
    'database': POSTGRES_DB,
    'user': POSTGRES_USER,
    'password': POSTGRES_PASSWORD
} 

MAX_WORKERS = 1 # Ограничиваем количество процессов 
