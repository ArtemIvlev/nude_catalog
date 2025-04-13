#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import logging
import re
from datetime import datetime
from tqdm import tqdm

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DB", "database.db"))
TABLE_NAME = "photos_ok"
APPROVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "approved_photos")

def connect_db():
    """Подключение к базе данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None

def ensure_directories():
    """Создание необходимых директорий, если они не существуют"""
    os.makedirs(APPROVED_DIR, exist_ok=True)
    logger.info(f"✅ Директория создана: {APPROVED_DIR}")

def extract_hash_from_filename(filename):
    """
    Извлекает хеш SHA-256 из имени файла
    
    Args:
        filename: имя файла
        
    Returns:
        str: хеш SHA-256 или None, если не удалось извлечь
    """
    try:
        # Ищем хеш в имени файла (формат: _DSCXXXX-Edit_хеш_phash.jpg или _DSCXXXX-2_хеш_phash.jpg или Studio Session-XXX_хеш_phash.jpg)
        match = re.search(r'[^_]_([a-f0-9]{64})_[a-f0-9]+\.jpg$', filename)
        if match:
            return match.group(1)
    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении хеша из имени файла {filename}: {str(e)}")
    return None

def update_approved_status():
    """
    Обновляет статус фото, которые найдены в папке approved
    """
    try:
        # Подключаемся к БД
        conn = connect_db()
        if not conn:
            return
            
        # Создаем директорию если нужно
        ensure_directories()
        
        # Проверяем существование директории
        if not os.path.exists(APPROVED_DIR):
            logger.error(f"❌ Директория {APPROVED_DIR} не существует")
            return
            
        # Получаем список всех файлов в директории approved
        files = os.listdir(APPROVED_DIR)
        image_files = [f for f in files if f.endswith('.jpg')]
        
        if not image_files:
            logger.info("❌ Нет изображений в директории approved")
            return
            
        logger.info(f"📸 Найдено {len(image_files)} изображений")
        
        # Обновляем статус фото
        cursor = conn.cursor()
        updated_count = 0
        
        with tqdm(total=len(image_files), desc="Обновление статуса") as pbar:
            for image_file in image_files:
                try:
                    # Извлекаем хеш из имени файла
                    hash_sha256 = extract_hash_from_filename(image_file)
                    
                    if hash_sha256:
                        # Обновляем статус в БД по хешу
                        cursor.execute(f"""
                            UPDATE {TABLE_NAME}
                            SET status = 'approved'
                            WHERE hash_sha256 = ?
                        """, (hash_sha256,))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                            logger.info(f"✅ Обновлен статус для хеша: {hash_sha256}")
                        else:
                            logger.warning(f"⚠️ Не найден хеш в БД: {hash_sha256}")
                    else:
                        logger.warning(f"⚠️ Не удалось извлечь хеш из имени файла: {image_file}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке {image_file}: {str(e)}")
                finally:
                    pbar.update(1)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Обновлено {updated_count} записей")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        if conn:
            conn.close()

def main():
    try:
        update_approved_status()
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    main() 