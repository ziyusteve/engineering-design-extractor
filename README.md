# Engineering Design Criteria Extractor

A tool to extract engineering design criteria from PDF drawings using Google Cloud Document AI.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Google Cloud Document AI Key
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable Document AI API
- Create a service account with Document AI permissions
- Download the JSON key as `document-ai-key.json` and place it in the project root
- Set up your `.env` file:
  ```
  GOOGLE_APPLICATION_CREDENTIALS=document-ai-key.json
  GOOGLE_CLOUD_PROJECT=your-project-id
  DOCUMENT_AI_PROCESSOR_ID=your-processor-id
  ```

### 3. Run the Web App
```bash
python -m src.webapp.run
```
Visit http://localhost:5000 to upload PDFs and view results.

### 4. Command Line Usage
```bash
python -m src.cli --input data/input/your_document.pdf --output data/output/
```

For more details, see the code or ask for help. 