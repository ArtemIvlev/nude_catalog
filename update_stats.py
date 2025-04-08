import os
import sys
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'stats_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def run_script(script_name):
    """Запускает Python скрипт и логирует результат"""
    try:
        logger.info(f"Запуск {script_name}...")
        script_path = os.path.join('stats', script_name)
        if not os.path.exists(script_path):
            logger.error(f"Скрипт {script_path} не найден")
            return False
            
        # Добавляем текущую директорию в PYTHONPATH
        sys.path.insert(0, os.path.abspath('.'))
        
        # Импортируем и запускаем скрипт
        module_name = os.path.splitext(script_name)[0]
        module = __import__(f'stats.{module_name}', fromlist=['*'])
        
        # Ищем основную функцию в модуле
        main_func = None
        for name in dir(module):
            if name.endswith('_stats') or name == 'analyze_normalized' or name == 'check_statuses' or name == 'compare_phash' or name == 'compare_telegram_photos' or name == 'list_no_matches' or name == 'process_telegram_photos' or name == 'sync_published_status' or name == 'update_subscribers' or name == 'check_publication_dates' or name == 'find_worst_photos':
                main_func = getattr(module, name)
                break
                
        if main_func:
            if asyncio.iscoroutinefunction(main_func):
                await main_func()
            else:
                main_func()
            logger.info(f"{script_name} успешно выполнен")
            return True
        else:
            logger.error(f"Не найдена основная функция в {script_name}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при выполнении {script_name}: {e}")
        return False

async def update_all_stats():
    """Запускает все скрипты статистики в правильном порядке"""
    scripts = [
        # 1. Синхронизация фотографий с Telegram
        'process_telegram_photos.py',  # Обработка фотографий из Telegram
        'compare_telegram_photos.py',  # Сравнение фотографий в базе и директории
        'compare_phash.py',           # Сравнение pHash фотографий
        'list_no_matches.py',         # Список фотографий без совпадений
        
        # 2. Обновление данных из Telegram
        'update_channel_stats.py',    # Получение текущей статистики канала
        'update_subscribers.py',      # Обновление количества подписчиков
        
        # 3. Импорт и обработка данных
        'import_stats.py',            # Импорт статистики в основную базу
        
        # 4. Анализ данных
        'analyze_stats.py',           # Общий анализ статистики
        'analyze_normalized.py',      # Анализ нормализованной статистики
        'check_dates.py',             # Проверка дат публикации
        'check_status.py',            # Проверка статусов
        'find_worst_photos.py'        # Поиск худших фотографий
    ]
    
    results = {}
    for script in scripts:
        success = await run_script(script)
        results[script] = "Успешно" if success else "Ошибка"
    
    # Выводим итоговый отчет
    logger.info("\nИтоговый отчет:")
    for script, result in results.items():
        logger.info(f"{script}: {result}")

if __name__ == "__main__":
    asyncio.run(update_all_stats()) 