#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import shutil
import logging
from datetime import datetime
from tqdm import tqdm
import imagehash
from PIL import Image

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
REVIEW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "review_photos")
APPROVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "approved_photos")
DUPLICATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "duplicate_photos")

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
    os.makedirs(REVIEW_DIR, exist_ok=True)
    os.makedirs(APPROVED_DIR, exist_ok=True)
    os.makedirs(DUPLICATES_DIR, exist_ok=True)
    logger.info(f"✅ Директории созданы: {REVIEW_DIR}, {APPROVED_DIR}, {DUPLICATES_DIR}")

def hamming_distance(hash1, hash2):
    """Вычисляет расстояние Хэмминга между двумя хешами"""
    if not hash1 or not hash2:
        return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

def is_similar(hash1, hash2, threshold=5):
    """Проверяет, являются ли два хеша похожими"""
    return hamming_distance(hash1, hash2) <= threshold

def select_photos_for_review():
    """
    Выбирает фото с метками нюд и без лица со статусом review
    и копирует их в папку на ревью, похожие фото копирует в папку дублей
    """
    try:
        # Подключаемся к БД
        conn = connect_db()
        if not conn:
            return
            
        # Создаем директории если нужно
        ensure_directories()
        
        # Выбираем фото для ревью
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT path, is_nude, has_face, nsfw_score, clip_nude_score, hash_sha256, phash
            FROM {TABLE_NAME}
            WHERE is_nude = 1 AND has_face = 0 AND status = 'review'
            ORDER BY nsfw_score DESC
        """)
        
        photos = cursor.fetchall()
        total_photos = len(photos)
        
        if total_photos == 0:
            logger.info("❌ Нет фото для ревью")
            return
            
        logger.info(f"📸 Найдено {total_photos} фото для ревью")
        
        # Копируем фото в директорию для ревью
        copied_count = 0
        skipped_count = 0
        duplicate_count = 0
        
        # Словарь для отслеживания уже обработанных хешей
        processed_hashes = {}
        
        with tqdm(total=total_photos, desc="Обработка фото") as pbar:
            for photo in photos:
                path, is_nude, has_face, nsfw_score, clip_nude_score, hash_sha256, phash = photo
                
                try:
                    # Получаем имя файла
                    filename = os.path.basename(path)
                    
                    # Проверяем, является ли фото дубликатом
                    is_duplicate = False
                    for processed_phash in processed_hashes:
                        if is_similar(phash, processed_phash):
                            is_duplicate = True
                            break
                    
                    # Создаем новое имя файла с хешем и phash
                    new_filename = f"{os.path.splitext(filename)[0]}_{hash_sha256}_{phash}.jpg"
                    
                    if is_duplicate:
                        # Копируем в папку дублей
                        new_path = os.path.join(DUPLICATES_DIR, new_filename)
                        if not os.path.exists(new_path):
                            shutil.copy2(path, new_path)
                            duplicate_count += 1
                    else:
                        # Копируем в папку для ревью
                        new_path = os.path.join(REVIEW_DIR, new_filename)
                        if not os.path.exists(new_path):
                            shutil.copy2(path, new_path)
                            copied_count += 1
                            # Добавляем хеш в обработанные
                            processed_hashes[phash] = True
                        else:
                            skipped_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка при копировании {path}: {str(e)}")
                finally:
                    pbar.update(1)
        
        conn.close()
        logger.info(f"✅ Скопировано: {copied_count}, дублей: {duplicate_count}, пропущено: {skipped_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        if conn:
            conn.close()

def main():
    try:
        select_photos_for_review()
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    main() 