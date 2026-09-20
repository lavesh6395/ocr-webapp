// ==========================================
// Notebook-to-PDF AI
// Version: 0.3
// ==========================================

// ---------- DOM Elements ----------

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const previewContainer = document.getElementById("preview-container");
const previewImage = document.getElementById("preview-image");
const fileName = document.getElementById("file-name");
const extractBtn = document.getElementById("extract-btn");
const resultContainer = document.getElementById("result-container");
const ocrResult = document.getElementById("ocr-result");
const copyBtn = document.getElementById("copy-btn");

// Currently selected file
let selectedFile = null;

// ---------- File Selection ----------

// Browse button
browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
});

// Clicking anywhere in the drop zone opens the picker
dropZone.addEventListener("click", () => {
    fileInput.click();
});

// File picker
fileInput.addEventListener("change", (e) => {
    selectedFile = e.target.files[0];
    showPreview(selectedFile);
});

// ---------- Drag & Drop ----------

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#2563eb";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "#94a3b8";
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#94a3b8";

    selectedFile = e.dataTransfer.files[0];
    showPreview(selectedFile);
});

// ---------- Preview ----------

function showPreview(file) {
    if (!file) return;

    fileName.textContent = file.name;
    previewImage.src = URL.createObjectURL(file);

    previewContainer.classList.remove("hidden");
    resultContainer.classList.add("hidden");
}

// ---------- Copy OCR Text ----------

copyBtn.addEventListener("click", async () => {
    try {
        await navigator.clipboard.writeText(ocrResult.textContent);
        copyBtn.textContent = "Copied!";
        setTimeout(() => {
            copyBtn.textContent = "Copy Text";
        }, 1500);
    } catch (err) {
        console.error(err);
    }
});

// ---------- Upload ----------

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
    browseBtn.disabled = true;

    try {

        const response = await fetch("/ocr/image", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.success) {

            ocrResult.textContent = data.ocr.text;
            resultContainer.classList.remove("hidden");

        } else {

            alert(data.message);

        }

    } catch (error) {

        console.error(error);
        alert("Upload failed. Please try again.");

    } finally {

        extractBtn.textContent = "Extract Text";
        extractBtn.disabled = false;
        browseBtn.disabled = false;

    }
}
