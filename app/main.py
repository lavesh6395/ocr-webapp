from fastapi import FastAPI

app = FastAPI(
    title="OCR WebApp",
    version="0.1.0",
    description="Notebook-to-PDF AI"
)

@app.get("/")
async def root():
    return {
        "message": "OCR WebApp is running.",
        "version": "0.1.0"
    }
