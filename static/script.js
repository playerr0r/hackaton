let currentPage = 1;
const photosPerPage = 40;

function getBboxSizeInputs() {
  const minWidth = parseInt(document.getElementById("minWidth").value, 10);
  const minHeight = parseInt(document.getElementById("minHeight").value, 10);
  return { minWidth, minHeight };
}

async function uploadImages(files) {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));

  try {
    const response = await fetch("http://localhost:8000/upload/", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const data = await response.json();
      const filenames = data.filenames;
      filenames.forEach(filename => processImage(filename));
    } else {
      alert("Ошибка при загрузке файлов");
    }
  } catch (error) {
    console.error("Ошибка:", error);
  }
}

async function processImage(filename) {
  try {
    const response = await fetch(`http://localhost:8000/process/${filename}`);
    if (response.ok) {
      const data = await response.json();
      displayImageData(data);
    } else {
      alert("Ошибка при обработке изображения");
    }
  } catch (error) {
    console.error("Ошибка:", error);
  }
}

function displayImageData(data) {
  const { filename, detections } = data;
  const hasAnimal = detections.some(d => d.has_animal);
  const { minWidth, minHeight } = getBboxSizeInputs();

  const img = document.createElement("img");
  img.src = `/output/${filename}`;
  img.alt = filename;
  img.classList.add("thumbnail");
  img.addEventListener("click", () => displayImage(img.src));

  if (!hasAnimal) {
    return;
  }

  const isGoodAnimalWithValidBbox = detections.some(d => 
    d.has_animal && d.class === 1 && 
    d.bbox[2] >= minWidth && d.bbox[3] >= minHeight
  );

  const containerId = isGoodAnimalWithValidBbox ? "goodViewPhotos" : "badViewPhotos";
  const container = document.getElementById(containerId);
  container.appendChild(img);
}

function displayImage(src) {
  const mainDisplay = document.getElementById("mainDisplay");
  mainDisplay.innerHTML = `<img src="${src}" alt="Выбранное изображение">`;
}

document.getElementById("fileInput").addEventListener("change", function() {
  const fileButton = document.getElementById("customFileButton");
  if (this.files.length > 0) {
    fileButton.textContent = "Файлы выбраны";
  } else {
    fileButton.textContent = "Выбрать файлы";
  }
});

document.getElementById("uploadButton").addEventListener("click", () => {
  const files = document.getElementById("fileInput").files;
  if (files.length > 0) {
    uploadImages(Array.from(files));
  }
});

function openTab(tabName) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
      tabContents[i].style.display = "none";
    }
    document.getElementById(tabName).style.display = "block";
}

document.getElementById("downloadButton").addEventListener("click", () => {
  // отправить запрос на скачивание файла output.csv с сервера
  const downloadLink = document.createElement("a");
  downloadLink.href = "http://localhost:8000/download/csv";  // Используем новый эндпоинт для скачивания
  downloadLink.download = "output.csv";  // Имя файла, который будет сохранен
  downloadLink.click();  // Инициируем скачивание
});
