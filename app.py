import os
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import subprocess
from pathlib import Path

# Load environment variables
load_dotenv()

app = FastAPI()

# Serve static files (index.html)
app.mount("/static", StaticFiles(directory="public"), name="static")

# Ensure uploads folder exists
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

    # Perform OCR
    try:
        print("Performing OCR on the image...")
        ocr_text = await ocr(filePath=str(image_path), apiKey=os.getenv("TOGETHER_API_KEY"))
        print("OCR Extraction Done!")
    except Exception as e:
        image_path.unlink()  # Clean up
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

    # Save OCR text
    txt_file_path = OUTPUT_DIR / f"{image_path.stem}.txt"
    with txt_file_path.open("w", encoding="utf-8") as f:
        f.write(ocr_text)
    print(f"OCR result saved to: {txt_file_path}")

    # Call JSON transformation
    try:
        print("Calling JSON Transformation script...")
        json_output = subprocess.check_output(
            ["python", "main.py", "transform_json", str(txt_file_path), userId, documentType],
            text=True,
            stderr=subprocess.STDOUT
        )
        print(json_output)
    except subprocess.CalledProcessError as e:
        image_path.unlink()  # Clean up
        raise HTTPException(status_code=500, detail=f"JSON transformation failed: {e.output}")
    finally:
        image_path.unlink()  # Clean up uploaded file

    return {"message": "Upload successful", "output": json_output}

@app.get("/fetch")
async def fetch_data(userId: str, documentType: str):
    try:
        fetch_output = subprocess.check_output(
            ["python", "main.py", "fetch", userId, documentType],
            text=True,
            stderr=subprocess.STDOUT
        )
        return {"message": "Fetch successful", "data": fetch_output}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e.output}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Confirm this line
