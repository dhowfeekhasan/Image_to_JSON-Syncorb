// index.js
import { config } from 'dotenv';
import { ocr } from 'llama-ocr';
import fs from 'fs';
import path from 'path';

// Load environment variables
config();

async function processImage(imagePath, userId, documentType) {
    if (!process.env.TOGETHER_API_KEY) return 'Error: TOGETHER_API_KEY not set in .env file';
    if (!fs.existsSync(imagePath)) return `Error: File not found - ${imagePath}`;

    console.log('Performing OCR on the image...');
    const ocrText = await ocr({ filePath: imagePath, apiKey: process.env.TOGETHER_API_KEY });
    console.log('OCR Extraction Done!');

    const outputFolder = 'output';
    if (!fs.existsSync(outputFolder)) fs.mkdirSync(outputFolder, { recursive: true });

    const txtFilePath = path.join(outputFolder, `${path.basename(imagePath, path.extname(imagePath))}.txt`);
    fs.writeFileSync(txtFilePath, ocrText);
    console.log(`OCR result saved to: ${txtFilePath}`);

    return `OCR completed for ${imagePath}`;
}

// Run from command line if arguments are provided
if (process.argv.length > 2) {
    const imagePath = process.argv[2];
    const userId = process.argv[3] || 'default_user';
    const documentType = process.argv[4] || 'invoice';
    processImage(imagePath, userId, documentType)
        .then(result => console.log(result))
        .catch(error => console.error(error));
}
