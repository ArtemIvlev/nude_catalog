import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Пути к файлам и директориям
PHOTO_DIR = os.getenv('PHOTO_DIR', r"/mnt/smb/OneDrive/Pictures/!Фотосессии/")
DB_FILE = os.getenv('DB_FILE', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DB", "database.db")))
REVIEW_DIR = os.getenv('REVIEW_DIR', "review")
TELEGRAM_DB = os.getenv('TELEGRAM_DB', os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "telegram_bot", "published_photos.sqlite")))
LOG_DIR = os.getenv('LOG_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs")))

# Параметры базы данных
TABLE_NAME = os.getenv('TABLE_NAME', "photos_ok")

# Пороговые значения для классификации
NSFW_THRESHOLD = float(os.getenv('NSFW_THRESHOLD', "0.8"))
CLIP_THRESHOLD = float(os.getenv('CLIP_THRESHOLD', "0.8"))
MIN_IMAGE_SIZE = int(os.getenv('MIN_IMAGE_SIZE', "2500"))  # минимальный размер изображения (ширина или высота)

# Статусы фотографий
STATUS_REVIEW = "review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_PUBLISHED = "published" 