import os
import sqlite3
import hashlib
from tqdm import tqdm
import mediapipe as mp
import cv2
import sys
from clip_classifier import CLIPNudeChecker
import opennsfw2
#from opennsfw2 import predict_image_bytes
from PIL import Image
import opennsfw2 as n2
from config import *

sys.path.append("./")

# === Конфигурация ===
PHOTO_DIR = r"/mnt/smb/OneDrive/Pictures/!Фотосессии/"
DB_FILE = "database.db"
TABLE_NAME = "photos_ok"

# === Инициализация моделей ===
clip_checker = CLIPNudeChecker()
mp_face_detection = mp.solutions.face_detection
face_detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
haar_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# === База данных ===
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# === Создание таблицы, если не существует ===
def ensure_table_schema():
    cur.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        is_nude INTEGER,
        has_face INTEGER,
        hash_sha256 TEXT,
        clip_nude_score REAL,
        nsfw_score REAL,
        status TEXT DEFAULT 'new'
    )
    ''')

    existing_columns = set(
        row[1] for row in cur.execute(f"PRAGMA table_info({TABLE_NAME})")
    )
    expected_columns = {
        'clip_nude_score': "REAL",
        'nsfw_score': "REAL",
        'status': "TEXT DEFAULT 'new'"
    }
    for col, coltype in expected_columns.items():
        if col not in existing_columns:
            cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {coltype}")
    conn.commit()

ensure_table_schema()

# === Утилиты ===
def compute_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def is_valid_path(path):
    # Проверяем на наличие недопустимых символов (нулевого байта)
    if '\0' in path:
        print(f"❌ Нулевой символ в пути: {path}")
        return False
    return True

def normalize_path(path):
    # Преобразуем путь, чтобы удалить потенциально проблемные символы
    normalized_path = os.path.normpath(path)
    # Заменяем символы, которые могут быть проблемой
    normalized_path = normalized_path.replace('\0', '')  # Убираем нулевой символ
    return normalized_path

def find_all_jpgs(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            normalized_path = normalize_path(path)
            # Пропускаем путь, если он невалидный
            if file.lower().endswith(".jpg") and is_valid_path(normalized_path):
                yield normalized_path

def detect_faces_combined(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return False
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # MediaPipe
    mp_result = face_detector.process(img_rgb)
    if mp_result.detections:
        return True

    # Haar Cascade fallback
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = haar_face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    return len(faces) > 0

def get_nsfw_score(path):
    try:
        # Открываем изображение из байтов
        pil_image = Image.open(path)
        # Получаем вероятность NSFW
        return n2.predict_image(pil_image)
    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")
        return 0.0

def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            return img.size  # Возвращает кортеж (width, height)
    except Exception as e:
        print(f"Ошибка при обработке изображения {image_path}: {e}")
        return None

def is_image_small(image_path):
    size = get_image_size(image_path)
    if size:
        width, height = size
        is_small = 1 if width < MIN_IMAGE_SIZE and height < MIN_IMAGE_SIZE else 0
    return is_small

# === Основной цикл ===
all_files = list(find_all_jpgs(PHOTO_DIR))
print(f"🔍 Найдено {len(all_files)} файлов.")

for path in tqdm(all_files, desc="🔬 Анализ"):
    try:
        # Пропуск, если уже есть
        cur.execute(f"SELECT id FROM {TABLE_NAME} WHERE path = ?", (path,))
        if cur.fetchone():
            continue

        sha256 = compute_sha256(path)

        # Модель NSFW (open_nsfw2)
        nsfw_score = get_nsfw_score(path)

        # Модель CLIP
        clip_score = float(clip_checker.classify(path).get("a nude photo", 0.0))

        # Комбинация условий
        is_nude = int(nsfw_score >= NSFW_THRESHOLD or clip_score >= CLIP_THRESHOLD)

        # Лица
        has_face = int(detect_faces_combined(path))

        # маленькие картинки
        is_small = int(is_image_small(path))

        # Вставка в БД
        cur.execute(f'''
            INSERT INTO {TABLE_NAME}
            (path, is_nude, has_face, hash_sha256, clip_nude_score, nsfw_score, is_small, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'done')
        ''', (path, is_nude, has_face, sha256, clip_score, nsfw_score, is_small))
        conn.commit()

        # Отладка
        #print(f"🖼 {os.path.basename(path)} → nsfw={nsfw_score:.2f}, clip={clip_score:.2f}, face={has_face}, is_nude={is_nude}")

    except Exception as e:
        print(f"❌ Ошибка с {path}: {e}")

conn.close()
print("✅ Готово. Результаты в database.db")
