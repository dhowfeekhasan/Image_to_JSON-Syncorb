import os
import sys
import json
from together import Together

def clean_json_output(raw_output: str) -> str:
    """Remove unwanted symbols and delimiters from the API response."""
    cleaned = raw_output.strip()  # Remove leading/trailing whitespace and newlines
    # Remove common delimiters
    delimiters = ["```json", "```", "```javascript"]
    for delimiter in delimiters:
        cleaned = cleaned.replace(delimiter, "")
    return cleaned.strip()

def extract_invoice_json(file_path: str, api_key: str, output_folder: str):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    client = Together(api_key=api_key)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            invoice_text = file.read()
    except FileNotFoundError:
        print("Error: File not found.")
        return
    except Exception as e:
        print(f"Error reading the file: {e}")
        return

    messages = [
        {"role": "system", "content": "You are an AI that extracts structured JSON from invoices."},
        {"role": "user", "content": f"Extract structured JSON from this invoice text. Return only valid JSON without any additional text or delimiters:\n{invoice_text}"}
    ]

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>", "<|eom_id|>"],
        stream=False
    )

    raw_output = response.choices[0].message.content
    # Removed Raw API output print statement

    if not raw_output.strip():
        print("\nError: No content received from the API.")
        return

    # Clean the output and log it
    cleaned_output = clean_json_output(raw_output)
    print(f"{cleaned_output}")

    output_filepath = os.path.join(output_folder, os.path.basename(file_path).replace('.txt', '.json'))
    try:
        json_data = json.loads(cleaned_output)
        with open(output_filepath, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, indent=4)
        print(f"\nJSON output saved to {output_filepath}")
    except json.JSONDecodeError as e:
        print(f"\nError: Invalid JSON received - {e}")
        print(f"{cleaned_output}")
        return

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python JSON_Transformation.py <path_to_txt_file> <output_folder_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    output_folder = sys.argv[2]
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("Error: TOGETHER_API_KEY not set in environment variables.")
        sys.exit(1)
    extract_invoice_json(file_path, api_key, output_folder)