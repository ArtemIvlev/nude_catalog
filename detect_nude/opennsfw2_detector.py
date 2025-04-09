import torch
import torchvision
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import opennsfw2

class OpenNSFW2Detector:
    def __init__(self):
        # OpenNSFW2 использует TensorFlow внутри, поэтому нам не нужно явно указывать устройство
        self.model = opennsfw2
        
        # Предобработка изображений
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225])
        ])

    def analyze_image(self, image_path):
        try:
            # Используем встроенную функцию predict_image из opennsfw2
            nsfw_score = opennsfw2.predict_image(image_path)
            safe_score = 1.0 - nsfw_score
            
            # Определение уверенности и деталей
            confidence = max(safe_score, nsfw_score)
            is_erotic = nsfw_score > safe_score
            
            details = []
            if is_erotic:
                if nsfw_score > 0.9:
                    details.append("Высокая вероятность NSFW контента")
                elif nsfw_score > 0.7:
                    details.append("Средняя вероятность NSFW контента")
                else:
                    details.append("Низкая вероятность NSFW контента")
            
            return {
                'is_erotic': is_erotic,
                'nsfw_score': float(nsfw_score),
                'safe_score': float(safe_score),
                'confidence': float(confidence),
                'details': details
            }
            
        except Exception as e:
            return {'error': str(e)} 