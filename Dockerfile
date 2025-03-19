FROM python:3.11

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl gnupg
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g npm

WORKDIR /app
COPY . .
RUN apt-get install -y tesseract-ocr libtesseract-dev
RUN pip install -r requirements.txt
RUN npm install --verbose  # Add --verbose for detailed logging
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
