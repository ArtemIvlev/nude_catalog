import torch
import clip
from PIL import Image
import sqlite3
from pathlib import Path
from tqdm import tqdm
from config import *
from train_classifier import LikesPredictor

def predict_likes():
    # Загружаем модель
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LikesPredictor().to(device)
    model.load_state_dict(torch.load('likes_model.pth'))
    model.eval()
    
    # Загружаем CLIP модель
    clip_model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Получаем все необработанные изображения
    cur.execute(f"""
        SELECT id, path 
        FROM {TABLE_NAME} 
        WHERE status = 'raw'
    """)
    images = cur.fetchall()
    
    print(f"Найдено {len(images)} необработанных изображений")
    
    # Обрабатываем каждое изображение
    for id, path in tqdm(images, desc="Обработка изображений"):
        try:
            # Загружаем и обрабатываем изображение
            image = Image.open(path)
            image = preprocess(image).unsqueeze(0).to(device)
            
            # Получаем CLIP эмбеддинги
            with torch.no_grad():
                image_features = clip_model.encode_image(image)
            
            # Получаем предсказание количества лайков
            with torch.no_grad():
                predicted_likes = model(image_features)
            
            # Обновляем статус в базе данных
            # Если предсказанное количество лайков выше порога, помечаем как approved
            predicted_likes = float(predicted_likes.item())
            status = 'approved' if predicted_likes > 10 else 'rejected'  # Порог можно настроить
            
            cur.execute(f"""
                UPDATE {TABLE_NAME} 
                SET status = ?, 
                    predicted_likes = ? 
                WHERE id = ?
            """, (status, predicted_likes, id))
            
        except Exception as e:
            print(f"Ошибка при обработке {path}: {str(e)}")
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    print("Готово!")

if __name__ == "__main__":
    predict_likes() 