import os
import sys
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import subprocess
from pathlib import Path
from mongodb_process import fetch_data_for_user  # Import the function directly

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

    # Perform OCR via Node.js script
    try:
        print("Performing OCR via Node.js script...")
        result = subprocess.check_output(
            ["node", "index.js", str(image_path), userId, documentType],
            text=True,
            stderr=subprocess.STDOUT,
            env=os.environ.copy()  # Pass environment variables
        )
        print("OCR and JSON transformation done!")
    except subprocess.CalledProcessError as e:
        image_path.unlink()  # Clean up
        raise HTTPException(status_code=500, detail=f"OCR or transformation failed: {e.output}")
    except Exception as e:
        image_path.unlink()  # Clean up
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        image_path.unlink()  # Clean up uploaded file

    return {"message": "Upload successful", "output": result}

@app.get("/fetch")
async def fetch_data(userId: str, documentType: str):
    try:
        # Directly call the fetch function instead of using subprocess
        fetch_output = fetch_data_for_user(userId, documentType)
        return {"message": "Fetch successful", "data": fetch_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
