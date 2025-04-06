import os
import onnxruntime as ort
import numpy as np
import cv2

class NudeClassifier:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), "classifier_model.onnx")
        self.session = ort.InferenceSession(model_path, providers=[ "CUDAExecutionProvider", "CPUExecutionProvider"]
)

    def preprocess(self, image_path):
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if img is None or img.shape[0] == 0 or img.shape[1] == 0:
            raise ValueError(f"Невозможно загрузить изображение или оно пустое: {image_path}")

        # Grayscale → RGB
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            raise ValueError(f"Неподдерживаемый формат изображения: {image_path}")

        # Resize to 256x256 (новая модель требует именно это)
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)  # NHWC → (1, 256, 256, 3)

        if img.shape != (1, 256, 256, 3):
            raise ValueError(f"Неверная форма входа: {img.shape} для файла {image_path}")

        return img

    def classify(self, image_path):
        input_tensor = self.preprocess(image_path)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: input_tensor})

        try:
            result = float(outputs[0][0][1])
            is_nude = 1 if result >= 0.85 else 0
            return {image_path: {"unsafe": result, "safe": 1.0 - result, "is_nude": is_nude}}
        except Exception as e:
            raise ValueError(f"Ошибка при разборе вывода модели для {image_path}: {e}")

