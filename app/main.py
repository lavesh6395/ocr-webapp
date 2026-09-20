from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="OCR WebApp",
    version="0.1.0",
    description="Notebook-to-PDF AI"
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>OCR WebApp</title>
        </head>
        <body style="font-family:Arial;text-align:center;margin-top:80px;">
            <h1>Notebook-to-PDF AI</h1>
            <p>Version 0.1.0</p>
            <p>Deployment successful.</p>
        </body>
    </html>
    """
