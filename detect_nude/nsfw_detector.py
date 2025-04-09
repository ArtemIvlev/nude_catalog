import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import numpy as np
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class NSFWDetector(ABC):
    """Базовый класс для детекторов NSFW контента"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название модели"""
        pass
    
    @abstractmethod
    def analyze_image(self, image_path: str) -> dict:
        """
        Анализ изображения на наличие NSFW контента
        
        Args:
            image_path: путь к изображению
            
        Returns:
            dict: словарь с результатами анализа
        """
        pass

class MarqoNSFWDetector(NSFWDetector):
    """Детектор NSFW контента на основе модели Marqo"""
    
    MODEL_NAME = "Marqo/nsfw-image-detection-384"
    
    def __init__(self):
        """Инициализация детектора"""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logging.info(f"Используется устройство: {self.device}")
            
            # Загружаем модель и процессор
            self.model = AutoModelForImageClassification.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True
            ).to(self.device)
            
            self.processor = AutoImageProcessor.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True
            )
            
            logging.info(f"✅ Модель {self.MODEL_NAME} успешно загружена")
            
        except Exception as e:
            logging.error(f"❌ Ошибка при инициализации MarqoNSFWDetector: {str(e)}")
            raise
    
    @property
    def name(self) -> str:
        return self.MODEL_NAME
    
    def analyze_image(self, image_path: str) -> dict:
        """
        Анализ изображения на наличие NSFW контента
        
        Args:
            image_path: путь к изображению
            
        Returns:
            dict: словарь с результатами анализа
        """
        try:
            # Загрузка изображения
            image = Image.open(image_path).convert("RGB")
            
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
            
            # Определяем, является ли изображение NSFW
            is_nsfw = False
            nsfw_score = 0.0
            safe_score = 0.0
            
            # Проверяем классы, которые могут указывать на NSFW контент
            nsfw_classes = ['nsfw', 'porn', 'sexy', 'hentai']
            safe_classes = ['normal', 'safe', 'neutral', 'sfw']
            
            for label, score in results.items():
                if any(nsfw_term in label.lower() for nsfw_term in nsfw_classes):
                    nsfw_score += score
                elif any(safe_term in label.lower() for safe_term in safe_classes):
                    safe_score += score
            
            # Если у нас есть только два класса (NSFW и SFW), используем их напрямую
            if len(results) == 2 and 'nsfw' in results and 'sfw' in results:
                nsfw_score = results['nsfw']
                safe_score = results['sfw']
            
            # Определяем, является ли изображение NSFW
            is_nsfw = nsfw_score > 0.5
            
            return {
                'is_nsfw': is_nsfw,
                'nsfw_score': nsfw_score,
                'safe_score': safe_score,
                'confidence': max_prob,
                'details': results,
                'model': self.name
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе изображения: {str(e)}")
            return {
                'is_nsfw': False,
                'nsfw_score': 0.0,
                'safe_score': 0.0,
                'confidence': 0.0,
                'details': {},
                'error': str(e),
                'model': self.name
            }

class NudeNetDetector(NSFWDetector):
    """Детектор NSFW на основе модели NudeNet"""
    
    MODEL_NAME = "nudenet"
    
    def __init__(self):
        try:
            from nudenet import NudeDetector
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Используется устройство: {self.device}")
            
            # Загрузка модели
            self.detector = NudeDetector()
            
            logger.info(f"✅ Модель {self.name} успешно загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации модели {self.name}: {str(e)}")
            raise
    
    @property
    def name(self) -> str:
        return self.MODEL_NAME
    
    def analyze_image(self, image_path: str) -> dict:
        """
        Анализ изображения на наличие NSFW контента
        
        Args:
            image_path: путь к изображению
            
        Returns:
            dict: словарь с результатами анализа
        """
        try:
            # Анализ изображения
            detections = self.detector.detect(image_path)
            
            # Формируем результаты
            results = {}
            max_prob = 0
            max_label = None
            
            logger.info("🧠 NSFW классификация:")
            for detection in detections:
                label = detection['class']
                prob_value = float(detection['score'])
                results[label] = prob_value
                logger.info(f"{label:<10}: {prob_value:.3f}")
                
                if prob_value > max_prob:
                    max_prob = prob_value
                    max_label = label
            
            # Определяем, является ли изображение NSFW
            is_nsfw = max_prob > 0.5
            
            return {
                'is_nsfw': is_nsfw,
                'nsfw_score': max_prob,
                'safe_score': 1 - max_prob,
                'confidence': max_prob,
                'details': results,
                'model': self.name
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе изображения: {str(e)}")
            return {
                'is_nsfw': False,
                'nsfw_score': 0.0,
                'safe_score': 0.0,
                'confidence': 0.0,
                'details': {},
                'error': str(e),
                'model': self.name
            } 