import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from huggingface_hub import snapshot_download
import argparse

MODEL_NAME = "Falconsai/nsfw_image_detection"

def show_model_info(force_reload=False):
    # Принудительная загрузка (обновление кеша)
    if force_reload:
        print("📦 Принудительная загрузка модели с Hugging Face...")
        snapshot_download(MODEL_NAME, local_files_only=False, force_download=True)

    print(f"🚀 Загрузка модели: {MODEL_NAME}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"💻 Используемое устройство: {device}")

    try:
        processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
        model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
        model.to(device)
        model.eval()

        print("\n📋 Классы (id2label):")
        for idx, label in model.config.id2label.items():
            print(f"  {idx}: {label}")

        print("\n🧠 Архитектура модели:")
        print(model.__class__.__name__)
        print(f"🔢 Кол-во выходных классов: {model.config.num_labels}")

    except Exception as e:
        print(f"❌ Ошибка при загрузке модели: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Информация о модели Falconsai NSFW")
    parser.add_argument("--reload", action="store_true", help="Принудительно обновить модель с Hugging Face")
    args = parser.parse_args()

    show_model_info(force_reload=args.reload)
