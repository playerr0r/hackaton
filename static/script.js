// Получение минимальных значений ширины и высоты bbox от пользователя
function getBboxSizeInputs() {
  const minWidth = parseInt(document.getElementById("minWidth").value, 10);
  const minHeight = parseInt(document.getElementById("minHeight").value, 10);
  return { minWidth, minHeight };
}

// Загрузка изображений на сервер
async function uploadImages(files) {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file)); // Используем "files" в соответствии с API

  try {
    const response = await fetch("http://localhost:8000/upload/", { // Проверьте, что URL и метод правильные
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const data = await response.json();
      const filenames = data.filenames;
      filenames.forEach(filename => processImage(filename)); // Обрабатываем каждое загруженное изображение
    } else {
      alert("Ошибка при загрузке файлов");
    }
  } catch (error) {
    console.error("Ошибка:", error);
  }
}

// Обработка изображения на сервере для детекции животных
async function processImage(filename) {
  try {
    const response = await fetch(`http://localhost:8000/process/${filename}`);
    if (response.ok) {
      const data = await response.json();
      displayImageData(data); // Отображаем данные о детекции на фронтенде
    } else {
      alert("Ошибка при обработке изображения");
    }
  } catch (error) {
    console.error("Ошибка:", error);
  }
}

// Отображение данных об изображении
function displayImageData(data) {
  const { filename, detections } = data;
  const hasAnimal = detections.some(d => d.has_animal);
  const { minWidth, minHeight } = getBboxSizeInputs();

  // Создаем элемент для миниатюры
  const img = document.createElement("img");
  img.src = `/output/${filename}`;
  img.alt = filename;
  img.classList.add("thumbnail");
  img.addEventListener("click", () => displayImage(img.src));

  // Добавляем в соответствующую вкладку в зависимости от наличия животного
  if (!hasAnimal) {
    return;
  }

  const isGoodAnimalWithValidBbox = detections.some(d => 
    d.has_animal && d.class === 1 && 
    d.bbox[2] >= minWidth && d.bbox[3] >= minHeight
  );

  if (isGoodAnimalWithValidBbox) {
    document.getElementById("goodViewPhotos").appendChild(img);
  } else {
    document.getElementById("badViewPhotos").appendChild(img);
  }
}

// Функция для отображения изображения в главном окне
function displayImage(src) {
  const mainDisplay = document.getElementById("mainDisplay");
  mainDisplay.innerHTML = `<img src="${src}" alt="Выбранное изображение">`;
}

// Запрос на загрузку файлов при нажатии кнопки
document.getElementById("uploadButton").addEventListener("click", () => {
  document.getElementById("goodViewPhotos").innerHTML = "";
  document.getElementById("badViewPhotos").innerHTML = "";

  const files = document.getElementById("fileInput").files;
  if (files.length > 0) {
    uploadImages(Array.from(files));
  }
});

// Функция переключения вкладок
function openTab(tabName) {
  const tabContents = document.getElementsByClassName("tab-content");
  for (let i = 0; i < tabContents.length; i++) {
    tabContents[i].style.display = "none";
  }
  document.getElementById(tabName).style.display = "block";
}
