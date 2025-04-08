import sqlite3
import logging
from pathlib import Path
import imagehash
from PIL import Image
from tqdm import tqdm
import sys
import cv2
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_most_similar(phash, db_photos, min_similarity=0.90):
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
        #diff = sum(c1 != c2 for c1, c2 in zip(phash, db_phash))
        
        diff = phash - db_phash
        similarity = 1 - (diff / 64.0)  # 64 - максимально возможная разница
        
        if similarity > best_similarity and similarity >= min_similarity:
            best_similarity = similarity
            best_match = db_photo
            
    if best_match:
        return best_match['path'], best_similarity
    return None, 0

def find_similar_with_lower_threshold(phash, db_photos, min_similarity=0.80):
    """
    Находит похожие фотографии с пониженным порогом схожести
    Возвращает список кортежей (путь, процент схожести)
    """
    similar_photos = []
    
    for db_photo in db_photos:
        db_phash = db_photo.get('phash')
        if not db_phash:
            continue
            
        try:
            # Проверяем тип входного phash
            if isinstance(phash, str):
                # Если phash - строка, конвертируем оба хеша в числа
                phash_int = int(phash, 16)
                db_phash_int = int(db_phash, 16)
                # Вычисляем разницу используя побитовое XOR
                diff = bin(phash_int ^ db_phash_int).count('1')
            else:
                # Если phash - объект ImageHash, используем встроенный метод сравнения
                diff = phash - db_phash
            
            # Вычисляем схожесть в процентах
            similarity = (1 - diff / 64.0) * 100
            
            # Проверяем размеры изображений если они доступны
            if 'width' in db_photo and 'height' in db_photo:
                try:
                    img = Image.open(db_photo['path'])
                    width, height = img.size
                    size_ratio = min(width, height) / max(width, height)
                    
                    # Если соотношение сторон сильно отличается, снижаем схожесть
                    if size_ratio < 0.7:  # Если одно изображение значительно шире/выше другого
                        similarity *= 0.8
                except Exception as e:
                    logger.warning(f"Не удалось проверить размеры изображения {db_photo['path']}: {e}")
            
            if similarity >= min_similarity * 100:  # Конвертируем порог в проценты
                similar_photos.append((db_photo['path'], similarity))
                
        except Exception as e:
            logger.error(f"Ошибка при сравнении хешей: {e}")
            continue
    
    return sorted(similar_photos, key=lambda x: x[1], reverse=True)

def compare_images_sift(img1_path, img2_path, min_matches=10):
    """
    Сравнивает два изображения используя SIFT
    Возвращает True если изображения совпадают
    """
    print(f"Сравниваем {img1_path} и {img2_path}")
    try:
        # Загружаем изображения
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            return False
            
        # Конвертируем в градации серого
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Инициализируем SIFT
        sift = cv2.SIFT_create()
        
        # Находим ключевые точки и дескрипторы
        kp1, des1 = sift.detectAndCompute(gray1, None)
        kp2, des2 = sift.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None:
            return False
            
        # Создаем matcher
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        
        # Применяем ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        return len(good_matches) >= min_matches
        
    except Exception as e:
        logger.error(f"Ошибка при SIFT сравнении {img1_path} и {img2_path}: {e}")
        return False

def compare_phash():
    """Сравнивает pHash фотографий из телеграм канала с pHash фотографий в основной базе данных"""
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect('database.db')
        main_cur = main_conn.cursor()
        
        telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
        telegram_cur = telegram_conn.cursor()
        
        # Добавляем поле processed, если его нет
        try:
            telegram_cur.execute("""
                ALTER TABLE published_photos 
                ADD COLUMN processed INTEGER DEFAULT 0
            """)
            telegram_conn.commit()
            logger.info("Добавлено поле processed в таблицу published_photos")
        except sqlite3.OperationalError:
            logger.info("Поле processed уже существует")
        
        # Получаем все фотографии из телеграм канала
        telegram_cur.execute("""
            SELECT p.message_id, p.file_path, h.phash
            FROM published_photos p
            LEFT JOIN photo_hashes h ON p.message_id = h.message_id
            WHERE p.file_path IS NOT NULL AND p.processed = 0
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
        
        # Пороги схожести для разных этапов
        strict_threshold = 0.90  # Строгий порог для точных совпадений
        loose_threshold = 0.80   # Ослабленный порог для поиска похожих
        
        # Списки для отслеживания совпадений по этапам
        exact_matches = []  # Совпадения на первом этапе (строгое сравнение по pHash)
        sift_matches = []   # Совпадения на третьем этапе (после SIFT сравнения)
        
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
            
            # Этап 1: Строгое сравнение по pHash
            found_match = False
            
            if phash in phash_dict:
                # Обновляем статус для всех фотографий с этим хешем
                for photo_path in phash_dict[phash]:
                    main_cur.execute("""
                        UPDATE photos_ok 
                        SET status = 'published', message_id = ?
                        WHERE path = ?
                    """, (message_id, photo_path))
                    if main_cur.rowcount > 0:
                        updated_count += 1
                
                matches.append((file_path, phash_dict[phash]))
                exact_matches.append((file_path, phash_dict[phash]))
                found_match = True
            else:
                # Этап 2: Поиск похожих с пониженным порогом
                similar_photos = find_similar_with_lower_threshold(
                    phash, 
                    [{'path': p, 'phash': h} for p, h in main_photos],
                    min_similarity=loose_threshold
                )
                
                # Сортируем похожие фотографии по схожести (от большей к меньшей)
                similar_photos.sort(key=lambda x: x[1], reverse=True)
                
                # Выводим количество похожих фотографий
                logger.info(f"Найдено {len(similar_photos)} похожих фотографий для {file_path}")
                
                # Берем только первые 10 самых похожих фотографий
                similar_photos = similar_photos[:10]
                
                # Этап 3: Строгое сравнение с помощью SIFT только для фотографий с схожестью выше порога
                if similar_photos:
                    telegram_path = f"../telegram_bot/{file_path}"
                    
                    # Фильтруем фотографии с схожестью выше порога
                    high_similarity_photos = [p for p in similar_photos if p[1] >= loose_threshold]
                    
                    logger.info(f"Из них {len(high_similarity_photos)} имеют схожесть выше {loose_threshold*100}%")
                    
                    for similar_path, similarity in high_similarity_photos:
                        if compare_images_sift(telegram_path, similar_path):
                            # Обновляем статус для найденной фотографии
                            main_cur.execute("""
                                UPDATE photos_ok 
                                SET status = 'published', message_id = ?
                                WHERE path = ?
                            """, (message_id, similar_path))
                            
                            # Отмечаем фото как обработанное
                            telegram_cur.execute("""
                                UPDATE published_photos 
                                SET processed = 1
                                WHERE message_id = ?
                            """, (message_id,))
                            
                            if main_cur.rowcount > 0:
                                updated_count += 1
                            
                            matches.append((file_path, [similar_path]))
                            sift_matches.append((file_path, [similar_path]))
                            found_match = True
                            break
            
            if not found_match:
                no_matches.append((file_path, phash))
            
            # Обновляем статус processed для всех проверенных фотографий
            telegram_cur.execute("""
                UPDATE published_photos 
                SET processed = 1
                WHERE message_id = ?
            """, (message_id,))
        
        # Сохраняем изменения в базах данных
        main_conn.commit()
        telegram_conn.commit()
        
        # Выводим результаты
        logger.info(f"\nРезультаты сравнения:")
        logger.info(f"Всего фотографий в телеграм канале: {len(telegram_photos)}")
        logger.info(f"Найдено совпадений: {len(matches)}")
        logger.info(f"  - Точные совпадения по pHash: {len(exact_matches)}")
        logger.info(f"  - Совпадения после SIFT сравнения: {len(sift_matches)}")
        logger.info(f"Не найдено совпадений: {len(no_matches)}")
        logger.info(f"Обновлено записей: {updated_count}")
        
        if matches:
            logger.info("\nСовпадения:")
            logger.info("\nТочные совпадения по pHash:")
            for file_path, matches_paths in exact_matches:
                logger.info(f"  - {file_path} -> {matches_paths}")
                
            logger.info("\nСовпадения после SIFT сравнения:")
            for file_path, matches_paths in sift_matches:
                logger.info(f"  - {file_path} -> {matches_paths}")
                
        if no_matches:
            logger.info("\nФотографии без совпадений:")
            for file_path, phash in no_matches:
                logger.info(f"  - {file_path}")
        
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