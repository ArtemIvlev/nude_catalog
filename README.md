# Nude Catalog

Система для управления каталогом фотографий с автоматической классификацией и публикацией.

## Основные компоненты

- `add_phash.py` - добавление pHash для фотографий
- `predict_preferences.py` - предсказание предпочтений для фотографий
- `stats/` - скрипты для анализа и синхронизации статистики
  - `compare_phash.py` - сравнение хешей между базами данных
  - `analyze_published_delta.py` - анализ разницы между опубликованными фото
  - `sync_published_status.py` - синхронизация статусов публикации

## Базы данных

- `database.db` - основная база данных с фотографиями
- `../telegram_bot/published_photos.sqlite` - база данных опубликованных фото в Telegram

## Зависимости

Основные зависимости указаны в `requirements.txt`:
- SQLite3
- Python 3.x
- Pillow
- imagehash
- numpy
- pandas 