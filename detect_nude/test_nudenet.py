import cv2
import numpy as np
import logging
import sys
from nsfw_detector import NudeNetDetector

# Массив с путями к тестовым файлам
TEST_FILES = [
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Василиса Аникина/_DSC9336.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9610.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9632.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9600.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9617.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9580.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9583.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9626.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9615.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9667.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9594.jpg",
    "/mnt/smb/OneDrive/Pictures/!Фотосессии/Ксю (@ksu_oh)/Домашка2_Кухня/_DSC9652.jpg"
]

logger = logging.getLogger(__name__)

def print_result(result):
    """Вывод результатов анализа в консоль"""
    if result:
        print(f"\nРезультаты анализа:")
        print(f"Путь к изображению: {result['image_path']}")
        print(f"Размеры: {result['dimensions']['width']}x{result['dimensions']['height']}")
        print(f"Количество каналов: {result['dimensions']['channels']}")
        print(f"Модель: {result['nsfw_analysis'].get('model', 'Неизвестно')}")
        print(f"NSFW анализ: {'NSFW' if result['nsfw_analysis']['is_nsfw'] else 'Безопасное'}")
        print(f"NSFW оценка: {result['nsfw_analysis']['nsfw_score']:.4f}")
        print(f"Безопасная оценка: {result['nsfw_analysis']['safe_score']:.4f}")
        print(f"Уверенность: {result['nsfw_analysis']['confidence']:.4f}")
        print("Детали:")
        for class_name, score in result['nsfw_analysis']['details'].items():
            print(f"  {class_name}: {score:.4f}")
    else:
        print("Не удалось проанализировать изображение")

def analyze_photo(image_path):
    """Анализ изображения и получение базовых данных о нем"""
    try:
        # Загружаем изображение
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"❌ Не удалось загрузить изображение: {image_path}")
            return None
            
        # Получаем базовые данные об изображении
        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        
        # Инициализируем детектор NSFW
        nsfw_detector = NudeNetDetector()
        
        # Анализируем изображение на наличие NSFW контента
        nsfw_result = nsfw_detector.analyze_image(image_path)
        
        # Формируем результат
        result = {
            'image_path': image_path,
            'dimensions': {
                'width': width,
                'height': height,
                'channels': channels
            },
            'nsfw_analysis': nsfw_result
        }
        
        logger.info(f"✅ Изображение успешно проанализировано: {width}x{height}, {channels} каналов")
        logger.info(f"NSFW анализ: {'NSFW' if result['nsfw_analysis']['is_nsfw'] else 'Безопасное'}, "
                   f"уверенность: {result['nsfw_analysis']['confidence']:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения: {str(e)}")
        return None

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Проверяем, передан ли путь к файлу как аргумент
    if len(sys.argv) > 1:
        # Если путь передан как аргумент, используем его
        image_path = sys.argv[1]
        result = analyze_photo(image_path)
        print_result(result)
    else:
        # Иначе используем файлы из массива TEST_FILES
        print("Путь к файлу не указан. Используются тестовые файлы из массива TEST_FILES:")
        for i, image_path in enumerate(TEST_FILES, 1):
            print(f"\nТест #{i}: {image_path}")
            result = analyze_photo(image_path)
            print_result(result) 