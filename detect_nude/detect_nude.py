import os
import sys

# Добавляем путь к корневой директории nude_catalog
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import gc
from PIL.ExifTags import TAGS
import time
import imagehash

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from config import (
    PHOTO_DIR, DB_FILE, TABLE_NAME, MIN_IMAGE_SIZE,
    MAX_IMAGE_SIZE, MAX_WORKERS, NSFW_THRESHOLD,
    CLIP_THRESHOLD, STATUS_REVIEW, STATUS_APPROVED,
    STATUS_REJECTED, STATUS_PUBLISHED
)

logger = logging.getLogger(__name__)

sys.path.append("./")

# Настройка TensorFlow для GPU
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    try:
        # Включаем память GPU по требованию
        for device in physical_devices:
            tf.config.experimental.set_memory_growth(device, True)
        logger.info(f"✅ Найдено {len(physical_devices)} GPU устройств")
    except RuntimeError as e:
        logger.error(f"❌ Ошибка при настройке GPU: {e}")
else:
    logger.warning("⚠️ GPU не найдены, используется CPU")

# Оптимизация производительности
tf.config.optimizer.set_jit(True)  # Включаем XLA оптимизации
tf.config.optimizer.set_experimental_options({
    'layout_optimizer': True,
    'constant_folding': True,
    'shape_optimization': True,
    'remapping': True,
    'arithmetic_optimization': True,
    'dependency_optimization': True,
    'loop_optimization': True,
    'function_optimization': True,
    'debug_stripper': True,
})

logger.info("✅ TensorFlow настроен для работы на CPU")

# Инициализация глобальных моделей
logger.info("🔄 Инициализация моделей...")
nsfw_detector = MarqoNSFWDetector()
opennsfw2_detector = OpenNSFW2Detector()
face_detector = FaceDetector()
logger.info("✅ Модели инициализированы")

def connect_db():
    """Подключение к базе данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None

def get_image_dates(image_path):
    """
    Получает дату съемки и дату изменения изображения
    
    Args:
        image_path: путь к изображению
        
    Returns:
        tuple: (дата_съемки, дата_изменения) в формате ISO
    """
    try:
        # Получаем дату изменения файла
        mtime = os.path.getmtime(image_path)
        modification_date = datetime.fromtimestamp(mtime).isoformat()
        
        # Пытаемся получить дату съемки из EXIF
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif:
                # Ищем теги с датой
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        # Преобразуем строку даты в ISO формат
                        date_str = exif[tag_id]
                        try:
                            shooting_date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').isoformat()
                            return shooting_date, modification_date
                        except ValueError:
                            pass
                    elif tag == 'DateTimeDigitized':
                        # Альтернативный тег даты
                        date_str = exif[tag_id]
                        try:
                            shooting_date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').isoformat()
                            return shooting_date, modification_date
                        except ValueError:
                            pass
        
        # Если не нашли дату съемки, используем дату изменения
        return modification_date, modification_date
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении дат изображения {image_path}: {str(e)}")
        # В случае ошибки возвращаем текущую дату
        current_date = datetime.now().isoformat()
        return current_date, current_date

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
        message_id TEXT,
        shooting_date TEXT,
        modification_date TEXT
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
        'message_id': "TEXT",
        'shooting_date': "TEXT",
        'modification_date': "TEXT"
    }
    
    for col, coltype in expected_columns.items():
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {coltype}")
    
    conn.commit()

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
        
        # Вычисляем phash
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            phash = str(imagehash.average_hash(pil_image))
        except Exception as e:
            logger.error(f"❌ Ошибка при вычислении phash: {str(e)}")
            phash = None
        
        # Анализируем NSFW контент
        nsfw_result = nsfw_detector.analyze_image(image_path)
        
        # Безопасно получаем данные NSFW анализа
        nsfw_score = nsfw_result.get('nsfw_score', 0.0)
        is_nsfw = nsfw_result.get('is_nsfw', False)
        confidence = nsfw_result.get('confidence', 0.0)
        
        # Анализируем OpenNSFW2
        opennsfw2_result = opennsfw2_detector.analyze_image(image_path)
        
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
            'face_landmarks': [],
            'phash': phash
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
            
        # Получаем даты изображения
        shooting_date, modification_date = get_image_dates(image_path)
            
        # Анализируем фото
        result = analyze_photo(image_path)
        if result is None:
            return None
            
        # Безопасно получаем результаты анализа
        nsfw_score = float(result.get('nsfw_score', 0.0))
        is_erotic = bool(result.get('is_erotic', False))
        confidence = float(result.get('confidence', 0.0))
        face_count = int(result.get('face_count', 0))
        phash = result.get('phash', '')
        
        # Определяем категорию на основе всех доступных данных
        is_nsfw = nsfw_score > 0.5 or is_erotic
        
        # Если есть детали от OpenNSFW2, учитываем их
        clip_nude_score = 0.0
        if 'details' in result and 'opennsfw2_analysis' in result['details']:
            clip_nude_score = float(result['details']['opennsfw2_analysis'].get('nsfw_score', 0.0))
        
        # Формируем итоговый результат
        final_result = {
            'is_nsfw': is_nsfw,
            'nsfw_score': nsfw_score,
            'clip_nude_score': clip_nude_score,
            'face_count': face_count,
            'confidence': confidence,
            'shooting_date': shooting_date,
            'modification_date': modification_date,
            'phash': phash
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке изображения: {str(e)}")
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
    Обрабатывает все изображения в директории последовательно
    
    Args:
        directory_path: путь к директории с изображениями
    """
    try:
        # Подключаемся к БД
        conn = connect_db()
        if not conn:
            return
            
        # Создаем таблицу если нужно
        ensure_table_schema(conn)
        
        # Получаем список всех jpg файлов
        image_paths = list(find_all_jpgs(directory_path))
        total_images = len(image_paths)
        
        if total_images == 0:
            logger.info("❌ Изображения не найдены")
            return
            
        logger.info(f"📸 Найдено {total_images} изображений")
        
        # Получаем список уже обработанных изображений
        cursor = conn.cursor()
        cursor.execute(f"SELECT path FROM {TABLE_NAME}")
        processed_paths = {row[0] for row in cursor.fetchall()}
        
        # Счетчики для статистики
        skipped_count = 0
        processed_count = 0
        
        # Обрабатываем изображения последовательно
        with tqdm(total=total_images, desc="Обработка изображений") as pbar:
            for path in image_paths:
                try:
                    # Проверяем, есть ли уже это изображение в базе
                    if path in processed_paths:
                        skipped_count += 1
                        pbar.update(1)
                        continue
                        
                    result = process_image(path)
                    if result:
                        # Безопасно получаем значения из результата
                        is_nsfw = result.get('is_nsfw', False)
                        nsfw_score = result.get('nsfw_score', 0.0)
                        face_count = result.get('face_count', 0)
                        clip_nude_score = result.get('clip_nude_score', 0.0)
                        shooting_date = result.get('shooting_date', '')
                        modification_date = result.get('modification_date', '')
                        phash = result.get('phash', '')
                        
                        # Сохраняем результат в БД
                        cursor = conn.cursor()
                        cursor.execute(f"""
                            INSERT OR REPLACE INTO {TABLE_NAME} 
                            (path, is_nude, has_face, hash_sha256, clip_nude_score, nsfw_score, is_small, status, shooting_date, modification_date, phash)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            path,
                            int(is_nsfw),
                            int(face_count > 0),
                            compute_sha256(path),
                            clip_nude_score,
                            nsfw_score,
                            is_image_small(path),
                            'review',
                            shooting_date,
                            modification_date,
                            phash
                        ))
                        conn.commit()
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке {path}: {str(e)}")
                    
                pbar.update(1)
                
        logger.info(f"✅ Обработка завершена:")
        logger.info(f"   - Пропущено (уже в базе): {skipped_count}")
        logger.info(f"   - Обработано новых: {processed_count}")
        logger.info(f"   - Всего: {total_images}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке директории: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    # Создаем директорию для логов если её нет
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    # Формируем имя файла лога с текущей датой
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIR, f'detect_nude_{current_date}.log')
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Для вывода в консоль
        ]
    )
    
    logger.info(f"🔄 Начало обработки. Логи сохраняются в {log_file}")
    
    try:
        # Обрабатываем директорию
        process_directory(PHOTO_DIR)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
    finally:
        # Очищаем ресурсы при завершении
        global nsfw_detector, opennsfw2_detector, face_detector
        del nsfw_detector
        del opennsfw2_detector
        del face_detector
        gc.collect()
        tf.keras.backend.clear_session()

if __name__ == "__main__":
    main()
