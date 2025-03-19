import { config } from 'dotenv';
import { ocr } from 'llama-ocr';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import express from 'express';
import multer from 'multer';
import dotenv from 'dotenv';
dotenv.config();

// Load environment variables
config();

const app = express();
const upload = multer({ dest: 'uploads/' }); // Temporary storage for uploaded files

// Serve static files (e.g., index.html)
app.use(express.static('public'));

// Process image function
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

    try {
        const jsonOutput = execSync(`python main.py transform_json "${txtFilePath}" "${userId}" "${documentType}"`, { encoding: 'utf-8' });
        return jsonOutput;
    } catch (error) {
        return `Error executing JSON transformation: ${error.message}`;
    }
}

// API Endpoints
app.post('/upload', upload.single('image'), async (req, res) => {
    const { userId, documentType } = req.body;
    const imagePath = req.file.path;

    const result = await processImage(imagePath, userId, documentType);
    fs.unlinkSync(imagePath); // Clean up uploaded file
    res.send(result);
});

app.get('/fetch', (req, res) => {
    const { userId, documentType } = req.query;
    try {
        const fetchOutput = execSync(`python main.py fetch "${userId}" "${documentType}"`, { encoding: 'utf-8' });
        res.send(fetchOutput);
    } catch (error) {
        res.send(`Error fetching data: ${error.message}`);
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
