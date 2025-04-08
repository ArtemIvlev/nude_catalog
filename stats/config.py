# Пути к файлам и директориям
PHOTO_DIR = r"/mnt/smb/OneDrive/Pictures/!Фотосессии/"
DB_FILE = "database.db"
REVIEW_DIR = "review"

# Параметры базы данных
TABLE_NAME = "photos_ok"

# Пороговые значения для классификации
NSFW_THRESHOLD = 0.8
CLIP_THRESHOLD = 0.8
MIN_IMAGE_SIZE = 2500  # минимальный размер изображения (ширина или высота)

# Статусы фотографий
STATUS_REVIEW = "review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_PUBLISHED = "published" 