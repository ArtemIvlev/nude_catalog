import os
import sys

# Добавляем путь к корневой директории nude_catalog
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Импортируем все из основного конфига
from config import * 