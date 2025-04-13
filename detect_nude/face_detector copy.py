import insightface
from insightface.app import FaceAnalysis
import cv2
import numpy as np

class FaceDetector:
    def __init__(self):
        self.app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect_faces(self, image):
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                return {
                    'face_count': 0,
                    'face_locations': [],
                    'face_angles': [],
                    'face_landmarks': []
                }

        faces = self.app.get(image)
        height, width = image.shape[:2]
        
        face_locations = []
        face_angles = []
        face_landmarks = []

        for face in faces:
            box = face.bbox.astype(int)  # [x1, y1, x2, y2]
            x, y, x2, y2 = box
            w, h = x2 - x, y2 - y
            face_locations.append((x, y, w, h))
            face_angles.append(face.pose[0])  # yaw
            face_landmarks.append(face.kps.tolist())  # 5 keypoints

        return {
            'face_count': len(face_locations),
            'face_locations': face_locations,
            'face_angles': face_angles,
            'face_landmarks': face_landmarks
        }

    def analyze_faces(self, image):
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
                'confidence': 1.0,  # Можно вытаскивать из face.score, если нужно
                'relative_size': {
                    'width': w / width,
                    'height': h / height
                }
            }
            result['faces'].append(face_info)
        
        return result
