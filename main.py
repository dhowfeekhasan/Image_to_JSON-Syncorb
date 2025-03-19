import os
import sys
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import subprocess
from pathlib import Path
from mongodb_process import fetch_data_for_user

# Load environment variables
load_dotenv()

app = FastAPI()

# Serve static files (index.html)
app.mount("/static", StaticFiles(directory="public"), name="static")

# Ensure uploads and output folders exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to the Document Processor API"}

@app.post("/upload")
async def upload_image(
    userId: str = Form(...),
    documentType: str = Form(...),
    image: UploadFile = Form(...)
):
    if not os.getenv("TOGETHER_API_KEY"):
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not set in .env file")

    # Save uploaded image
    image_path = UPLOAD_DIR / image.filename
    with image_path.open("wb") as buffer:
        buffer.write(await image.read())
        print(f"Image saved to: {image_path}")

    # Perform OCR via Node.js script
    try:
        print("Performing OCR via Node.js script...")
        result = subprocess.check_output(
            ["node", "index.js", str(image_path), userId, documentType],
            text=True,
            stderr=subprocess.STDOUT,
            env=os.environ.copy()
        )
        print("OCR raw result:", result)
        print("OCR and JSON transformation done!")
        return {"message": "Upload successful", "output": result}
    except subprocess.CalledProcessError as e:
        error_detail = f"OCR or transformation failed: {e.output}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        error_detail = f"Unexpected error: {str(e)}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    finally:
        # Only delete if the file exists
        if image_path.exists():
            image_path.unlink()
            print(f"Image deleted: {image_path}")

@app.get("/fetch")
async def fetch_data(userId: str, documentType: str):
    try:
        fetch_output = fetch_data_for_user(userId, documentType)
        if fetch_output is None:
            return {"message": "Fetch successful", "data": "No data found"}
        return {"message": "Fetch successful", "data": fetch_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
