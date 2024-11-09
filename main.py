from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from typing import List
from test import initialize_model, process_image  # Ваши функции для инициализации модели и обработки изображений
import csv
from fastapi.responses import FileResponse
from PIL import Image

app = FastAPI()

# Разрешаем CORS для взаимодействия фронтенда и бэкенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите домены для production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация модели (можно вызвать один раз при запуске приложения)
initialize_model()

# Папки для хранения загруженных и обработанных изображений
UPLOAD_FOLDER = "uploaded_images"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Роут для статических файлов фронтенда
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_images", StaticFiles(directory=UPLOAD_FOLDER), name="uploaded_images")
app.mount("/output", StaticFiles(directory=OUTPUT_FOLDER), name="output")

# Главная страница - возвращаем HTML файл
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "rb") as f:
        return f.read()

# Эндпоинт для загрузки изображений
@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    filenames = []

    # Очистка папкок загруженных и обработанных изображений
    shutil.rmtree(UPLOAD_FOLDER)
    shutil.rmtree(OUTPUT_FOLDER)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Удаление csv файла
    if os.path.exists("output.csv"):
        os.remove("output.csv")

    for file in files:
        file_location = os.path.join(UPLOAD_FOLDER, file.filename)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filenames.append(file.filename)
    return {"filenames": filenames}

# Эндпоинт для обработки изображения
@app.get("/process/{filename:path}")
async def process_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"message": "File not found"})
    
    # Обработка изображения
    detections = process_image(file_path)

    print(detections)
    
    # Если результат None, возвращаем ошибку
    if detections is None:
        return {
            "has_animal": False,
            "bbox": [],
            "class": "not_animal"
        }
    
    # Форматируем detections
    formatted_detections = [
        {
            "has_animal": True,
            "bbox": [detection["x_min"], detection["y_min"], detection["width"], detection["height"]],
            "class": detection["class"]
        }
        for detection in detections
    ]

    print(formatted_detections)

    add_to_csv(filename, formatted_detections)
    
    # Возвращаем результат
    return {"filename": filename, "detections": formatted_detections}

def add_to_csv(filename, detections):
    csv_file = "output.csv"

    # Проверяем, существует ли CSV файл, если нет, создаем его с заголовками
    file_exists = os.path.exists(csv_file)

    # Получаем реальные размеры изображения
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with Image.open(image_path) as img:
            img_width, img_height = img.size  # Получаем размеры изображения
    except Exception as e:
        print(f"Ошибка при открытии изображения {filename}: {e}")
        return  # Если не удается открыть изображение, выходим из функции

    # Открываем файл для записи
    with open(csv_file, mode='a', newline='') as csvfile:
        fieldnames = ['Name', 'BBox', 'Class']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Если файл новый, добавляем заголовки
        if not file_exists:
            writer.writeheader()

        # Обрабатываем все детекции и добавляем их в CSV
        for detection in detections:
            x_min, y_min, width, height = detection["bbox"]

            # Нормализуем координаты
            xc = (x_min + width / 2) / img_width
            yc = (y_min + height / 2) / img_height
            w = width / img_width
            h = height / img_height

            # Записываем строку в CSV
            writer.writerow({
                'Name': filename,
                'BBox': f'{xc:.6f},{yc:.6f},{w:.6f},{h:.6f}',  # Формат xcycwh
                'Class': 1 if detection["class"] else 0  # Преобразуем True/False в 1/0
            })


@app.get("/download/csv")
async def download_csv():
    # Проверяем, существует ли файл
    csv_file = "output.csv"
    if os.path.exists(csv_file):
        # Отправляем файл с заголовком для скачивания
        return FileResponse(csv_file, media_type='text/csv', headers={"Content-Disposition": "attachment; filename=output.csv"})
    else:
        return JSONResponse(status_code=404, content={"message": "File not found"})