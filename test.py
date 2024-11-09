import os
import torch
from PIL import Image
import pathlib
import numpy as np

# Путь к вашей обученной модели
model_path = 'yolov5\\models\\best.pt'  # Укажите путь к вашему файлу best.pt

# Устанавливаем путь для Windows
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# Устанавливаем порог уверенности для класса 1
CONFIDENCE_THRESHOLD = 0.76  # Установите нужный порог уверенности


# Инициализация модели
def initialize_model() -> None:
    global detection_model

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using {'GPU' if DEVICE == 'cuda' else 'CPU'} for computations")

    # Загрузка кастомной модели YOLOv5
    detection_model = torch.hub.load('yolov5', 'custom', path=model_path, force_reload=True, source='local')
    detection_model.eval()
    print("YOLOv5 model initialized.")


def process_image(tgt_img_path: str) -> np.ndarray:
    tgt_img_path = os.path.normpath(tgt_img_path)

    if detection_model is None:
        raise RuntimeError("Model is not initialized. Call initialize_model() first.")

    if not os.path.isfile(tgt_img_path):
        raise FileNotFoundError(f"Invalid image path: {tgt_img_path}")

    try:
        img = Image.open(tgt_img_path)
        results = detection_model(img)
        predictions = results.xyxy[0]

        if predictions is None or len(predictions) == 0:
            print(f"No detections found for the image: {tgt_img_path}")
            return []

        bbox_xywh_conf = []
        for det in predictions:
            x_min, y_min, x_max, y_max, conf, cls = det.tolist()
            width = x_max - x_min
            height = y_max - y_min

            # Применяем порог для класса 1: если уверенность ниже порога, меняем класс на 0
            if int(cls) == 1 and conf < CONFIDENCE_THRESHOLD:
                cls = 0  # Изменяем класс на 0

            bbox = {
                "x_min": float(x_min),
                "y_min": float(y_min),
                "width": float(width),
                "height": float(height),
                "confidence": float(conf),
                "class": int(cls)
            }
            bbox_xywh_conf.append(bbox)

        # Обновление результатов в объекте results
        results.xyxy[0] = torch.tensor([
            [x['x_min'], x['y_min'], x['x_min'] + x['width'], x['y_min'] + x['height'], x['confidence'], x['class']]
            for x in bbox_xywh_conf
        ])

        image_dir = os.path.dirname(tgt_img_path)
        folder_name = os.path.basename(image_dir)

        output_dir = os.path.join("output", folder_name)
        os.makedirs(output_dir, exist_ok=True)

        # Сохранение изображения с обновленными подписями классов
        print(f"Saving image to: {output_dir}")
        results.save(save_dir=output_dir, exist_ok=True)

        return bbox_xywh_conf

    except Exception as e:
        print(f"Error processing {tgt_img_path}: {e}")
        return None