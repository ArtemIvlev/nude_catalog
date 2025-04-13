from ultralytics import YOLO
import cv2

class FaceDetector:
    def __init__(self, model_path="yolov8n-face.pt"):
        self.model = YOLO(model_path)

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

        results = self.model.predict(image, verbose=False)[0]
        height, width = image.shape[:2]

        face_locations = []
        face_angles = []
        face_landmarks = []

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2 - x1, y2 - y1
            face_locations.append((x1, y1, w, h))
            face_angles.append(0.0)
            face_landmarks.append([])

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
                'confidence': 1.0,
                'relative_size': {
                    'width': w / width,
                    'height': h / height
                }
            }
            result['faces'].append(face_info)

        return result
