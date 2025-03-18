import json
from pymongo import MongoClient
from datetime import datetime
import os

def store_json_in_mongo(file_path, user_id, document_type):
    client = os.getenv("MONGODB_URI")
    db = client['customer_data']
    collection_name = f"user_{user_id}"
    collection = db[collection_name]

    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        return

    json_data['timestamp'] = datetime.utcnow()
    json_data['document_type'] = document_type

    collection.insert_one(json_data)
    print(f"Data stored in MongoDB (Collection: '{collection_name}').")

def fetch_data_for_user(user_id, document_type):
    client = os.getenv("MONGODB_URI")
    db = client['customer_data']
    
    collection_name = f"user_{user_id}"
    collection = db[collection_name]

    query = {} if document_type.lower() == 'all' else {'document_type': document_type}
    data = collection.find(query)
    
    data_list = list(data)
    if data_list:
        return json.dumps(data_list, indent=4, default=str)
    else:
        return f"No data found for User {user_id} and Document Type '{document_type}'"