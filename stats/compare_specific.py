import cv2
import numpy as np
from PIL import Image
import imagehash
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compare_images_sift(img1_path, img2_path, min_matches=10):
    """
    Сравнивает два изображения используя SIFT
    Возвращает количество совпадений и процент схожести
    """
    logger.info(f"Сравниваем {img1_path} и {img2_path}")
    try:
        # Загружаем изображения
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            logger.error("Не удалось загрузить одно из изображений")
            return 0, 0
            
        # Конвертируем в градации серого
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Инициализируем SIFT
        sift = cv2.SIFT_create()
        
        # Находим ключевые точки и дескрипторы
        kp1, des1 = sift.detectAndCompute(gray1, None)
        kp2, des2 = sift.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None:
            logger.error("Не удалось найти ключевые точки")
            return 0, 0
            
        # Создаем matcher
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        
        # Применяем ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        # Вычисляем процент схожести
        similarity = len(good_matches) / min(len(kp1), len(kp2)) * 100 if min(len(kp1), len(kp2)) > 0 else 0
        
        return len(good_matches), similarity
        
    except Exception as e:
        logger.error(f"Ошибка при SIFT сравнении: {e}")
        return 0, 0

def get_phash(img_path):
    """
    Вычисляет pHash для изображения
    Возвращает pHash и его строковое представление
    """
    try:
        img = Image.open(img_path)
        phash = imagehash.average_hash(img)
        return phash, str(phash)
    except Exception as e:
        logger.error(f"Ошибка при вычислении pHash: {e}")
        return None, None

def compare_phash(img1_path, img2_path):
    """
    Сравнивает два изображения используя pHash
    Возвращает процент схожести
    """
    try:
        # Получаем pHash для обоих изображений
        phash1, phash1_str = get_phash(img1_path)
        phash2, phash2_str = get_phash(img2_path)
        
        if phash1 is None or phash2 is None:
            return 0
            
        # Выводим pHash значения
        logger.info(f"\npHash значения:")
        logger.info(f"Изображение 1: {phash1_str}")
        logger.info(f"Изображение 2: {phash2_str}")
        
        # Вычисляем разницу между хешами
        diff = phash1 - phash2
        similarity = (1 - diff / 64.0) * 100  # 64 - максимально возможная разница
        
        return similarity
        
    except Exception as e:
        logger.error(f"Ошибка при pHash сравнении: {e}")
        return 0
    


def compare_phash2(img1_path, img2_path):
    """
    Сравнивает два изображения используя pHash
    Возвращает процент схожести
    """
    try:
        # Получаем pHash для обоих изображений
        phash1, phash1_str = get_phash(img1_path)
        phash2, phash2_str = get_phash(img2_path)
        
        if phash1 is None or phash2 is None:
            return 0
            
        
        phash1_int = int(phash1_str, 16)
        phash2_int = int(phash2_str, 16)

        # Выводим pHash значения
        logger.info(f"\npHash значения:")
        logger.info(f"Изображение 1: {phash1_int}")
        logger.info(f"Изображение 2: {phash2_int}")


        # Вычисляем разницу между хешами
        diff = phash1_int - phash2_int
        similarity = (1 - diff / 64.0) * 100  # 64 - максимально возможная разница
        
        return similarity
        
    except Exception as e:
        logger.error(f"Ошибка при pHash сравнении: {e}")
        return 0


def main():
    # Пути к файлам
    telegram_path = "../telegram_bot/downloaded/msg_385.jpg"
    db_path = "/mnt/smb/OneDrive/Pictures/!Фотосессии/Алина Титова (@ApelsiN04KA)/_DSC4017.jpg"
    
    # Сравнение с помощью SIFT
    matches, sift_similarity = compare_images_sift(telegram_path, db_path)
    logger.info(f"\nРезультаты SIFT сравнения:")
    logger.info(f"Количество совпадений: {matches}")
    logger.info(f"Процент схожести: {sift_similarity:.2f}%")
    
    # Сравнение с помощью pHash
    phash_similarity = compare_phash(telegram_path, db_path)
    phash_similarity2 = compare_phash2(telegram_path, db_path)
    logger.info(f"\nРезультаты pHash сравнения:")
    logger.info(f"Процент схожести: {phash_similarity:.2f}%")
    logger.info(f"Процент схожести: {phash_similarity2:.2f}%")

if __name__ == "__main__":
    main() 