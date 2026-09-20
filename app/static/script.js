// ==========================================
// Notebook-to-PDF AI
// Version: 1.0.0
// Final Production Release
// ==========================================

// ---------- DOM Elements ----------

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const previewContainer = document.getElementById("preview-container");
const previewImage = document.getElementById("preview-image");
const fileName = document.getElementById("file-name");

const extractBtn = document.getElementById("extract-btn");
const extractBtnText = document.getElementById("extract-btn-text");
const processingCard = document.getElementById("processing-card");
const resultContainer = document.getElementById("result-container");
const ocrResult = document.getElementById("ocr-result");
const copyBtn = document.getElementById("copy-btn");
const downloadBtn = document.getElementById("download-btn");
const confidenceBadge = document.getElementById("confidence-badge");

// Processing step indicators
const steps = {
    upload: document.getElementById("step-upload"),
    preprocess: document.getElementById("step-preprocess"),
    ocr: document.getElementById("step-ocr"),
    pdf: document.getElementById("step-pdf"),
};

// ---------- Config ----------

const ALLOWED_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf"
];

const MAX_SIZE = 10 * 1024 * 1024;       // 10 MB
const REQUEST_TIMEOUT_MS = 300000;       // 5 minutes

// ---------- State ----------

let selectedFile = null;
let previewUrl = null;
let dragDepth = 0;

// ---------- Helpers ----------

function setResultText(text) {
    if ("value" in ocrResult) {
        ocrResult.value = text;
    } else {
        ocrResult.textContent = text;
    }
}

function getResultText() {
    return "value" in ocrResult ? ocrResult.value : ocrResult.textContent;
}

function setLoading(isLoading) {
    extractBtn.disabled = isLoading;
    browseBtn.disabled = isLoading;
    dropZone.style.pointerEvents = isLoading ? "none" : "auto";

    if (isLoading) {
        extractBtnText.textContent = "Processing…";
    } else {
        extractBtnText.textContent = "Extract Text";
    }
}

function setStepState(stepEl, state) {
    if (!stepEl) return;
    const indicator = stepEl.querySelector(".step-indicator");
    if (!indicator) return;
    indicator.className = "step-indicator " + state;
}

function resetSteps() {
    Object.values(steps).forEach(step => setStepState(step, "pending"));
}

function animateSteps() {
    resetSteps();
    processingCard.classList.remove("hidden");

    // Simulate step progression for visual feedback
    setStepState(steps.upload, "active");

    setTimeout(() => {
        setStepState(steps.upload, "done");
        setStepState(steps.preprocess, "active");
    }, 600);

    setTimeout(() => {
        setStepState(steps.preprocess, "done");
        setStepState(steps.ocr, "active");
    }, 1500);
}

function completeSteps(hasPdf) {
    setStepState(steps.upload, "done");
    setStepState(steps.preprocess, "done");
    setStepState(steps.ocr, "done");

    if (hasPdf) {
        setStepState(steps.pdf, "done");
    } else {
        setStepState(steps.pdf, "pending");
    }
}

function setConfidenceBadge(confidence) {
    if (!confidenceBadge) return;

    const pct = Math.round(confidence * 100);
    confidenceBadge.textContent = `${pct}% confidence`;

    confidenceBadge.className = "confidence-badge";
    if (pct >= 75) {
        confidenceBadge.classList.add("high");
    } else if (pct >= 45) {
        confidenceBadge.classList.add("medium");
    } else {
        confidenceBadge.classList.add("low");
    }
}

// ---------- File Handling ----------

function setFile(file) {
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
        alert("Please select a PNG, JPG, JPEG, or PDF file.");
        return;
    }

    if (file.size > MAX_SIZE) {
        alert("File is too large (maximum 10 MB).");
        return;
    }

    selectedFile = file;
    showPreview(file);
}

function showPreview(file) {
    if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
    }

    previewUrl = URL.createObjectURL(file);

    fileName.textContent = file.name;

    setResultText("");

    if (file.type === "application/pdf") {
        previewImage.src = "/static/pdf-placeholder.png";
    } else {
        previewImage.src = previewUrl;
    }

    previewContainer.classList.remove("hidden");
    resultContainer.classList.add("hidden");
    processingCard.classList.add("hidden");

    if (downloadBtn) {
        downloadBtn.classList.add("hidden");
    }

    resetSteps();
}

// ---------- File Selection ----------

browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
});

fileInput.addEventListener("click", (e) => {
    e.stopPropagation();
});

dropZone.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", (e) => {
    setFile(e.target.files[0]);
    fileInput.value = "";
});

// ---------- Drag & Drop ----------

["dragover", "drop"].forEach((eventName) => {
    window.addEventListener(eventName, (e) => {
        e.preventDefault();
    });
});

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
            const temp = document.createElement("textarea");
            temp.value = text;
            temp.style.position = "fixed";
            temp.style.opacity = "0";
            document.body.appendChild(temp);
            temp.select();
            document.execCommand("copy");
            document.body.removeChild(temp);
        }

        copyBtn.textContent = "✓ Copied!";
        setTimeout(() => {
            copyBtn.textContent = "📋 Copy Text";
        }, 2000);

    } catch (err) {
        console.error(err);
        alert("Could not copy the text.");
    }
});

// ---------- Upload / OCR ----------

extractBtn.addEventListener("click", uploadImage);

async function uploadImage() {

    if (!selectedFile) {
        alert("Please choose a file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setLoading(true);
    resultContainer.classList.add("hidden");
    animateSteps();

    const controller = new AbortController();
    const timeoutId = setTimeout(
        () => controller.abort(),
        REQUEST_TIMEOUT_MS
    );

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
            throw new Error(`Server returned ${response.status}`);
        }

        if (!response.ok || !data.success) {
            alert(data.message || `Request failed (${response.status})`);
            processingCard.classList.add("hidden");
            return;
        }

        // Display results
        const text = data.ocr?.text ?? "";
        const confidence = data.ocr?.confidence ?? 0;
        const hasPdf = !!data.searchable_pdf;

        setResultText(text);
        setConfidenceBadge(confidence);
        completeSteps(hasPdf);

        resultContainer.classList.remove("hidden");

        // Searchable PDF download
        if (downloadBtn && data.searchable_pdf) {
            downloadBtn.classList.remove("hidden");
            downloadBtn.onclick = () => {
                window.location.href = data.searchable_pdf;
            };
        } else if (downloadBtn) {
            downloadBtn.classList.add("hidden");
        }

    } catch (error) {
        console.error(error);
        processingCard.classList.add("hidden");

        if (error.name === "AbortError") {
            alert("The request timed out. Please try again with a smaller file.");
        } else {
            alert("Upload failed. Please try again.");
        }

    } finally {
        clearTimeout(timeoutId);
        setLoading(false);
    }
}