import os
import sys
import subprocess
from mongodb_process import store_json_in_mongo, fetch_data_for_user

def transform_json(txt_file_path, user_id, document_type):
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    from JSON_Transformation import extract_invoice_json
    extract_invoice_json(txt_file_path, os.getenv("TOGETHER_API_KEY"), output_folder)

    json_file_path = os.path.join(output_folder, os.path.basename(txt_file_path).replace('.txt', '.json'))
    store_json_in_mongo(json_file_path, user_id, document_type)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "transform_json":
            transform_json(sys.argv[2], sys.argv[3], sys.argv[4])
        elif sys.argv[1] == "fetch":
            user_id = sys.argv[2]
            document_type = sys.argv[3]
            result = fetch_data_for_user(user_id, document_type)
            print(result)
        else:
            print("Invalid command. Use 'transform_json' or 'fetch'.")
    else:
        # Interactive mode
        user_id = input("Enter your user ID: ")
        action = input("Do you want to 'upload' or 'fetch'? ").strip().lower()
        if action == "upload":
            image_path = input("Enter the image file path: ")
            document_type = input("Enter the document type (e.g., invoice, emi, hotel bills): ")
            if not os.path.exists(image_path):
                print(f"Error: File not found - {image_path}")
                return
            result = subprocess.run(["node", "index.js", image_path, user_id, document_type], text=True, capture_output=True)
            print(result.stdout)
        elif action == "fetch":
            document_type = input("Enter document type (or 'all' for all types): ")
            result = fetch_data_for_user(user_id, document_type)
            print(result)
        else:
            print("Invalid option! Choose 'upload' or 'fetch'.")

if __name__ == "__main__":
    main()