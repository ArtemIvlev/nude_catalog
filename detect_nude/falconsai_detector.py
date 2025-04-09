import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FalconsaiDetector:
    def __init__(self):
        """Инициализация детектора NSFW на основе модели Falconsai/nsfw_image_detection"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Используется устройство: {self.device}")
            
            # Загрузка модели и процессора
            self.processor = AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
            self.model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("✅ Модель Falconsai/nsfw_image_detection успешно загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации модели Falconsai/nsfw_image_detection: {str(e)}")
            raise
    def analyze_image(self, image_path):
        """
        Анализ изображения на наличие NSFW контента

        Args:
            image_path: путь к изображению

        Returns:
            dict: словарь с результатами анализа
        """
        logger.info(f"!!!!Анализ изображения: {image_path}")

        try:
            # Загрузка изображения
            image = Image.open(image_path).convert("RGB")

            # Предобработка
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Предсказание
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

            # Получение названий классов
            id2label = self.model.config.id2label
            results = {}

            max_prob = 0.0
            max_label = None

            logger.info("🧠 NSFW классификация:")
            for idx, prob in enumerate(probs):
                label = id2label[idx]
                prob_value = float(prob)
                results[label] = prob_value
                logger.info(f"{label:<10}: {prob_value:.3f}")

                if prob_value > max_prob:
                    max_prob = prob_value
                    max_label = label

            # Группировка по категориям
            nsfw_categories = ['porn', 'sexy', 'hentai']
            safe_categories = ['neutral', 'drawings']

            nsfw_score = sum(results.get(k, 0.0) for k in nsfw_categories)
            safe_score = sum(results.get(k, 0.0) for k in safe_categories)

            return {
                'is_nsfw': max_label in nsfw_categories,
                'nsfw_score': round(nsfw_score, 4),
                'safe_score': round(safe_score, 4),
                'confidence': round(max_prob, 4),
                'details': dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
            }

        except Exception as e:
            logger.error(f"❌ Ошибка при анализе изображения: {str(e)}")
            return {
                'is_nsfw': False,
                'nsfw_score': 0.0,
                'safe_score': 0.0,
                'confidence': 0.0,
                'details': {},
                'error': str(e)
            }

    def analyze_image_old(self, image_path):
        """
        Анализ изображения на наличие NSFW контента
        
        Args:
            image_path: путь к изображению
            
        Returns:
            dict: словарь с результатами анализа
        """
        try:
            # Загрузка изображения
            image = Image.open(image_path)
            
            # Предобработка изображения
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Предсказание
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

            # Получаем названия классов
            id2label = self.model.config.id2label
            
            # Формируем результаты
            results = {}
            max_prob = 0
            max_label = None
            
            logger.info("🧠 NSFW классификация:")
            for idx, prob in enumerate(probs):
                label = id2label[idx]
                prob_value = float(prob)
                results[label] = prob_value
                logger.info(f"{label:<10}: {prob_value:.3f}")
                
                if prob_value > max_prob:
                    max_prob = prob_value
                    max_label = label
            

            return {
                'is_nsfw': max_label in ['porn', 'sexy', 'hentai'],
                'nsfw_score': float(results.get('nsfw', 0.0)),
                'safe_score': float(results.get('normal', 0.0)),
                'confidence': float(max_prob),
                'details': results
            }

            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе изображения: {str(e)}")
            return {
                'is_nsfw': False,
                'nsfw_score': 0.0,
                'safe_score': 0.0,
                'confidence': 0.0,
                'details': {},
                'error': str(e)
            } 