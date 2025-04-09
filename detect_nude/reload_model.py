from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch

model_id = "Marqo/nsfw-image-detection-384"
device = "cuda" if torch.cuda.is_available() else "cpu"

# Загрузка процессора и модели
processor = AutoImageProcessor.from_pretrained(model_id)
model = AutoModelForImageClassification.from_pretrained(model_id).to(device)

# Вывод информации
print("✅ Загружена модель:", model_id)
print("📋 Классы:")
print(model.config.id2label)