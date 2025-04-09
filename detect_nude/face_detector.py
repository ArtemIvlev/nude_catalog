import mediapipe as mp
import cv2
import numpy as np

class FaceDetector:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0 для ближних лиц, 1 для дальних
            min_detection_confidence=0.5
        )
        
    def detect_faces(self, image):
        """
        Детектирует лица на изображении
        
        Args:
            image: Путь к изображению (str) или numpy array с изображением в формате BGR
            
        Returns:
            dict: Словарь с информацией о найденных лицах
        """
        # Если передан путь к файлу, загружаем изображение
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                return {
                    'face_count': 0,
                    'face_locations': [],
                    'face_angles': [],
                    'face_landmarks': []
                }
        
        # Конвертация в RGB для MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Детекция лиц
        results = self.face_detection.process(image_rgb)
        
        faces = []
        face_locations = []
        face_angles = []
        face_landmarks = []
        
        if results.detections:
            height, width = image.shape[:2]
            
            for detection in results.detections:
                # Получение координат лица
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * width)
                y = int(bbox.ymin * height)
                w = int(bbox.width * width)
                h = int(bbox.height * height)
                
                # Проверка валидности лица
                if self.is_valid_face(x, y, w, h, width, height):
                    face_locations.append((x, y, w, h))
                    face_angles.append(0.0)  # Пока не реализовано определение угла
                    face_landmarks.append([])  # Пока не реализовано определение ключевых точек
                    
        return {
            'face_count': len(face_locations),
            'face_locations': face_locations,
            'face_angles': face_angles,
            'face_landmarks': face_landmarks
        }
        
    def is_valid_face(self, x, y, w, h, img_width, img_height):
        """
        Проверяет, является ли обнаруженная область действительно лицом
        
        Args:
            x, y: координаты верхнего левого угла
            w, h: ширина и высота области
            img_width, img_height: размеры изображения
            
        Returns:
            bool: True если область похожа на лицо, False иначе
        """
        # Проверка минимального размера (0.5% от размера изображения)
        min_size = min(img_width, img_height) * 0.005
        if w < min_size or h < min_size:
            return False
            
        # Проверка максимального размера (30% от размера изображения)
        max_size = min(img_width, img_height) * 0.3
        if w > max_size or h > max_size:
            return False
            
        # Проверка соотношения сторон (должно быть близко к 1:1)
        aspect_ratio = w / h
        if aspect_ratio < 0.7 or aspect_ratio > 1.3:
            return False
            
        # Проверка расположения (не должно быть слишком близко к краям)
        margin = min(img_width, img_height) * 0.1
        if x < margin or y < margin or x + w > img_width - margin or y + h > img_height - margin:
            return False
            
        return True
    
    def analyze_faces(self, image):
        """
        Анализирует лица на изображении и возвращает подробную информацию
        
        Args:
            image: numpy array с изображением в формате BGR
            
        Returns:
            dict: словарь с информацией о найденных лицах
        """
        faces = self.detect_faces(image)
        height, width = image.shape[:2]
        
        result = {
            'total_faces': len(faces['face_locations']),
            'faces': []
        }
        
        for i, (x, y, w, h) in enumerate(faces['face_locations']):
            face_info = {
                'id': i + 1,
                'position': {'x': x, 'y': y},
                'size': {'width': w, 'height': h},
                'confidence': 1.0,  # Confidence is not provided in the new detect_faces method
                'relative_size': {
                    'width': w / width,
                    'height': h / height
                }
            }
            result['faces'].append(face_info)
        
        return result 