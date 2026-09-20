const dropZone=document.getElementById("drop-zone");

const fileInput=document.getElementById("file-input");

const browseBtn=document.getElementById("browse-btn");

const previewContainer=document.getElementById("preview-container");

const previewImage=document.getElementById("preview-image");

const fileName=document.getElementById("file-name");

browseBtn.addEventListener("click",()=>{

    fileInput.click();

});

dropZone.addEventListener("click",()=>{

    fileInput.click();

});

fileInput.addEventListener("change",handleFile);

dropZone.addEventListener("dragover",(e)=>{

    e.preventDefault();

    dropZone.style.borderColor="#2563eb";

});

dropZone.addEventListener("dragleave",()=>{

    dropZone.style.borderColor="#94a3b8";

});

dropZone.addEventListener("drop",(e)=>{

    e.preventDefault();

    dropZone.style.borderColor="#94a3b8";

    const file=e.dataTransfer.files[0];

    showPreview(file);

});

function handleFile(e){

    const file=e.target.files[0];

    showPreview(file);

}

function showPreview(file){

    if(!file)return;

    fileName.textContent=file.name;

    previewImage.src=URL.createObjectURL(file);

    previewContainer.classList.remove("hidden");

}
