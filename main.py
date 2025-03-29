# main.py (Updated)
import os
import sys
import subprocess
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import json
from pymongo import MongoClient
from datetime import datetime, timezone  # Import timezone for UTC fix

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

# MongoDB connection setup
def get_mongo_client():
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise HTTPException(status_code=500, detail="MONGODB_URI not set in .env file")
    return MongoClient(mongo_uri)

@app.get("/")
async def root():
    return {"message": "Welcome to the Document Processor API"}

@app.post("/upload")
async def upload_image(
    userId: str = Form(...),
    documentType: str = Form(...),
    image: UploadFile = Form(...)
):
    # Validate environment variables
    if not os.getenv("TOGETHER_API_KEY"):
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not set in .env file")

    # Save uploaded image
    image_path = UPLOAD_DIR / image.filename
    with image_path.open("wb") as buffer:
        buffer.write(await image.read())

    txt_file = OUTPUT_DIR / f"{image.filename.split('.')[0]}.txt"
    json_file = OUTPUT_DIR / f"{image.filename.split('.')[0]}.json"

    try:
        # Step 1: Perform OCR using Node.js script
        print("Performing OCR via Node.js script...")
        ocr_result = subprocess.check_output(
            ["node", "index.js", str(image_path), userId, documentType],
            text=True,
            stderr=subprocess.STDOUT
        )
        print("OCR completed!")

        # Step 2: Transform OCR result to JSON
        if not txt_file.exists():
            raise HTTPException(status_code=500, detail="OCR text file not generated")
        
        json_transform_command = [
            "python", "json_transformation.py", 
            str(txt_file), str(OUTPUT_DIR)
        ]
        json_result = subprocess.check_output(
            json_transform_command,
            text=True,
            stderr=subprocess.STDOUT
        )
        print("JSON transformation completed!")

        # Step 3: Store in MongoDB
        if not json_file.exists():
            raise HTTPException(status_code=500, detail="JSON file not generated")

        with json_file.open("r") as f:
            json_data = json.load(f)

        client = get_mongo_client()
        db = client['customer_data']
        collection = db[f"user_{userId}"]

        # Use timezone-aware UTC datetime (fix deprecation warning)
        json_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        json_data['document_type'] = documentType

        # Insert into MongoDB
        result = collection.insert_one(json_data)
        
        # Add the inserted _id to json_data and convert to string
        json_data['_id'] = str(result.inserted_id)

        print(f"Data stored in MongoDB for user_{userId}")

        return {
            "message": "Upload and processing successful",
            "json_data": json_data
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e.output}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Clean up files
        if image_path.exists():
            image_path.unlink()
        if txt_file.exists():
            txt_file.unlink()
        if json_file.exists():
            json_file.unlink()

@app.get("/fetch")
async def fetch_data(userId: str, documentType: str):
    try:
        client = get_mongo_client()
        db = client['customer_data']
        collection = db[f"user_{userId}"]

        query = {} if documentType.lower() == 'all' else {'document_type': documentType}
        data = list(collection.find(query))
        
        if not data:
            return {
                "message": f"No data found for User {userId} and Document Type '{documentType}'",
                "data": []
            }
        
        # Convert MongoDB ObjectId to string
        for item in data:
            item['_id'] = str(item['_id'])
        
        return {
            "message": "Fetch successful",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

# Command-line fetch function
def fetch_data_cmd(user_id: str, document_type: str):
    try:
        client = get_mongo_client()
        db = client['customer_data']
        collection = db[f"user_{user_id}"]

        query = {} if document_type.lower() == 'all' else {'document_type': document_type}
        data = list(collection.find(query))
        
        if not data:
            return f"No data found for User {user_id} and Document Type '{document_type}'"
        
        # Convert to JSON string
        for item in data:
            item['_id'] = str(item['_id'])
        return json.dumps(data, indent=4, default=str)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        if len(sys.argv) != 4:
            print("Usage: python main.py fetch <userId> <documentType>")
            sys.exit(1)
        user_id = sys.argv[2]
        document_type = sys.argv[3]
        result = fetch_data_cmd(user_id, document_type)
        print(result)
    else:
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
