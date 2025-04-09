import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import numpy as np

class EroticDetector:
    def __init__(self):
        self.model_name = "Falconsai/nsfw_image_detection"
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
    def analyze_image(self, image_path):
        try:
            # Загрузка и предобработка изображения
            image = Image.open(image_path)
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Получение предсказаний
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                
            # Получение вероятностей для каждого класса
            probs = probabilities[0].cpu().numpy()
            nsfw_score = probs[1]  # Индекс 1 соответствует NSFW классу
            safe_score = probs[0]  # Индекс 0 соответствует безопасному классу
            
            # Определение результата
            is_erotic = nsfw_score > 0.5  # Порог для определения эротического контента
            
            return {
                'is_erotic': is_erotic,
                'nsfw_score': float(nsfw_score),
                'safe_score': float(safe_score),
                'confidence': float(nsfw_score if is_erotic else safe_score),
                'details': [
                    f"Вероятность NSFW контента: {nsfw_score:.6f}",
                    f"Вероятность безопасного контента: {safe_score:.6f}"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}

    def is_safe(self, image_path):
        """
        Быстрая проверка безопасности изображения
        
        Args:
            image_path: путь к изображению
            
        Returns:
            tuple: (is_safe, confidence, details)
        """
        result = self.analyze_image(image_path)
        return not result['is_erotic'], result['confidence'], result['details'] 