import os
import cv2
import logging
import argparse
from detect_nude.face_detector import FaceDetector

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def test_face_detection(image_path):
    """
    Тестирует обнаружение лиц на изображении
    
    Args:
        image_path: путь к изображению
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(image_path):
            logger.error(f"❌ Файл не существует: {image_path}")
            return False
            
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"❌ Не удалось загрузить изображение: {image_path}")
            return False
            
        # Получаем размеры изображения
        height, width = image.shape[:2]
        logger.info(f"📏 Размеры изображения: {width}x{height}")
        
        # Создаем детектор лиц
        face_detector = FaceDetector()
        
        # Обнаруживаем лица
        result = face_detector.detect_faces(image)
        
        # Выводим результаты
        face_count = result.get('face_count', 0)
        face_locations = result.get('face_locations', [])
        face_angles = result.get('face_angles', [])
        
        logger.info(f"👥 Обнаружено лиц: {face_count}")
        
        if face_count > 0:
            logger.info("📍 Расположение лиц:")
            for i, (x, y, w, h) in enumerate(face_locations):
                logger.info(f"  Лицо {i+1}: x={x}, y={y}, ширина={w}, высота={h}")
                
            if face_angles:
                logger.info("🔄 Углы поворота лиц:")
                for i, angle in enumerate(face_angles):
                    logger.info(f"  Лицо {i+1}: {angle:.2f}°")
        
        # Визуализируем результаты
        for (x, y, w, h) in face_locations:
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
        # Сохраняем результат
        output_path = os.path.splitext(image_path)[0] + "_faces.jpg"
        cv2.imwrite(output_path, image)
        logger.info(f"💾 Результат сохранен: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {str(e)}")
        return False

def test_all_files():
    """
    Тестирует все файлы из массива TEST_FILES
    """
    total_files = len(TEST_FILES)
    success_count = 0
    
    logger.info(f"🔍 Начинаем тестирование {total_files} файлов")
    
    for i, file_path in enumerate(TEST_FILES, 1):
        logger.info(f"\n[{i}/{total_files}] Тестирование: {os.path.basename(file_path)}")
        if test_face_detection(file_path):
            success_count += 1
    
    logger.info(f"\n📊 Итоги тестирования:")
    logger.info(f"  - Всего файлов: {total_files}")
    logger.info(f"  - Успешно обработано: {success_count}")
    logger.info(f"  - Ошибок: {total_files - success_count}")

def main():
    parser = argparse.ArgumentParser(description="Тестирование обнаружения лиц")
    parser.add_argument("--image", help="Путь к изображению для тестирования")
    parser.add_argument("--all", action="store_true", help="Тестировать все файлы из массива TEST_FILES")
    args = parser.parse_args()
    
    if args.all:
        test_all_files()
    elif args.image:
        test_face_detection(args.image)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 