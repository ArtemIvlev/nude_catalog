import sqlite3
import logging
from pathlib import Path
import imagehash
from PIL import Image
from tqdm import tqdm
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_most_similar(phash, db_photos, min_similarity=0.5):
    """
    Находит максимально похожую фотографию из базы данных
    Возвращает кортеж (путь, процент схожести)
    """
    best_match = None
    best_similarity = 0
    
    for db_photo in db_photos:
        db_phash = db_photo.get('phash')
        if not db_phash:
            continue
            
        # Вычисляем разницу между хешами
        diff = sum(c1 != c2 for c1, c2 in zip(phash, db_phash))
        similarity = 1 - (diff / 64.0)  # 64 - максимально возможная разница
        
        if similarity > best_similarity and similarity >= min_similarity:
            best_similarity = similarity
            best_match = db_photo
            
    if best_match:
        return best_match['path'], best_similarity
    return None, 0

def compare_phash():
    """Сравнивает pHash фотографий из телеграм канала с pHash фотографий в основной базе данных"""
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect('database.db')
        main_cur = main_conn.cursor()
        
        telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
        telegram_cur = telegram_conn.cursor()
        
        # Получаем все фотографии из телеграм канала
        telegram_cur.execute("""
            SELECT p.message_id, p.file_path, h.phash
            FROM published_photos p
            LEFT JOIN photo_hashes h ON p.message_id = h.message_id
            WHERE p.file_path IS NOT NULL
        """)
        
        telegram_photos = telegram_cur.fetchall()
        logger.info(f"Найдено {len(telegram_photos)} фотографий в телеграм канале")
        
        # Получаем все фотографии из основной базы данных
        main_cur.execute("""
            SELECT path, phash
            FROM photos_ok
            WHERE phash IS NOT NULL
        """)
        
        main_photos = main_cur.fetchall()
        logger.info(f"Найдено {len(main_photos)} фотографий в основной базе данных")
        
        # Создаем словарь для быстрого поиска по pHash
        phash_dict = {}
        for path, phash in main_photos:
            if phash not in phash_dict:
                phash_dict[phash] = []
            phash_dict[phash].append(path)
        
        # Сравниваем pHash
        matches = []
        no_matches = []
        updated_count = 0
        
        # Порог схожести для определения совпадений
        similarity_threshold = 0.83 
        
        for message_id, file_path, phash in tqdm(telegram_photos, desc="Сравнение pHash"):
            if not phash:
                # Если pHash не вычислен, вычисляем его
                try:
                    image = Image.open(f"../telegram_bot/{file_path}")
                    phash = str(imagehash.average_hash(image))
                    
                    # Сохраняем pHash в базу данных телеграм бота
                    telegram_cur.execute("""
                        INSERT OR REPLACE INTO photo_hashes (message_id, phash)
                        VALUES (?, ?)
                    """, (message_id, phash))
                except Exception as e:
                    logger.error(f"Ошибка при вычислении pHash для {file_path}: {e}")
                    continue
            
            # Ищем совпадения с учетом порога схожести
            found_match = False
            
            # Сначала проверяем точное совпадение
            if phash in phash_dict:
                # Обновляем статус для всех фотографий с этим хешем
                for photo_path in phash_dict[phash]:
                    main_cur.execute("""
                        UPDATE photos_ok 
                        SET status = 'published'
                        WHERE path = ?
                    """, (photo_path,))
                    if main_cur.rowcount > 0:
                        updated_count += 1
                
                matches.append((file_path, phash_dict[phash]))
                found_match = True
            else:
                # Если точного совпадения нет, ищем максимально похожую фотографию
                most_similar_path, similarity = find_most_similar(phash, [{'path': p, 'phash': h} for p, h in main_photos])
                
                if most_similar_path and similarity >= similarity_threshold:
                    # Обновляем статус для найденной похожей фотографии
                    main_cur.execute("""
                        UPDATE photos_ok 
                        SET status = 'published'
                        WHERE path = ?
                    """, (most_similar_path,))
                    if main_cur.rowcount > 0:
                        updated_count += 1
                    
                    # Нашли достаточно похожую фотографию
                    matches.append((file_path, [most_similar_path]))
                    found_match = True
            
            if not found_match:
                no_matches.append((file_path, phash))
        
        # Сохраняем изменения в базах данных
        main_conn.commit()
        telegram_conn.commit()
        
        # Выводим результаты
        logger.info(f"\nРезультаты сравнения:")
        logger.info(f"Всего фотографий в телеграм канале: {len(telegram_photos)}")
        logger.info(f"Найдено совпадений: {len(matches)}")
        logger.info(f"Не найдено совпадений: {len(no_matches)}")
        logger.info(f"Обновлено записей: {updated_count}")
        
        if matches:
            logger.info("\nСовпадения:")
            for file_path, matches_paths in matches:
                logger.info(f"  - {file_path} -> {matches_paths}")
                
        if no_matches:
            logger.info("\nФотографии без совпадений (с максимально похожими):")
            for file_path, phash in no_matches:
                # Ищем максимально похожую фотографию
                most_similar_path, similarity = find_most_similar(phash, [{'path': p, 'phash': h} for p, h in main_photos])
                if most_similar_path:
                    logger.info(f"  - {file_path}")
                    logger.info(f"    Наиболее похожая: {most_similar_path} (схожесть: {similarity:.2%})")
                else:
                    logger.info(f"  - {file_path}")
                    logger.info(f"    Нет достаточно похожих фотографий (максимальная схожесть < 50%)")
        
        # Закрываем соединения
        main_conn.close()
        telegram_conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при сравнении pHash: {e}")
        raise

def calculate_phash(image_path):
    try:
        img = Image.open(image_path)
        phash = imagehash.average_hash(img)
        return str(phash)
    except Exception as e:
        print(f"Ошибка при обработке {image_path}: {e}")
        return None

def find_matches(telegram_photos, db_photos, similarity_threshold=0.75):
    """
    Находит совпадения между фотографиями из Telegram и базы данных
    на основе pHash с учетом порога схожести
    """
    matches = {}
    no_matches = []
    
    for t_photo in telegram_photos:
        t_phash = t_photo.get('phash')
        if not t_phash:
            continue
            
        best_match = None
        best_similarity = 0
        
        for db_photo in db_photos:
            db_phash = db_photo.get('phash')
            if not db_phash:
                continue
                
            # Вычисляем разницу между хешами
            diff = sum(c1 != c2 for c1, c2 in zip(t_phash, db_phash))
            similarity = 1 - (diff / 64.0)  # 64 - максимально возможная разница
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = db_photo
                
        if best_match and best_similarity >= similarity_threshold:
            if t_photo['file_path'] not in matches:
                matches[t_photo['file_path']] = []
            matches[t_photo['file_path']].append(best_match['path'])
        else:
            no_matches.append(t_photo['file_path'])
            
    return matches, no_matches

if __name__ == "__main__":
    compare_phash() 