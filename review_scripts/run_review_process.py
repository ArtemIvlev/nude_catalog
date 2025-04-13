#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import subprocess
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Пути к скриптам
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SELECT_SCRIPT = os.path.join(SCRIPT_DIR, "select_for_review.py")
UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, "update_approved_status.py")

def run_script(script_path, description):
    """
    Запускает скрипт и обрабатывает результат
    
    Args:
        script_path: путь к скрипту
        description: описание скрипта
        
    Returns:
        bool: True, если скрипт выполнен успешно, иначе False
    """
    try:
        logger.info(f"🔄 Запуск скрипта: {description}")
        
        # Запускаем скрипт
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Выводим результат
        logger.info(f"✅ Скрипт выполнен успешно: {description}")
        if result.stdout:
            logger.info(f"Вывод скрипта:\n{result.stdout}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Ошибка при выполнении скрипта {description}: {e}")
        if e.stdout:
            logger.error(f"Вывод скрипта:\n{e.stdout}")
        if e.stderr:
            logger.error(f"Ошибка скрипта:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при выполнении скрипта {description}: {e}")
        return False

def main():
    try:
        # Проверяем существование скриптов
        if not os.path.exists(SELECT_SCRIPT):
            logger.error(f"❌ Скрипт не найден: {SELECT_SCRIPT}")
            return
            
        if not os.path.exists(UPDATE_SCRIPT):
            logger.error(f"❌ Скрипт не найден: {UPDATE_SCRIPT}")
            return
            
        # Запускаем скрипт выбора фото для ревью
        select_success = run_script(SELECT_SCRIPT, "Выбор фото для ревью")
        
        # Запускаем скрипт обновления статуса
        update_success = run_script(UPDATE_SCRIPT, "Обновление статуса одобренных фото")
        
        # Выводим итоговый результат
        if select_success and update_success:
            logger.info("✅ Все скрипты выполнены успешно")
        else:
            logger.warning("⚠️ Некоторые скрипты завершились с ошибками")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    main() 