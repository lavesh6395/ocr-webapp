// ==========================================
// Notebook-to-PDF AI
// Version: 0.3.1 (fixed)
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

// ---------- Config ----------

const ALLOWED_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf"
];
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const REQUEST_TIMEOUT_MS = 60000; // 60 seconds

// ---------- State ----------

let selectedFile = null;
let previewUrl = null;
let dragDepth = 0;

// ---------- Helpers ----------

function setResultText(text) {
    // Works whether #ocr-result is a <div>/<pre> or a <textarea>
    if ("value" in ocrResult) {
        ocrResult.value = text;
    } else {
        ocrResult.textContent = text;
    }
}

function getResultText() {
    return "value" in ocrResult ? ocrResult.value : ocrResult.textContent;
}

// ---------- File Handling ----------

function setFile(file) {
    // Picker cancelled: keep the current state untouched
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
        alert("Please select a PNG, JPG, or JPEG image.");
        return;
    }

    if (file.size > MAX_SIZE) {
        alert("Image is too large (max 10 MB).");
        return;
    }

    selectedFile = file;
    showPreview(file);
}

function showPreview(file){

    if(previewUrl) URL.revokeObjectURL(previewUrl);

    previewUrl=URL.createObjectURL(file);

    fileName.textContent=file.name;

    setResultText("");

    if(file.type==="application/pdf"){

        previewImage.src="/static/pdf-placeholder.png";

    }else{

        previewImage.src=previewUrl;
    }

    previewContainer.classList.remove("hidden");

    resultContainer.classList.add("hidden");
}
// ---------- File Selection ----------

// Browse button
browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
});

// Prevent the input's own click from bubbling into the drop zone
// (avoids opening the picker twice if the input lives inside the zone)
fileInput.addEventListener("click", (e) => {
    e.stopPropagation();
});

// Clicking anywhere in the drop zone opens the picker
dropZone.addEventListener("click", () => {
    fileInput.click();
});

// File picker
fileInput.addEventListener("change", (e) => {
    setFile(e.target.files[0]);
    // Reset so selecting the same file again still fires "change"
    fileInput.value = "";
});

// ---------- Drag & Drop ----------

// Stop the browser from opening a file that is dropped outside the zone
["dragover", "drop"].forEach((evt) => {
    window.addEventListener(evt, (e) => e.preventDefault());
});

// Counter approach avoids flicker when dragging over child elements
dropZone.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dragDepth++;
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
});

dropZone.addEventListener("dragleave", () => {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) {
        dropZone.classList.remove("dragover");
    }
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dragDepth = 0;
    dropZone.classList.remove("dragover");

    setFile(e.dataTransfer.files[0]);
});

// ---------- Copy OCR Text ----------

copyBtn.addEventListener("click", async () => {
    const text = getResultText();

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else {
            // Fallback for non-HTTPS contexts
            const temp = document.createElement("textarea");
            temp.value = text;
            temp.style.position = "fixed";
            temp.style.opacity = "0";
            document.body.appendChild(temp);
            temp.select();
            document.execCommand("copy");
            document.body.removeChild(temp);
        }

        copyBtn.textContent = "Copied!";
        setTimeout(() => {
            copyBtn.textContent = "Copy Text";
        }, 1500);
    } catch (err) {
        console.error(err);
        alert("Could not copy the text. Please select and copy it manually.");
    }
});

// ---------- Upload / OCR ----------

extractBtn.addEventListener("click", uploadImage);

async function uploadImage() {
    if (!selectedFile) {
        alert("Please choose an image.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    extractBtn.textContent = "Extracting...";
    extractBtn.disabled = true;
    browseBtn.disabled = true;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch("/ocr/image", {
            method: "POST",
            body: formData,
            signal: controller.signal
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error(`Server error (${response.status})`);
        }

        if (!response.ok || !data.success) {
            alert(data.message || `Request failed (${response.status})`);
            return;
        }

        setResultText(data.ocr?.text ?? "");
        resultContainer.classList.remove("hidden");

    } catch (error) {
        console.error(error);

        if (error.name === "AbortError") {
            alert("The request timed out. Please try again.");
        } else {
            alert("Upload failed. Please try again.");
        }

    } finally {
        clearTimeout(timeoutId);
        extractBtn.textContent = "Extract Text";
        extractBtn.disabled = false;
        browseBtn.disabled = false;
    }
}
