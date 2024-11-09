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

# Инициализация модели
def initialize_model() -> None:
    """
    Initialize the detection model.
    """

    global detection_model

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    if DEVICE == "cuda":
        print("Using GPU for computations")
    else:
        print("Using CPU for computations")

    # Загрузка кастомной модели YOLOv5
    detection_model = torch.hub.load('yolov5', 'custom', path=model_path, force_reload=True, source='local')
    detection_model.eval()  # Переводим модель в режим инференса (предсказания)
    print("YOLOv5 model initialized.")

def process_image(tgt_img_path: str) -> np.ndarray:
    """
    Process an image using the initialized model.

    Args:
        tgt_img_path (str): Path to the image file to process.

    Returns:
        np.ndarray: Detected bounding boxes in the format (x, y, width, height, confidence).
    """

    tgt_img_path = os.path.normpath(tgt_img_path)

    if detection_model is None:
        raise RuntimeError("Model is not initialized. Call initialize_model() first.")
    
    if not os.path.isfile(tgt_img_path):
        raise FileNotFoundError(f"Invalid image path: {tgt_img_path}")

    try:
        # Загрузка изображения
        img = Image.open(tgt_img_path)
        
        # Выполнение предсказания
        results = detection_model(img)
        
        # Доступ к сырым данным предсказания
        predictions = results.xyxy[0]  # Координаты bounding box'ов, уверенность, класс
        
        if predictions is None or len(predictions) == 0:
            print(f"No detections found for the image: {tgt_img_path}")
            return []  # Возвращаем пустой список, если нет предсказаний
        
        # Подготовка результатов в нужный формат
        bbox_xywh_conf = []
        for det in predictions:
            x_min, y_min, x_max, y_max, conf, cls = det.tolist()
            width = x_max - x_min
            height = y_max - y_min
            bbox = {
                "x_min": float(x_min),
                "y_min": float(y_min),
                "width": float(width),
                "height": float(height),
                "confidence": float(conf),
                "class": int(cls)
            }
            bbox_xywh_conf.append(bbox)
    
        # Получаем имя папки из пути к изображению
        image_dir = os.path.dirname(tgt_img_path)
        folder_name = os.path.basename(image_dir)  # Название папки с изображениями

        # Указание пути для сохранения изображения
        output_dir = os.path.join("output", folder_name)  # Папка внутри 'output', имя которой соответствует имени загруженной папки

        # Создаем директорию, если она не существует
        os.makedirs(output_dir, exist_ok=True)

        # Сохранение изображения с bounding box'ами в кастомную папку
        # Метод save с указанием директории
        print(f"Saving image to: {output_dir}")
        results.save(save_dir=output_dir, exist_ok = True)  # Указываем кастомную папку для сохранения

        return bbox_xywh_conf

    except Exception as e:
        print(f"Error processing {tgt_img_path}: {e}")
        return None