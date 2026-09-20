const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const previewContainer = document.getElementById("preview-container");
const previewImage = document.getElementById("preview-image");
const fileName = document.getElementById("file-name");
const extractBtn = document.getElementById("extract-btn");

// Stores whichever file the user selected
let selectedFile = null;

// Browse button
browseBtn.addEventListener("click", () => fileInput.click());

// Clicking the drop zone also opens the file picker
dropZone.addEventListener("click", () => fileInput.click());

// File picker
fileInput.addEventListener("change", (e) => {
    selectedFile = e.target.files[0];
    showPreview(selectedFile);
});

// Drag events
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#2563eb";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "#94a3b8";
});

// Drop
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#94a3b8";

    selectedFile = e.dataTransfer.files[0];
    showPreview(selectedFile);
});

// Preview
function showPreview(file) {
    if (!file) return;

    fileName.textContent = file.name;
    previewImage.src = URL.createObjectURL(file);
    previewContainer.classList.remove("hidden");
}

// Upload
extractBtn.addEventListener("click", uploadImage);

async function uploadImage() {

    if (!selectedFile) {
        alert("Please choose an image.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    extractBtn.textContent = "Uploading...";
    extractBtn.disabled = true;

    try {
        const response = await fetch("/ocr/image", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        alert(data.message);

    } catch (error) {
        alert("Upload failed. Please try again.");
        console.error(error);

    } finally {
        extractBtn.textContent = "Extract Text";
        extractBtn.disabled = false;
    }
}
