import os
import sys
import cv2
import numpy as np
from PIL import Image
import sqlite3
import torch
import hashlib
from tqdm import tqdm
from face_detector import FaceDetector
from datetime import datetime
import tensorflow as tf
import logging
from nsfw_detector import MarqoNSFWDetector
from clip_classifier import CLIPNudeChecker
from opennsfw2_detector import OpenNSFW2Detector
from face_detector import FaceDetector

logger = logging.getLogger(__name__)

sys.path.append("./")

# === Конфигурация ===
PHOTO_DIR = r"/mnt/smb/OneDrive/Pictures/!Фотосессии/"
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DB", "database.db"))
TABLE_NAME = "photos_ok"
MIN_IMAGE_SIZE = 100
MAX_IMAGE_SIZE = 10000

# === База данных ===
def connect_db():
    """Подключение к базе данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None

def ensure_table_schema(conn):
    """Создание таблицы, если не существует"""
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        is_nude INTEGER,
        has_face INTEGER,
        hash_sha256 TEXT,
        clip_nude_score REAL,
        nsfw_score REAL,
        status TEXT DEFAULT 'new',
        is_small INTEGER,
        phash TEXT,
        views INTEGER,
        forwards INTEGER,
        reactions INTEGER,
        predicted_likes INTEGER,
        subscribers INTEGER,
        normalized_views REAL,
        normalized_forwards REAL,
        publication_date TEXT,
        message_id TEXT
    )
    ''')
    
    # Проверяем наличие всех необходимых колонок
    existing_columns = set(
        row[1] for row in cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    )
    expected_columns = {
        'clip_nude_score': "REAL",
        'nsfw_score': "REAL",
        'status': "TEXT DEFAULT 'new'",
        'is_small': "INTEGER",
        'phash': "TEXT",
        'views': "INTEGER",
        'forwards': "INTEGER",
        'reactions': "INTEGER",
        'predicted_likes': "INTEGER",
        'subscribers': "INTEGER",
        'normalized_views': "REAL",
        'normalized_forwards': "REAL",
        'publication_date': "TEXT",
        'message_id': "TEXT"
    }
    
    for col, coltype in expected_columns.items():
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {coltype}")
    
    conn.commit()

# === Утилиты ===
def compute_sha256(filepath):
    """Вычисление SHA256 хеша файла"""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def is_valid_path(path):
    """Проверка пути на наличие недопустимых символов"""
    if '\0' in path:
        logger.error(f"❌ Нулевой символ в пути: {path}")
        return False
    return True

def normalize_path(path):
    """Нормализация пути"""
    normalized_path = os.path.normpath(path)
    normalized_path = normalized_path.replace('\0', '')
    return normalized_path

def find_all_jpgs(directory):
    """Поиск всех JPG файлов в директории"""
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            normalized_path = normalize_path(path)
            if file.lower().endswith(".jpg") and is_valid_path(normalized_path):
                yield normalized_path

def get_image_dimensions(image_path):
    """Получение размеров изображения"""
    with Image.open(image_path) as img:
        return img.size

def check_image_size(image_path):
    """Проверка размеров изображения"""
    try:
        width, height = get_image_dimensions(image_path)
        return (MIN_IMAGE_SIZE <= width <= MAX_IMAGE_SIZE and 
                MIN_IMAGE_SIZE <= height <= MAX_IMAGE_SIZE)
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке размеров изображения: {str(e)}")
        return False

def is_normal_size(width, height):
    """Проверка нормальности размеров изображения"""
    return (MIN_IMAGE_SIZE <= width <= MAX_IMAGE_SIZE and 
            MIN_IMAGE_SIZE <= height <= MAX_IMAGE_SIZE)

def is_image_small(image_path):
    """Проверка, является ли изображение маленьким"""
    size = get_image_dimensions(image_path)
    if size:
        width, height = size
        return 1 if width < MIN_IMAGE_SIZE or height < MIN_IMAGE_SIZE else 0
    return 0

def analyze_photo(image_path):
    """
    Анализирует изображение на наличие NSFW контента
    """
    try:
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"❌ Не удалось загрузить изображение: {image_path}")
            return None
            
        # Получаем размеры изображения
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        # Анализируем NSFW контент
        nsfw_detector = MarqoNSFWDetector()
        nsfw_result = nsfw_detector.analyze_image(image_path)
        
        # Безопасно получаем данные NSFW анализа
        nsfw_score = nsfw_result.get('nsfw_score', 0.0)
        is_nsfw = nsfw_result.get('is_nsfw', False)
        confidence = nsfw_result.get('confidence', 0.0)
        
        # Анализируем OpenNSFW2
        opennsfw2_detector = OpenNSFW2Detector()
        opennsfw2_result = opennsfw2_detector.analyze_image(image_path)
        

        # Загружаем изображение

        
        # Создаем детектор лиц
        face_detector = FaceDetector()
        
        # Обнаруживаем лица
        result = face_detector.detect_faces(image)
        
        # Выводим результаты
        face_count = result.get('face_count', 0)
        face_locations = result.get('face_locations', [])
        face_angles = result.get('face_angles', [])
        
        logger.info(f"👥 Обнаружено лиц: {face_count}")
        
   

        # Объединяем результаты
        result = {
            'nsfw_score': nsfw_score,
            'is_erotic': is_nsfw,
            'confidence': confidence,
            'details': {
                'nsfw_analysis': nsfw_result,
                'opennsfw2_analysis': opennsfw2_result
            },
            'face_count': face_count,
            'face_locations': face_locations,
            'face_angles': face_angles,
            'face_landmarks': []
        }
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Ошибка при анализе изображения: {str(e)}")
        return None

def process_image(image_path):
    """
    Обрабатывает одно изображение и возвращает результат анализа
    
    Args:
        image_path: путь к изображению
        
    Returns:
        dict: результат анализа или None в случае ошибки
    """
    try:
        # Проверяем размеры изображения
        if not check_image_size(image_path):
            logger.warning(f"⚠️ Изображение слишком маленькое или большое: {image_path}")
            return None
            
        # Анализируем фото
        result = analyze_photo(image_path)
        if result is None:
            return None
            
        # Получаем результаты анализа
        nsfw_score = float(result['nsfw_score'])
        is_erotic = bool(result['is_erotic'])
        confidence = float(result['confidence'])
        
        # Определяем категорию на основе всех доступных данных
        is_nsfw = nsfw_score > 0.5 or is_erotic
        
        # Если есть детали от OpenNSFW2, учитываем их
        if 'details' in result and 'opennsfw2_analysis' in result['details']:
            opennsfw2_score = result['details']['opennsfw2_analysis'].get('nsfw_score', 0.0)
            # Если OpenNSFW2 считает изображение NSFW с высокой уверенностью
            if opennsfw2_score > 0.8:
                is_nsfw = True
                confidence = max(confidence, opennsfw2_score)
        
        # Определяем финальную категорию
        category = 'unsafe' if is_nsfw else 'safe'
        
        return {
            'path': image_path,
            'category': category,
            'nsfw_score': nsfw_score,
            'is_erotic': is_erotic,
            'confidence': confidence,
            'face_count': result.get('face_count', 0),
            'face_locations': result.get('face_locations', []),
            'face_angles': result.get('face_angles', []),
            'face_landmarks': result.get('face_landmarks', []),
            'details': result.get('details', {})
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке {image_path}: {str(e)}")
        return None

def print_result(result):
    """Вывод результатов анализа в консоль"""
    if result:
        print(f"\nРезультаты анализа:")
        print(f"Путь к изображению: {result['path']}")
        print(f"Размеры: {result['dimensions']['width']}x{result['dimensions']['height']}")
        print(f"Количество каналов: {result['dimensions']['channels']}")
        
        # NSFW анализ
        nsfw_analysis = result['details']['nsfw_analysis']
        print(f"Модель: {nsfw_analysis.get('model', 'Неизвестно')}")
        print(f"NSFW анализ: {'NSFW' if nsfw_analysis['is_nsfw'] else 'Безопасное'}")
        print(f"NSFW оценка: {nsfw_analysis['nsfw_score']:.4f}")
        print(f"Безопасная оценка: {nsfw_analysis['safe_score']:.4f}")
        print(f"Уверенность: {nsfw_analysis['confidence']:.4f}")
        print("Детали NSFW:")
        for class_name, score in nsfw_analysis['details'].items():
            print(f"  {class_name}: {score:.4f}")
        
        # OpenNSFW2 анализ
        opennsfw2_analysis = result['details']['opennsfw2_analysis']
        print("OpenNSFW2 анализ:")
        print(f"  NSFW: {opennsfw2_analysis['nsfw_score']:.4f}")
        print(f"  Безопасное: {opennsfw2_analysis['safe_score']:.4f}")
    else:
        print("Не удалось проанализировать изображение")

def process_directory(directory_path):
    """
    Обработка всех изображений в директории
    
    Args:
        directory_path: путь к директории с изображениями
    """
    # Подключаемся к БД
    conn = connect_db()
    if not conn:
        return
    
    # Создаем таблицу, если не существует
    ensure_table_schema(conn)
    cursor = conn.cursor()
    
    # Получаем список всех файлов
    try:
        all_files = list(find_all_jpgs(directory_path))
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении директории: {e}")
        return
        
    total_files = len(all_files)
    processed = 0
    safe_count = 0
    unsafe_count = 0
    
    logger.info(f"\n🔍 Найдено файлов: {total_files}")
    
    # Обрабатываем каждый файл
    for path in tqdm(all_files, desc="🔬 Анализ"):
        processed += 1
        
        # Пропуск, если уже есть
        cursor.execute(f"SELECT id FROM {TABLE_NAME} WHERE path = ?", (path,))
        if cursor.fetchone():
            continue
        
        logger.info(f"[{processed}/{total_files}] Обработка: {os.path.basename(path)}")
        
        # Вычисляем хеш
        sha256 = compute_sha256(path)
        
        # Проверяем изображение
        result = process_image(path)
        if result:
            is_safe = not result['is_erotic']
            nsfw_score = result['nsfw_score']
            confidence = result['confidence']
            face_count = result['face_count']
            
            # Получаем opennsfw2_score
            opennsfw2_score = 0.0
            if 'details' in result and 'opennsfw2_analysis' in result['details']:
                opennsfw2_score = result['details']['opennsfw2_analysis'].get('nsfw_score', 0.0)
            
            # Увеличиваем счетчики
            if is_safe:
                safe_count += 1
            else:
                unsafe_count += 1
            
            logger.info(f"path {path}")
            logger.info(f"is_safe {is_safe}")
            logger.info(f"confidence {confidence}")
            logger.info(f"face_count {face_count}")
            logger.info(f"opennsfw2_score {opennsfw2_score}")
            
            logger.info(f"--------------------------------")
            
            # Определяем, есть ли лица
            has_face = face_count > 0
            
            # Определяем, маленькое ли изображение
            is_small = is_image_small(path)
            
            # Обновляем БД
            try:
                status = 'review'
                
                cursor.execute(f'''
                    INSERT INTO {TABLE_NAME}
                    (path, is_nude, has_face, hash_sha256, clip_nude_score, nsfw_score, is_small, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (path, int(not is_safe), has_face, sha256, opennsfw2_score, nsfw_score, is_small, status))
                
                conn.commit()
                
                # Выводим результат
                status_text = "✅ Безопасно" if is_safe else "❌ Небезопасно"
                logger.info(f"  {status_text} (уверенность: {confidence:.3f})")
                    
            except sqlite3.Error as e:
                logger.error(f"  ❌ Ошибка при обновлении БД: {e}")
        else:
            logger.error(f"❌ Ошибка при обработке {path}")
    
    # Выводим итоги
    logger.info("\n📊 Итоги:")
    logger.info(f"  - Всего обработано: {total_files}")
    logger.info(f"  - Безопасно: {safe_count}")
    logger.info(f"  - Небезопасно: {unsafe_count}")
    
    conn.close()

def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        directory_path = PHOTO_DIR
        
    if not os.path.isdir(directory_path):
        logger.error(f"❌ Ошибка: {directory_path} не является директорией")
        return
        
    process_directory(directory_path)

if __name__ == "__main__":
    main()
