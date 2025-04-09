import torch
import torchvision.transforms as T
from PIL import Image
from transformers import AutoFeatureExtractor, AutoModelForImageClassification
import numpy as np
from transformers import CLIPModel, CLIPProcessor

class CLIPNudeChecker:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        model_name = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(model_name).to(device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        
    def classify(self, image_path):
        """Базовая классификация safe/nsfw"""
        return self.classify_with_prompts(image_path, ["safe photo", "nsfw content"])
        
    def classify_with_prompt(self, image_path, prompt):
        """Классификация с одним промптом"""
        return self.classify_with_prompts(image_path, [prompt, "unrelated content"])["nsfw"]
        
    def classify_with_prompts(self, image_path, prompts):
        """Классификация с произвольными промптами"""
        try:
            # Загружаем и обрабатываем изображение
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(
                text=prompts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Переносим на нужное устройство
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Получаем эмбеддинги
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits_per_image[0]
                probs = torch.nn.functional.softmax(logits, dim=-1)
                scores = probs.cpu().numpy()
            
            # Возвращаем словарь с вероятностями
            return {
                "safe": float(scores[0]),
                "nsfw": float(scores[1])
            }
            
        except Exception as e:
            return {'error': str(e)}